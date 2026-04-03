import pytest
from playwright.sync_api import Page
from pathlib import Path

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1280, "height": 720}}

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        page = item.funcargs.get("page")
        if page:
            screenshot_dir = Path("reports/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            path = screenshot_dir / f"{item.name}.png"
            page.screenshot(path=str(path))
            print(f"\nScreenshot saved: {path}")