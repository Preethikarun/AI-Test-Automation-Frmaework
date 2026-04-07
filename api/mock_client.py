"""
api/mock_client.py

Mock APIClient — returns responses from _mock.json or _mock.xml files.
Activated when MOCK_MODE=true in .env.

Mock files live alongside their definition files:
  testCases/api/rest/property_search.json       ← definition
  testCases/api/rest/property_search_mock.json  ← mock response

No network call is made. Response time is read from the mock file
so timing assertions still work against realistic values.

Usage (handled automatically by Runner — do not call directly):
    client = MockClient(definition_path="testCases/api/rest/property_search.json")
    response = client.execute()
    assert response.status == 200
    assert response.mocked is True
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from context.test_context import APIResponse


class MockClient:
    """
    Reads the _mock.json or _mock.xml file matching a definition
    and returns a pre-built APIResponse.
    """

    def __init__(self, definition_path: str):
        self.definition_path = Path(definition_path)
        self.mock_path       = self._find_mock_file()

    def execute(self) -> APIResponse:
        """
        Load and return the mock response.
        Raises FileNotFoundError if no mock file exists alongside
        the definition — this is intentional to force mock creation.
        """
        if not self.mock_path.exists():
            raise FileNotFoundError(
                f"Mock file not found: {self.mock_path}\n"
                f"Create it alongside: {self.definition_path}\n"
                f"See CLAUDE.md API definition pattern for format."
            )

        suffix = self.mock_path.suffix.lower()
        if suffix == ".json":
            return self._load_json_mock()
        elif suffix == ".xml":
            return self._load_xml_mock()
        else:
            raise ValueError(f"Unsupported mock format: {suffix}")

    # ── loaders ───────────────────────────────────────────────────

    def _load_json_mock(self) -> APIResponse:
        data = json.loads(self.mock_path.read_text(encoding="utf-8"))
        return APIResponse(
            status        = data.get("status", 200),
            body          = data.get("body", {}),
            response_time = float(data.get("response_time_ms", 50)),
            text          = json.dumps(data.get("body", {})),
            headers       = data.get("headers", {}),
            mocked        = True,
        )

    def _load_xml_mock(self) -> APIResponse:
        text = self.mock_path.read_text(encoding="utf-8")
        try:
            root = ET.fromstring(text)
            body = self._xml_to_dict(root)
        except ET.ParseError:
            body = text

        # SOAP mock files optionally include a status element
        status = 200
        if isinstance(body, dict):
            status = int(body.pop("__status__", 200))
            resp_time = float(body.pop("__response_time_ms__", 50))
        else:
            resp_time = 50.0

        return APIResponse(
            status        = status,
            body          = body,
            response_time = resp_time,
            text          = text,
            mocked        = True,
        )

    # ── helpers ───────────────────────────────────────────────────

    def _find_mock_file(self) -> Path:
        """
        Build mock file path by inserting _mock before the extension.
        property_search.json → property_search_mock.json
        """
        stem   = self.definition_path.stem
        suffix = self.definition_path.suffix
        return self.definition_path.parent / f"{stem}_mock{suffix}"

    @staticmethod
    def _xml_to_dict(element: ET.Element) -> dict:
        """Recursively convert XML element tree to a plain dict."""
        result = {}
        for child in element:
            tag   = child.tag.split("}")[-1]   # strip namespace
            value = MockClient._xml_to_dict(child) if len(child) else child.text
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(value)
            else:
                result[tag] = value
        return result or (element.text or "")
