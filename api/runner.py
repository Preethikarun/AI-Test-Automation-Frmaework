"""
api/runner.py

Central API test runner.
Reads a definition file (JSON or XML), routes to live or mock client,
executes the request, validates the response, and returns a result.

One line in a Spec test:
    result = Runner.run("testCases/api/rest/property_search.json")
    assert result.passed, str(result)

MOCK_MODE=true  → reads _mock.json / _mock.xml (no network)
MOCK_MODE=false → hits live API with auth from .env

Spec test pattern:
    @allure.suite("API Tests")
    class TestPropertyAPI:

        @pytest.mark.api
        @pytest.mark.smoke
        @allure.title("Property search returns Wellington results")
        def test_property_search(self):
            result = Runner.run("testCases/api/rest/property_search.json")
            assert result.passed, str(result)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Union

import allure

from api.auth_handler import AuthHandler
from api.mock_client import MockClient
from api.rest_client import RestClient
from api.validator import ValidationResult, Validator
from context.test_context import APIResponse


class RunResult:
    """
    Combines APIResponse and ValidationResult into one return value.
    Spec tests assert on RunResult.passed directly.
    """

    def __init__(self, response: APIResponse, validation: ValidationResult):
        self.response   = response
        self.validation = validation
        self.passed     = validation.passed

    def __bool__(self) -> bool:
        return self.passed

    def __str__(self) -> str:
        lines = [str(self.validation)]
        if not self.passed:
            lines.append(
                f"Response: status={self.response.status} "
                f"time={self.response.response_time:.0f}ms "
                f"mocked={self.response.mocked}"
            )
        return "\n".join(lines)


class Runner:
    """
    Executes a single API test definition.
    Auto-detects REST (JSON) vs SOAP (XML) from file extension.
    Routes to mock or live based on MOCK_MODE env var.
    """

    MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

    @staticmethod
    def run(definition_path: str) -> RunResult:
        """
        Execute one API test definition and return RunResult.

        Args:
            definition_path: relative path to the definition file,
                             e.g. "testCases/api/rest/property_search.json"

        Returns:
            RunResult with .passed, .response, .validation
        """
        path = Path(definition_path)
        if not path.exists():
            raise FileNotFoundError(f"Definition not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".json":
            return Runner._run_rest(path)
        elif suffix == ".xml":
            return Runner._run_soap(path)
        else:
            raise ValueError(
                f"Unknown definition format: {suffix}. "
                f"Expected .json (REST) or .xml (SOAP)."
            )

    # ── REST ──────────────────────────────────────────────────────

    @staticmethod
    def _run_rest(path: Path) -> RunResult:
        definition = json.loads(path.read_text(encoding="utf-8"))

        with allure.step(f"API: {definition.get('name', path.stem)}"):

            if Runner.MOCK_MODE:
                response = MockClient(str(path)).execute()
                allure.attach(
                    f"MOCK MODE — reading {path.stem}_mock.json",
                    name="Mock mode active",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                auth   = AuthHandler.from_definition(
                    definition.get("auth", {})
                )
                client = RestClient(
                    base_url = definition["base_url"],
                    auth     = auth,
                    headers  = definition.get("headers", {}),
                )
                method   = definition.get("method", "GET").upper()
                endpoint = definition.get("endpoint", "/")
                params   = definition.get("params")
                body     = definition.get("body")

                response = getattr(client, method.lower())(
                    endpoint = endpoint,
                    params   = params,
                    body     = body,
                ) if method not in ("GET", "DELETE") else getattr(
                    client, method.lower()
                )(endpoint=endpoint, params=params)

            # attach response to Allure report
            allure.attach(
                json.dumps(
                    response.body if isinstance(response.body, dict)
                    else {"text": response.text},
                    indent=2,
                    default=str,
                ),
                name="Response body",
                attachment_type=allure.attachment_type.JSON,
            )

            validation = Validator.validate(
                response, definition.get("expected", {})
            )

            if not validation.passed:
                allure.attach(
                    str(validation),
                    name="Validation failures",
                    attachment_type=allure.attachment_type.TEXT,
                )

        return RunResult(response, validation)

    # ── SOAP ──────────────────────────────────────────────────────

    @staticmethod
    def _run_soap(path: Path) -> RunResult:
        """
        SOAP support via zeep.
        pip install zeep must be in requirements.txt.
        """
        if Runner.MOCK_MODE:
            response = MockClient(str(path)).execute()
            validation = Validator.validate(response, {})
            return RunResult(response, validation)

        try:
            from api.soap_client import SoapClient
        except ImportError:
            raise ImportError(
                "pip install zeep to run SOAP tests. "
                "Add zeep to requirements.txt."
            )

        import xml.etree.ElementTree as ET
        tree       = ET.parse(path)
        root       = tree.getroot()
        wsdl_url   = root.findtext("wsdl_url") or ""
        operation  = root.findtext("operation") or ""
        auth_el    = root.find("auth")
        auth_cfg   = {}
        if auth_el is not None:
            auth_cfg = {child.tag: child.text for child in auth_el}

        auth   = AuthHandler.from_definition(auth_cfg)
        client = SoapClient(wsdl_url=wsdl_url, auth=auth)
        params = {
            child.tag: child.text
            for child in (root.find("params") or [])
        }

        with allure.step(f"SOAP: {operation}"):
            response   = client.call(operation, **params)
            expected   = {}
            exp_el     = root.find("expected")
            if exp_el is not None:
                expected = {child.tag: child.text for child in exp_el}

            validation = Validator.validate(response, expected)

        return RunResult(response, validation)
