"""
api/validator.py

Validates an APIResponse against the "expected" block
in a test definition JSON/XML file.

Validation types (Option D — all four):
status         — HTTP status code matches exactly
response_time  — response time under threshold (ms)
fields_exist   — listed keys present in response body
field_values   — specific key-value pairs match
contains_text  — substring present in response text

Returns a ValidationResult with passed=True/False and
a list of failure messages for Allure and failures.json.

Usage (called by Runner — not directly from tests):
    result = Validator.validate(response, expected_block)
    assert result.passed, str(result)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

from context.test_context import APIResponse


@dataclass
class ValidationResult:
    passed:   bool        = True
    failures: List[str]   = field(default_factory=list)
    warnings: List[str]   = field(default_factory=list)

    def fail(self, message: str) -> None:
        self.passed = False
        self.failures.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def __str__(self) -> str:
        if self.passed:
            return "PASSED"
        return "FAILED:\n" + "\n".join(f"  - {f}" for f in self.failures)

    def __bool__(self) -> bool:
        return self.passed


class Validator:
    """
    Validates an APIResponse against an expected block dict.

    Expected block format (from definition JSON):
    {
      "status":           200,
      "response_time_ms": 3000,
      "fields_exist":     ["List", "TotalCount"],
      "field_values":     {"TotalCount": 5},
      "contains_text":    "Wellington"
    }
    """

    @staticmethod
    def validate(
        response: APIResponse,
        expected: dict,
    ) -> ValidationResult:
        result = ValidationResult()

        if not expected:
            return result

        Validator._check_status(response, expected, result)
        Validator._check_response_time(response, expected, result)
        Validator._check_fields_exist(response, expected, result)
        Validator._check_field_values(response, expected, result)
        Validator._check_contains_text(response, expected, result)

        return result

    # ── individual checks ─────────────────────────────────────────

    @staticmethod
    def _check_status(
        response: APIResponse,
        expected: dict,
        result:   ValidationResult,
    ) -> None:
        exp = expected.get("status")
        if exp is None:
            return
        if response.status != int(exp):
            result.fail(
                f"Status: expected {exp}, got {response.status}"
            )

    @staticmethod
    def _check_response_time(
        response: APIResponse,
        expected: dict,
        result:   ValidationResult,
    ) -> None:
        threshold = expected.get("response_time_ms")
        if threshold is None:
            return
        if response.response_time > float(threshold):
            result.fail(
                f"Response time: {response.response_time:.0f}ms "
                f"exceeded threshold {threshold}ms"
            )

    @staticmethod
    def _check_fields_exist(
        response: APIResponse,
        expected: dict,
        result:   ValidationResult,
    ) -> None:
        fields = expected.get("fields_exist", [])
        if not fields or not isinstance(response.body, dict):
            return
        for field_name in fields:
            if field_name not in response.body:
                result.fail(
                    f"Missing field: '{field_name}' not in response body"
                )

    @staticmethod
    def _check_field_values(
        response: APIResponse,
        expected: dict,
        result:   ValidationResult,
    ) -> None:
        field_values = expected.get("field_values", {})
        if not field_values or not isinstance(response.body, dict):
            return
        for key, expected_val in field_values.items():
            actual = response.body.get(key)
            if actual != expected_val:
                result.fail(
                    f"Field value mismatch: '{key}' "
                    f"expected {expected_val!r}, got {actual!r}"
                )

    @staticmethod
    def _check_contains_text(
        response: APIResponse,
        expected: dict,
        result:   ValidationResult,
    ) -> None:
        text = expected.get("contains_text", "")
        if not text:
            return
        if text not in response.text:
            result.fail(
                f"Text not found: '{text}' not in response body"
            )
