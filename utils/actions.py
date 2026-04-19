"""
utils/actions.py

Actions — low-level Playwright wrapper for all PageObject interactions.

Rules:
- Every PageObject method calls Actions instead of page.locator() directly
- All waits are handled here — never hard sleep() in tests
- Every method accepts a selector string (the value from the locator dict)
- Timeout defaults match Playwright defaults but can be overridden per call

Usage in PageObjects:
    from utils.actions import Actions
    self.actions = Actions(page)
    self.actions.click(self.loc["search"]["button"])
    self.actions.fill(self.loc["search"]["input"], "Wellington")
"""

from __future__ import annotations

from typing import Optional

from playwright.sync_api import Page, Locator


class Actions:
    """
    Wraps Playwright page interactions.
    Every public method accepts a CSS/XPath selector string.
    """

    DEFAULT_TIMEOUT = 10_000   # ms — 10 seconds

    def __init__(self, page: Page, timeout: int = DEFAULT_TIMEOUT):
        self.page    = page
        self.timeout = timeout

    # ── navigation ────────────────────────────────────────────────

    def navigate(self, url: str) -> None:
        """Navigate to a URL and wait for the page to settle."""
        self.page.goto(url)
        self.wait_for_page_load()

    def wait_for_page_load(self) -> None:
        """
        Wait for the DOM to be ready.

        Uses 'domcontentloaded' (not 'networkidle') because sites with
        continuous analytics/ad traffic (e.g. Trade Me) never reach networkidle
        and would always time out.  A short extra pause absorbs JS hydration.
        """
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)
        except Exception:
            pass
        # absorb JS framework hydration without blocking on network
        self.page.wait_for_timeout(500)

    # ── visibility + waiting ──────────────────────────────────────

    def wait_for_visible(self, selector: str, timeout: int = None) -> Locator:
        """Wait until the element matching selector is visible. Returns Locator."""
        loc = self.page.locator(selector)
        loc.wait_for(state="visible", timeout=timeout or self.timeout)
        return loc

    def wait_for_hidden(self, selector: str, timeout: int = None) -> None:
        """Wait until the element matching selector is hidden or detached."""
        self.page.locator(selector).wait_for(
            state="hidden", timeout=timeout or self.timeout
        )

    def is_visible(self, selector: str) -> bool:
        """Return True if the element is visible on the page right now."""
        return self.page.locator(selector).is_visible()

    def is_enabled(self, selector: str) -> bool:
        """Return True if the element is not disabled."""
        return self.page.locator(selector).is_enabled()

    # ── clicks ────────────────────────────────────────────────────

    def click(self, selector: str, timeout: int = None) -> None:
        """Wait for element to be visible then click it."""
        self.page.locator(selector).click(timeout=timeout or self.timeout)

    def double_click(self, selector: str) -> None:
        """Double-click an element."""
        self.page.locator(selector).dblclick()

    def click_if_visible(self, selector: str) -> bool:
        """Click element only if it is currently visible. Returns True if clicked."""
        if self.is_visible(selector):
            self.click(selector)
            return True
        return False

    # ── inputs ────────────────────────────────────────────────────

    def fill(self, selector: str, value: str) -> None:
        """Clear then type value into an input field."""
        loc = self.page.locator(selector)
        loc.clear()
        loc.fill(value)

    def type_slowly(self, selector: str, value: str, delay: int = 50) -> None:
        """Type value character-by-character (for fields that react to key events)."""
        self.page.locator(selector).type(value, delay=delay)

    def clear(self, selector: str) -> None:
        """Clear an input field."""
        self.page.locator(selector).clear()

    def press_key(self, key: str) -> None:
        """Press a keyboard key (e.g. 'Enter', 'Tab', 'Escape')."""
        self.page.keyboard.press(key)

    # ── selects / dropdowns ───────────────────────────────────────

    def select(self, selector: str, value: str) -> None:
        """
        Select an option in a <select> element.
        Value can be the option text, value attribute, or index.
        """
        self.page.locator(selector).select_option(label=value)

    def select_by_value(self, selector: str, value: str) -> None:
        """Select a <select> option by its value attribute."""
        self.page.locator(selector).select_option(value=value)

    # ── text extraction ───────────────────────────────────────────

    def get_text(self, selector: str) -> str:
        """Return the trimmed text content of the first matching element."""
        return (self.page.locator(selector).text_content() or "").strip()

    def get_all_texts(self, selector: str) -> list[str]:
        """Return a list of text content from all matching elements."""
        return [
            (t or "").strip()
            for t in self.page.locator(selector).all_text_contents()
        ]

    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Return the value of an HTML attribute on the first matching element."""
        return self.page.locator(selector).get_attribute(attribute)

    def get_value(self, selector: str) -> str:
        """Return the current value of an input field."""
        return self.page.locator(selector).input_value()

    # ── counting ──────────────────────────────────────────────────

    def count(self, selector: str) -> int:
        """Return the number of elements matching the selector."""
        return self.page.locator(selector).count()

    # ── hover + scroll ────────────────────────────────────────────

    def hover(self, selector: str) -> None:
        """Hover over an element (triggers CSS :hover state)."""
        self.page.locator(selector).hover()

    def scroll_into_view(self, selector: str) -> None:
        """Scroll the element into the viewport."""
        self.page.locator(selector).scroll_into_view_if_needed()

    # ── screenshots ───────────────────────────────────────────────

    def screenshot(self, path: str) -> None:
        """Capture a full-page screenshot and save to path."""
        self.page.screenshot(path=path, full_page=True)

    def screenshot_element(self, selector: str, path: str) -> None:
        """Capture a screenshot of a specific element."""
        self.page.locator(selector).screenshot(path=path)

    # ── iframe support ────────────────────────────────────────────

    def frame_locator(self, frame_selector: str):
        """Return a FrameLocator for interacting with elements inside an iframe."""
        return self.page.frame_locator(frame_selector)
