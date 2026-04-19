"""
capture/ci_failure_capture.py

CI Failure Capture — wired into conftest.py pytest hooks.

On every test failure:
  1. Saves Playwright trace to reports/traces/{test_name}.zip
  2. Takes screenshot to reports/screenshots/{test_name}.png
  3. Appends structured record to reports/failures.json
  4. Flags trace for MCP analysis (flaky / locator failures)

CI workflow:
  - GitHub Actions uploads traces + failures.json as artifacts
  - Agent 4 (failure_analysis_agent) reads failures.json
  - Agent 4 routes: locator → Agent 3 self-heal
                    logic   → fix plan
                    flaky   → MCPAnalyser batch analysis

Usage in conftest.py:
    from capture.ci_failure_capture import CIFailureCapture
    capture = CIFailureCapture()

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(item, call):
        outcome = yield
        report  = outcome.get_result()
        if report.when == "call" and report.failed:
            capture.on_failure(item, call, report)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from context.logger import Logger

if TYPE_CHECKING:
    import pytest


class CIFailureCapture:
    """
    Captures full failure context on every test failure.
    Writes to reports/failures.json for Agent 4 to read.
    """

    SCREENSHOTS_DIR = Path("reports/screenshots")
    TRACES_DIR      = Path("reports/traces")

    def __init__(self):
        self.log = Logger()
        self.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        self.TRACES_DIR.mkdir(parents=True, exist_ok=True)

    def on_failure(
        self,
        item:   "pytest.Item",
        call:   "pytest.CallInfo",
        report: "pytest.TestReport",
    ) -> None:
        """
        Called by conftest.py pytest_runtest_makereport hook
        when a test fails.

        Captures screenshot, reads trace path from TestContext,
        classifies the error, and writes to failures.json.
        """
        test_id   = item.nodeid
        error_msg = self._extract_error(call)
        category  = self._classify(call)
        browser   = self._extract_browser(item)

        # ── screenshot ────────────────────────────────────────────
        screenshot_path = self._take_screenshot(item)

        # ── trace path (set by TraceRecorder in conftest fixture) ─
        trace_path = self._extract_trace_path(item)

        # ── broken locator (from TimeoutError message) ────────────
        locator_key, broken_selector = self._extract_locator(call)

        # ── retry count ───────────────────────────────────────────
        retry_count = self._extract_retry_count(item)

        # ── write to failures.json ────────────────────────────────
        self.log.failure(
            test_id         = test_id,
            error           = error_msg,
            category        = category,
            trace_path      = trace_path,
            screenshot_path = screenshot_path,
            locator_key     = locator_key,
            broken_selector = broken_selector,
            browser         = browser,
            retry_count     = retry_count,
        )

    # ── classification ────────────────────────────────────────────

    def _classify(self, call: "pytest.CallInfo") -> str:
        """
        Classify failure category from exception type and message.

        Categories (matches ApprovalGateway decision matrix):
          locator     — Playwright TimeoutError waiting for a UI element
          api_timeout — HTTP/API timeout (httpx, requests, urllib)
          logic       — AssertionError — test expectation was wrong
          environment — Network, connection refused, Docker/AKS issues
          flaky       — Explicitly marked or detected intermittent failure
          unknown     — Everything else
        """
        if not call.excinfo:
            return "unknown"

        exc_type = type(call.excinfo.value).__name__.lower()
        exc_msg  = str(call.excinfo.value).lower()

        # ── API timeout — httpx / requests / urllib ───────────────────────
        _api_timeout_signals = (
            "readtimeout", "connecttimeout", "httptimeout",
            "requests.exceptions.timeout", "httpx",
            "connectiontimeout", "sockettimeout",
        )
        if "timeout" in exc_type and any(s in exc_msg for s in _api_timeout_signals):
            return "api_timeout"
        # also catch when the exception class name itself comes from httpx/requests
        if any(s in exc_type for s in ("readtimeout", "connecttimeout", "httptimeout")):
            return "api_timeout"

        # ── Playwright UI locator timeout ─────────────────────────────────
        # Playwright TimeoutErrors mention "locator" or "waiting for" in the message
        if "timeout" in exc_type:
            if any(kw in exc_msg for kw in ("locator", "waiting for", "selector", "element")):
                return "locator"
            # generic playwright timeout with no locator hint → still locator category
            if "playwright" in exc_msg or "page.goto" in exc_msg:
                return "locator"
            return "locator"   # safest default for any remaining TimeoutError

        # ── assertion error — test logic is wrong ─────────────────────────
        if "assertion" in exc_type:
            return "logic"

        # ── environment — network / infra ─────────────────────────────────
        if any(kw in exc_msg for kw in (
            "connection", "network", "refused", "unreachable",
            "econnrefused", "no route", "name resolution"
        )):
            return "environment"

        # ── explicitly flaky ──────────────────────────────────────────────
        if any(kw in exc_msg for kw in ("flaky", "intermittent")):
            return "flaky"

        return "unknown"

    # ── helpers ───────────────────────────────────────────────────

    def _take_screenshot(self, item: "pytest.Item") -> Optional[str]:
        """Take a screenshot if a page fixture is available."""
        try:
            page = item.funcargs.get("page")
            if page:
                safe_name = re.sub(r"[^\w\-]", "_", item.name)
                path = self.SCREENSHOTS_DIR / f"{safe_name}.png"
                page.screenshot(path=str(path), full_page=True)
                return str(path)
        except Exception:
            pass
        return None

    def _extract_trace_path(self, item: "pytest.Item") -> Optional[str]:
        """Read trace path stored on TestContext by TraceRecorder."""
        try:
            tc = item.funcargs.get("test_context")
            if tc and tc.trace_path:
                return tc.trace_path
        except Exception:
            pass
        return None

    def _extract_error(self, call: "pytest.CallInfo") -> str:
        """Extract and truncate the error message."""
        if call.excinfo:
            return str(call.excinfo.value)[:500]
        return "unknown error"

    def _extract_browser(self, item: "pytest.Item") -> Optional[str]:
        """Extract browser name from pytest-playwright markers."""
        try:
            return item.config.getoption("--browser", default=None)
        except Exception:
            return None

    def _extract_locator(
        self, call: "pytest.CallInfo"
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Extract broken selector from TimeoutError message.
        Returns (locator_key, selector_string) or (None, None).

        TimeoutError messages typically look like:
          "Timeout 30000ms exceeded waiting for locator('input.search')"
        """
        if not call.excinfo:
            return None, None

        msg = str(call.excinfo.value)
        match = re.search(r"locator\(['\"](.+?)['\"]\)", msg)
        if match:
            selector = match.group(1)
            return None, selector   # locator_key requires locator file lookup

        return None, None

    def _extract_retry_count(self, item: "pytest.Item") -> int:
        """Read retry count from pytest-rerunfailures plugin if active."""
        try:
            return item.execution_count - 1
        except AttributeError:
            return 0
