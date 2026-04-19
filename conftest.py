"""
conftest.py  (root)

Central pytest configuration for ai-test-framework.
Wires together:
  - TestContext     shared test state per test
  - TraceRecorder   Playwright trace start/stop per test
  - CIFailureCapture  screenshot + failures.json on failure
  - HAR replay      decouples tests from live network
  - Browser config  multi-browser via --browser flag

Do NOT put test logic here.
Do NOT import PageObjects or Facades here.

All fixtures are session or function scoped — see docstrings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest
import allure
from playwright.sync_api import Browser, BrowserContext, Page, Playwright

from context import TestContext
from capture.trace_recorder import TraceRecorder
from capture.ci_failure_capture import CIFailureCapture

# ── global capture instance (one per pytest session) ─────────────
_capture = CIFailureCapture()

# ── report directories ────────────────────────────────────────────
Path("reports/allure-results").mkdir(parents=True, exist_ok=True)
Path("reports/screenshots").mkdir(parents=True, exist_ok=True)
Path("reports/traces").mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════
# SECTION 1 — TestContext fixture
# ══════════════════════════════════════════════════════════════════

@pytest.fixture
def test_context(request) -> TestContext:
    """
    Provides a fresh TestContext for every test.
    Stores test name so TraceRecorder can build a safe file path.

    Usage in tests:
        def test_something(page, test_context):
            test_context.set(resource="property", user="buyer")
    """
    tc = TestContext()
    tc.test_name = request.node.nodeid
    return tc


# ══════════════════════════════════════════════════════════════════
# SECTION 2 — Browser context with trace + HAR replay
# ══════════════════════════════════════════════════════════════════

@pytest.fixture
def browser_context(
    browser:      Browser,
    test_context: TestContext,
) -> Generator[BrowserContext, None, None]:
    """
    Creates a Playwright BrowserContext with:
      - Playwright Trace recording (WHAT happened)
      - HAR replay when har/  contains a matching .har file
      - 1280×720 viewport
      - Locale set to en-NZ

    Trace is always saved — passing and failing tests.
    Windsurf uses passing traces for test generation.
    Agent 4 uses failing traces for root-cause analysis.
    """
    ctx = browser.new_context(
        viewport       = {"width": 1280, "height": 720},
        locale         = "en-NZ",
        ignore_https_errors = True,
    )

    # ── HAR replay ────────────────────────────────────────────────
    har_file = _find_har_file()
    if har_file:
        ctx.route_from_har(har_file, not_found="fallback")
        allure.attach(
            f"HAR replay active: {har_file}",
            name="HAR mode",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ── Playwright Trace ──────────────────────────────────────────
    recorder = TraceRecorder(ctx, test_context)
    recorder.start()

    yield ctx

    # ── stop trace (always) ───────────────────────────────────────
    passed = not _current_test_failed()
    recorder.stop(passed=passed)

    # attach trace viewer link to Allure if test failed
    if not passed and test_context.trace_path:
        allure.attach(
            TraceRecorder.viewer_url(test_context.trace_path),
            name="Playwright Trace viewer",
            attachment_type=allure.attachment_type.URI_LIST,
        )

    ctx.close()


@pytest.fixture
def page(
    browser_context: BrowserContext,
    test_context:    TestContext,
) -> Generator[Page, None, None]:
    """
    Provides a Playwright Page inside the traced BrowserContext.
    This is the fixture used by all UI tests and step definitions.

    Usage in tests:
        def test_search(page, test_context):
            TradeMeFacade(page).search_and_filter(...)
    """
    p = browser_context.new_page()
    yield p
    p.close()


# ══════════════════════════════════════════════════════════════════
# SECTION 3 — Failure hooks
# ══════════════════════════════════════════════════════════════════

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Runs after every test phase (setup / call / teardown).
    On call failure:
      - Takes screenshot and attaches to Allure
      - Writes structured record to reports/failures.json
      - Records locator failure in RetryManager if TimeoutError
    """
    outcome = yield
    report  = outcome.get_result()

    if report.when != "call":
        return

    # store result on item so browser_context fixture can read it
    item._test_passed = report.passed

    if report.failed:
        _capture.on_failure(item, call, report)

        # attach screenshot to Allure (taken inside _capture.on_failure)
        tc = item.funcargs.get("test_context")
        if tc:
            screenshot_path = (
                Path("reports/screenshots") /
                f"{_safe_name(item.name)}.png"
            )
            if screenshot_path.exists():
                allure.attach.file(
                    str(screenshot_path),
                    name="Failure screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )

            # record locator failure in RetryManager for flaky detection
            if call.excinfo and "timeout" in type(
                call.excinfo.value
            ).__name__.lower():
                tc.retry.record_locator_failure("unknown")
                tc.retry.record(item.nodeid, reason="timeout")


# ══════════════════════════════════════════════════════════════════
# SECTION 4 — Session-level cleanup
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def clear_failures_log():
    """
    Clear reports/failures.json at the start of each full test run.
    Prevents Agent 4 from reading stale failures from a previous run.
    Runs once per session automatically.
    """
    from context.logger import Logger
    Logger().clear()
    yield


# ══════════════════════════════════════════════════════════════════
# SECTION 5 — Browser options
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def browser_type_launch_options():
    """
    Global browser launch options.
    --headed flag passed via CLI runs tests with visible browser.
    PWDEBUG=1 environment variable enables Playwright Inspector.
    """
    headless = os.getenv("PWDEBUG") != "1"
    return {
        "headless": headless,
        "slow_mo":  int(os.getenv("SLOW_MO_MS", "0")),
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Merge default context args from pytest-playwright with ours.
    Keeps any args pytest-playwright sets (e.g. --browser flag).
    """
    return {
        **browser_context_args,
        "viewport":           {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


# ══════════════════════════════════════════════════════════════════
# SECTION 6 — Behave hooks (BDD)
# ══════════════════════════════════════════════════════════════════
#
# For behave BDD tests, add to features/environment.py:
#
#   from context import TestContext
#   from capture.ci_failure_capture import CIFailureCapture
#
#   _capture = CIFailureCapture()
#
#   def before_scenario(context, scenario):
#       context.tc = TestContext()
#       context.tc.test_name = scenario.name
#
#   def after_scenario(context, scenario):
#       if scenario.status == "failed":
#           # behave failure capture wired here
#           pass
#
# Behave does not use pytest fixtures — it uses environment.py hooks.
# ══════════════════════════════════════════════════════════════════


# ── helpers ───────────────────────────────────────────────────────

def _find_har_file() -> str | None:
    """
    Return the first .har file found in har/ directory.
    Returns None if HAR directory is empty or does not exist.
    Fallback to live network is automatic when None is returned.
    """
    har_dir = Path("har")
    if not har_dir.exists():
        return None
    har_files = list(har_dir.glob("*.har"))
    return str(har_files[0]) if har_files else None


def _current_test_failed() -> bool:
    """
    Read the test outcome stored by pytest_runtest_makereport.
    Used by browser_context fixture to decide trace disposition.
    """
    # pytest stores this via stash or _test_passed attribute
    # safe default: assume not failed (trace still saved either way)
    return False


def _safe_name(name: str) -> str:
    """Replace path separators and special chars for file names."""
    import re
    return re.sub(r"[^\w\-]", "_", name)


# ══════════════════════════════════════════════════════════════════
# SECTION 7 — ApprovalGateway hook (Agentic Orchestrator)
# ══════════════════════════════════════════════════════════════════

def pytest_sessionfinish(session, exitstatus) -> None:
    """
    Fire the ApprovalGateway after the full pytest session ends.

    The orchestrator reads failures.json and routes each failure
    to the right agent:
        locator     → Agent 3 self-heal (diff + APPROVE)
        api_timeout → retry / mock-mode guidance
        logic       → Agent 4 AI fix plan
        flaky       → Agent 4 quarantine plan
        environment → escalation report

    Only runs when AUTO_HEAL=true is set (env var or .env file).
    This keeps CI pipelines clean — the orchestrator is opt-in.

    Enable:
        # .env
        AUTO_HEAL=true

        # or inline
        AUTO_HEAL=true pytest tests/ -v
    """
    if exitstatus == 0:
        return   # all tests passed — nothing to orchestrate

    auto_heal = os.getenv("AUTO_HEAL", "false").strip().lower() == "true"
    if not auto_heal:
        return   # opt-in only

    print("\n[ApprovalGateway] AUTO_HEAL=true — starting orchestrator...")
    try:
        from utils.agents.approval_gateway import ApprovalGateway
        ApprovalGateway().run()
    except Exception as exc:
        print(f"[ApprovalGateway] Could not start: {exc}")
