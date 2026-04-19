"""
api/mock_client.py

Mock APIClient -- returns responses from pre-recorded files.
Activated when MOCK_MODE=true.

Naming convention (consistent across ALL API tests):
    {name}_request.json   <- what you send   (HTTP method, endpoint, headers, body)
    {name}_response.json  <- what comes back  (pre-recorded mock response)

Examples:
    posts_list_request.json   + posts_list_response.json
    cat_image_request.json    + cat_image_response.json
    create_post_request.json  + create_post_response.json

MockClient resolves the response file automatically by replacing
'_request' with '_response' in the definition file stem.

Usage (handled automatically by Runner -- do not call directly):
    client = MockClient(definition_path="testCases/api/rest/posts_list_request.json")
    response = client.execute()
    assert response.mocked is True
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from context.test_context import APIResponse


class MockClient:

    def __init__(self, definition_path: str):
        self.definition_path = Path(definition_path)
        self.mock_path = self._find_mock_file()

    def execute(self) -> APIResponse:
        if not self.mock_path.exists():
            raise FileNotFoundError(
                f"Response file not found: {self.mock_path}\n"
                f"Create it alongside: {self.definition_path}\n"
                f"Convention: {self.definition_path.stem.replace('_request', '_response')}.json"
            )
        suffix = self.mock_path.suffix.lower()
        if suffix == ".json":
            return self._load_json_mock()
        elif suffix == ".xml":
            return self._load_xml_mock()
        else:
            raise ValueError(f"Unsupported mock format: {suffix}")

    # -- loaders -------------------------------------------------------

    def _load_json_mock(self) -> APIResponse:
        data = json.loads(self.mock_path.read_text(encoding="utf-8"))
        return APIResponse(
            status=data.get("status", 200),
            body=data.get("body", {}),
            response_time=float(data.get("response_time_ms", 50)),
            text=json.dumps(data.get("body", {})),
            headers=data.get("headers", {}),
            mocked=True,
        )

    def _load_xml_mock(self) -> APIResponse:
        text = self.mock_path.read_text(encoding="utf-8")
        try:
            root = ET.fromstring(text)
            body = self._xml_to_dict(root)
        except ET.ParseError:
            body = text

        status = 200
        resp_time = 50.0
        if isinstance(body, dict):
            status = int(body.pop("__status__", 200))
            resp_time = float(body.pop("__response_time_ms__", 50))

        return APIResponse(
            status=status,
            body=body,
            response_time=resp_time,
            text=text,
            mocked=True,
        )

    # -- mock file resolution ------------------------------------------

    def _find_mock_file(self) -> Path:
        """
        Resolve the paired response file from the request file name.

        Convention:
            posts_list_request.json -> posts_list_response.json
            cat_image_request.json  -> cat_image_response.json

        For SOAP:
            property_request.xml    -> property_response.xml
        """
        stem = self.definition_path.stem
        suffix = self.definition_path.suffix
        parent = self.definition_path.parent

        # new convention: swap _request -> _response
        if stem.endswith("_request"):
            response_stem = stem[: -len("_request")] + "_response"
            return parent / f"{response_stem}{suffix}"

        # legacy fallback: {stem}_mock.{suffix} (backward compatibility)
        return parent / f"{stem}_mock{suffix}"

    @staticmethod
    def _xml_to_dict(element: ET.Element) -> dict:
        result = {}
        for child in element:
            tag = child.tag.split("}")[-1]
            value = MockClient._xml_to_dict(child) if len(child) else child.text
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(value)
            else:
                result[tag] = value
        return result or (element.text or "")
