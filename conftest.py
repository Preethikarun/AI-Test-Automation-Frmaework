import pytest
from playwright.sync_api import Page
from pathlib import Path

HAR_PATH = "har/todo_app.har"

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args, 
        "viewport": {"width": 1280, "height": 720}
    }

@pytest.fixture
def page(browser):
    """
    Custom page fixture — replays network from HAR file.
    Tests run without any live network dependency.
    """
    context = browser.new_context()

    if Path(HAR_PATH).exists():
        context.route_from_har(
            HAR_PATH,
            not_found="fallback"   # pass through unknown URLs
        )
        print(f"\nHAR replay active: {HAR_PATH}")
    else:
        print("\nNo HAR file found — using live network")

    page = context.new_page()
    yield page

# Screenshot on failure
    context.close()


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
            try:
                page.screenshot(path=str(path))
                print(f"\nScreenshot: {path}")
            except Exception:
                pass