"""
api/rest_client.py

REST APIClient — wraps httpx for all HTTP calls.
All REST requests in the framework go through this.
Never use httpx directly in tests or step definitions.

Returns APIResponse (from context.test_context) on every call.
TestContext.post_back() is called by the ServiceLayer, not here.

Usage:
    client = RestClient(base_url="https://api.trademe.co.nz")
    response = client.get(
        endpoint = "/v1/Search/Property/Residential.json",
        params   = {"search_string": "Wellington"},
        auth     = AuthHandler.from_definition(auth_config),
    )
    assert response.ok
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

import httpx

from api.auth_handler import AuthHandler
from context.test_context import APIResponse


class RestClient:
    """
    HTTP client for REST APIs.
    Handles auth, request construction, timing, and response parsing.
    """

    DEFAULT_TIMEOUT = int(os.getenv("API_TIMEOUT_S", "30"))

    def __init__(
        self,
        base_url: str,
        auth:     Optional[AuthHandler] = None,
        headers:  Optional[dict]        = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth     = auth or AuthHandler()
        self._default_headers = {
            "Content-Type": "application/json",
            "Accept":       "application/json",
            **(headers or {}),
        }

    # ── public methods ────────────────────────────────────────────

    def get(
        self,
        endpoint: str,
        params:   Optional[dict] = None,
        headers:  Optional[dict] = None,
    ) -> APIResponse:
        return self._request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        body:     Optional[Any]  = None,
        params:   Optional[dict] = None,
        headers:  Optional[dict] = None,
    ) -> APIResponse:
        return self._request("POST", endpoint, body=body,
                             params=params, headers=headers)

    def put(
        self,
        endpoint: str,
        body:     Optional[Any]  = None,
        headers:  Optional[dict] = None,
    ) -> APIResponse:
        return self._request("PUT", endpoint, body=body, headers=headers)

    def delete(
        self,
        endpoint: str,
        headers:  Optional[dict] = None,
    ) -> APIResponse:
        return self._request("DELETE", endpoint, headers=headers)

    def patch(
        self,
        endpoint: str,
        body:     Optional[Any]  = None,
        headers:  Optional[dict] = None,
    ) -> APIResponse:
        return self._request("PATCH", endpoint, body=body, headers=headers)

    # ── core request ──────────────────────────────────────────────

    def _request(
        self,
        method:   str,
        endpoint: str,
        body:     Optional[Any]  = None,
        params:   Optional[dict] = None,
        headers:  Optional[dict] = None,
    ) -> APIResponse:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        merged_headers = {
            **self._default_headers,
            **self.auth.get_headers(),
            **(headers or {}),
        }
        merged_params = {
            **(params or {}),
            **self.auth.get_params(),
        }
        cert = self.auth.get_cert()

        start = time.monotonic()
        try:
            with httpx.Client(
                timeout=self.DEFAULT_TIMEOUT,
                cert=cert,
                verify=True,
            ) as client:
                raw = client.request(
                    method  = method,
                    url     = url,
                    headers = merged_headers,
                    params  = merged_params,
                    json    = body if isinstance(body, dict) else None,
                    content = body if isinstance(body, (str, bytes)) else None,
                )
        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"API timeout after {self.DEFAULT_TIMEOUT}s: {url}"
            ) from e
        except httpx.RequestError as e:
            raise ConnectionError(f"API request failed: {url} — {e}") from e

        elapsed_ms = (time.monotonic() - start) * 1000

        # parse body
        try:
            parsed_body = raw.json()
        except Exception:
            parsed_body = raw.text

        return APIResponse(
            status        = raw.status_code,
            body          = parsed_body,
            response_time = round(elapsed_ms, 2),
            text          = raw.text,
            headers       = dict(raw.headers),
            mocked        = False,
        )
