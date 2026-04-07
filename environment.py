"""
features/environment.py

Behave hooks — the behave equivalent of pytest conftest.py.
Wires TestContext, TraceRecorder, and CIFailureCapture
into every BDD scenario.

Behave does NOT use pytest fixtures.
All setup goes here via before_/after_ hooks.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from context import TestContext
from capture.trace_recorder import TraceRecorder
from capture.ci_failure_capture import CIFailureCapture

# ── one capture instance per behave session ───────────────────────
_capture = CIFailureCapture()


# ══════════════════════════════════════════════════════════════════
# SESSION HOOKS
# ══════════════════════════════════════════════════════════════════

def before_all(context):
    """
    Runs once before the entire behave test suite.
    Clears failures.json so Agent 4 reads only this run's data.
    Starts the Playwright instance shared across all scenarios.
    """
    from context.logger import Logger
    Logger().clear()

    # ensure report directories exist
    Path("reports/screenshots").mkdir(parents=True, exist_ok=True)
    Path("reports/traces").mkdir(parents=True, exist_ok=True)

    # start shared Playwright instance
    context._playwright = sync_playwright().start()
    context._browser    = context._playwright.chromium.launch(
        headless=True,
    )


def after_all(context):
    """Runs once after the entire suite. Cleans up Playwright."""
    if hasattr(context, "_browser"):
        context._browser.close()
    if hasattr(context, "_playwright"):
        context._playwright.stop()


# ══════════════════════════════════════════════════════════════════
# SCENARIO HOOKS
# ══════════════════════════════════════════════════════════════════

def before_scenario(context, scenario):
    """
    Runs before each scenario.
    Creates a fresh TestContext and a new browser context with tracing.
    """
    # fresh state — no bleed between scenarios
    context.tc = TestContext()
    context.tc.test_name = scenario.name

    # new browser context per scenario
    context._browser_context = context._browser.new_context(
        viewport            = {"width": 1280, "height": 720},
        locale              = "en-NZ",
        ignore_https_errors = True,
    )

    # HAR replay if available
    har_file = _find_har_file()
    if har_file:
        context._browser_context.route_from_har(
            har_file, not_found="fallback"
        )

    # start Playwright Trace
    context._recorder = TraceRecorder(
        context._browser_context, context.tc
    )
    context._recorder.start()

    # page used by step definitions
    context.page = context._browser_context.new_page()


def after_scenario(context, scenario):
    """
    Runs after each scenario.
    Stops trace, captures screenshot on failure, writes failures.json.
    """
    passed = scenario.status != "failed"

    # stop trace — always saved
    if hasattr(context, "_recorder"):
        context._recorder.stop(passed=passed)

    # on failure — screenshot + failures.json
    if not passed:
        _on_failure(context, scenario)

    # close page and browser context
    if hasattr(context, "page"):
        context.page.close()
    if hasattr(context, "_browser_context"):
        context._browser_context.close()

    # reset TestContext between scenarios
    if hasattr(context, "tc"):
        context.tc.reset()


# ══════════════════════════════════════════════════════════════════
# FAILURE CAPTURE
# ══════════════════════════════════════════════════════════════════

def _on_failure(context, scenario) -> None:
    """
    Screenshot + failures.json entry on scenario failure.
    Called from after_scenario when scenario.status == "failed".
    """
    import re

    safe_name = re.sub(r"[^\w\-]", "_", scenario.name)

    # screenshot
    screenshot_path = None
    if hasattr(context, "page"):
        try:
            path = Path("reports/screenshots") / f"{safe_name}.png"
            context.page.screenshot(path=str(path), full_page=True)
            screenshot_path = str(path)
        except Exception:
            pass

    # classify and write to failures.json
    error_msg = ""
    category  = "unknown"
    if scenario.exception:
        error_msg = str(scenario.exception)[:500]
        exc_type  = type(scenario.exception).__name__.lower()
        if "timeout"   in exc_type: category = "locator"
        elif "assert"  in exc_type: category = "logic"
        elif "connect" in exc_type: category = "environment"

    context.tc.log.failure(
        test_id         = scenario.name,
        error           = error_msg,
        category        = category,
        trace_path      = getattr(context.tc, "trace_path", None),
        screenshot_path = screenshot_path,
    )


# ── helpers ───────────────────────────────────────────────────────

def _find_har_file() -> str | None:
    """Return first .har file in har/ or None."""
    har_dir   = Path("har")
    har_files = list(har_dir.glob("*.har")) if har_dir.exists() else []
    return str(har_files[0]) if har_files else None
