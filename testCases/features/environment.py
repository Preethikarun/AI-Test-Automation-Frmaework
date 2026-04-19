"""
testCases/features/environment.py

Behave lifecycle hooks — Playwright browser + TestContext setup.

Behave calls these functions automatically:
  before_all   → launch the Playwright browser process once
  before_scenario → open a fresh browser page + TestContext per scenario
  after_scenario  → close the page, save trace on failure
  after_all    → shut down the browser process

Environment variables:
  BROWSER   chromium (default) | firefox | webkit
  HEADLESS  true (default) | false
"""

from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from context.test_context import TestContext


# ── configuration helpers ─────────────────────────────────────────────

def _browser_name() -> str:
    return os.getenv("BROWSER", "chromium").lower()

def _headless() -> bool:
    return os.getenv("HEADLESS", "false").lower() != "false"


# ── lifecycle hooks ───────────────────────────────────────────────────

def before_all(context):
    """Start Playwright and launch the browser once for the whole test run."""
    context.playwright = sync_playwright().start()
    engine             = getattr(context.playwright, _browser_name())
    context.browser    = engine.launch(headless=_headless(), slow_mo=50)
    print(f"\nBrowser launched: {_browser_name()}  headless={_headless()}")


def before_scenario(context, scenario):
    """
    Open a fresh browser page and a new TestContext for each scenario.
    Tracing is started here so every scenario gets its own trace file.
    """
    context.tc        = TestContext()
    context.browser_context = context.browser.new_context(
        viewport={"width": 1400, "height": 900},
        record_video_dir="reports/videos/" if not _headless() else None,
    )

    # Start Playwright trace for this scenario
    context.browser_context.tracing.start(
        screenshots=True,
        snapshots=True,
        sources=True,
    )

    context.page = context.browser_context.new_page()


def after_scenario(context, scenario):
    """
    Close the page after each scenario.
    On failure: save the trace so it can be inspected in Playwright Trace Viewer.
    """
    trace_dir = Path("reports/traces")
    trace_dir.mkdir(parents=True, exist_ok=True)

    # Sanitise scenario name for use as filename
    safe_name = scenario.name.replace(" ", "_").replace("/", "-")[:80]

    if scenario.status == "failed":
        trace_path = trace_dir / f"FAILED_{safe_name}.zip"
        try:
            context.browser_context.tracing.stop(path=str(trace_path))
            print(f"\n  Trace saved → {trace_path}")
            print(f"  View with:  playwright show-trace {trace_path}")
        except Exception:
            pass

        # Screenshot on failure
        screenshot_dir = Path("reports/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        try:
            context.page.screenshot(
                path=str(screenshot_dir / f"FAILED_{safe_name}.png"),
                full_page=True,
            )
        except Exception:
            pass
    else:
        try:
            context.browser_context.tracing.stop()
        except Exception:
            pass

    try:
        context.page.close()
        context.browser_context.close()
    except Exception:
        pass


def after_all(context):
    """Shut down the browser and Playwright after the full test run."""
    try:
        context.browser.close()
        context.playwright.stop()
        print("\nBrowser closed.")
    except Exception:
        pass
