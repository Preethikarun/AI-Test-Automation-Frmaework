"""
api/soap_client.py

SOAP client wrapping zeep.
All SOAP calls in the framework go through this.
Never call zeep directly in tests or step definitions.

Install: pip install zeep

Usage (via Runner -- do not call directly in tests):
    client = SoapClient(wsdl_url="https://example.com/service?WSDL")
    response = client.call("OperationName", param1="value1")
    assert response.ok
"""

from __future__ import annotations

import time
from typing import Any

from context.test_context import APIResponse


class SoapClient:
    """
    Thin wrapper around zeep for SOAP/WSDL calls.
    Returns APIResponse so the Validator works identically for REST and SOAP.
    """

    def __init__(self, wsdl_url: str, auth=None):
        self.wsdl_url = wsdl_url
        self.auth = auth

    def call(self, operation: str, **params) -> APIResponse:
        """
        Call a SOAP operation and return a standardised APIResponse.

        Args:
            operation: the WSDL operation name, e.g. "NumberToWords"
            **params:  keyword arguments matching the operation's input fields

        Returns:
            APIResponse with status=200 on success, body as dict or str
        """
        try:
            from zeep import Client
        except ImportError:
            raise ImportError(
                "pip install zeep   -- required for SOAP tests"
            )

        client = Client(wsdl=self.wsdl_url)
        start = time.monotonic()

        try:
            raw_result = getattr(client.service, operation)(**params)
            status = 200
        except Exception as e:
            elapsed_ms = (time.monotonic() - start) * 1000
            return APIResponse(
                status=500,
                body={"error": str(e)},
                response_time=round(elapsed_ms, 2),
                text=str(e),
                mocked=False,
            )

        elapsed_ms = (time.monotonic() - start) * 1000

        # normalise the zeep result into a plain dict or string
        body = self._normalise(raw_result)

        return APIResponse(
            status=status,
            body=body if isinstance(body, dict) else {"result": body},
            response_time=round(elapsed_ms, 2),
            text=str(raw_result),
            mocked=False,
        )

    # -- helpers -------------------------------------------------------

    @staticmethod
    def _normalise(value: Any) -> Any:
        """Convert zeep CompoundValue or primitive to dict/str."""
        if value is None:
            return {}
        # zeep CompoundValue has __dict__ and __values__ attributes
        if hasattr(value, "__dict__"):
            try:
                return dict(value)
            except Exception:
                pass
        return str(value)
