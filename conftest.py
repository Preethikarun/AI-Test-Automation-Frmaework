import pytest
import re as _re
from pathlib import Path
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720}
    }


@pytest.fixture
def page(browser):
    context = browser.new_context()
    har_path = "har/todo_app.har"
    if Path(har_path).exists():
        context.route_from_har(har_path, not_found="fallback")
        print(f"\nHAR replay active: {har_path}")
    else:
        print("\nNo HAR file — using live network")
    page = context.new_page()
    yield page
    context.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.failed and call.excinfo:
        exc = call.excinfo.value
        page = item.funcargs.get("page")

        # screenshot on any failure
        if page:
            screenshot_dir = Path("reports/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            path = screenshot_dir / f"{item.name}.png"
            try:
                page.screenshot(path=str(path))
                print(f"\nScreenshot saved: {path}")
            except Exception:
                pass

        # self-heal on TimeoutError only
        error_msg = str(exc)
        if "TimeoutError" in type(exc).__name__ and page:
            match = _re.search(
                r'locator\(["\'](.+?)["\']\)', error_msg
            )
            broken_locator = match.group(1) if match else "unknown"
            locator_key = _find_locator_key(broken_locator)

            print(f"\nTimeoutError — broken locator: '{broken_locator}'")
            print("Triggering Agent 3 self-heal...")

            try:
                page_html = page.content()
            except Exception:
                page_html = "<html>Could not capture page</html>"

            from agents.self_heal_agent import SelfHealAgent
            agent = SelfHealAgent()
            agent.run(
                broken_locator=broken_locator,
                locator_key=locator_key,
                page_html=page_html,
                locator_file="locators/todo_locators.py"
            )


def _find_locator_key(broken_locator: str) -> str:
    try:
        from locators.todo_locators import TODO_LOCATORS
        for key, value in TODO_LOCATORS.items():
            if value == broken_locator:
                return key
    except ImportError:
        pass
    return "unknown_key"