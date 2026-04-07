"""
context/test_context.py

Shared test state for a single test run.
Replaces the Cucumber 'World' pattern with Python-Pytest idiom.

Usage in pytest (via conftest.py fixture):
    @pytest.fixture
    def test_context():
        return TestContext()

Usage in behave (via environment.py):
    def before_scenario(context, scenario):
        context.tc = TestContext()

Usage in step definitions:
    @given("the user is authenticated as admin")
    def step_auth(context):
        context.tc.set(resource="property", user="admin")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from context.retry_manager import RetryManager
from context.logger import Logger


@dataclass
class APIResponse:
    """
    Standardised response object returned by APIClient.
    Replaces 'RestClient Result' from the Ruby/Cucumber pattern.
    """
    status:        int
    body:          Any            # dict for JSON, str for XML/text
    response_time: float          # milliseconds
    text:          str = ""
    headers:       dict = field(default_factory=dict)
    mocked:        bool = False

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def __str__(self) -> str:
        return (
            f"APIResponse(status={self.status}, "
            f"time={self.response_time:.0f}ms, "
            f"mocked={self.mocked})"
        )


class TestContext:
    """
    Holds all shared state for one test run.

    Flow (mirrors automation-pylib sequence diagram):
      1. Fixture / before_scenario creates TestContext
      2. Step definitions call tc.set(resource, user)
      3. ServiceLayer reads tc.resource and tc.user
      4. APIClient executes the request
      5. ServiceLayer calls tc.post_back(response)
      6. Assertions read tc.api_response and tc.data
    """

    def __init__(self):
        # ── what is being tested ──────────────────────────────────
        self.resource: Optional[str] = None
        self.user:     Optional[str] = None

        # ── API state ─────────────────────────────────────────────
        self.api_response: Optional[APIResponse] = None

        # ── shared data bag (populated by post_back) ──────────────
        self.data: dict = {}

        # ── infrastructure ────────────────────────────────────────
        self.retry = RetryManager()
        self.log   = Logger()

        # ── behaviour capture metadata ────────────────────────────
        self.trace_path:    Optional[str] = None   # set by conftest trace hook
        self.test_name:     Optional[str] = None   # set by conftest

    # ── state setters ─────────────────────────────────────────────

    def set(self, resource: str, user: str) -> None:
        """
        Called by step definitions to configure what is being tested.

        Example:
            context.tc.set(resource="property", user="admin")
        """
        self.resource = resource
        self.user     = user
        self.log.debug(f"TestContext.set: resource={resource} user={user}")

    def post_back(self, response: APIResponse) -> None:
        """
        Called by ServiceLayer after every API call.
        Stores the response and merges body into the shared data bag.

        This closes the loop: API result becomes available to
        subsequent steps and assertions without passing values
        through step arguments.
        """
        self.api_response = response
        self.log.debug(f"TestContext.post_back: {response}")

        if isinstance(response.body, dict):
            self.data.update(response.body)

    # ── convenience accessors ─────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Read a value from the shared data bag."""
        return self.data.get(key, default)

    def store(self, key: str, value: Any) -> None:
        """Write a value into the shared data bag."""
        self.data[key] = value

    @property
    def last_status(self) -> Optional[int]:
        """Shortcut: HTTP status of the last API call."""
        return self.api_response.status if self.api_response else None

    @property
    def last_body(self) -> Any:
        """Shortcut: response body of the last API call."""
        return self.api_response.body if self.api_response else None

    # ── reset ─────────────────────────────────────────────────────

    def reset(self) -> None:
        """
        Called between scenarios in behave to avoid state bleed.
        pytest fixtures are scoped per-function so this is
        typically not needed there.
        """
        self.resource     = None
        self.user         = None
        self.api_response = None
        self.data         = {}
        self.retry.reset()
        self.log.debug("TestContext.reset")

    def __repr__(self) -> str:
        return (
            f"TestContext("
            f"resource={self.resource!r}, "
            f"user={self.user!r}, "
            f"data_keys={list(self.data.keys())})"
        )
