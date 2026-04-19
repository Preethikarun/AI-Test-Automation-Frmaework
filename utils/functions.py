"""
utils/functions.py

Functions — common application-level flows and reusable assertions.

Difference from Actions:
  Actions  → low-level Playwright wrappers  (click, fill, wait)
  Functions → higher-level app interactions (accept cookies, login, assert)

Rules:
- Every PageObject method calls Functions for cross-cutting concerns
- Functions call Actions internally — never page.locator() directly
- Assertions in Functions start with assert_* naming
- No test-specific logic here — only reusable flows

Usage in PageObjects:
    from utils.functions import Functions
    self.functions = Functions(page)
    self.functions.accept_cookies()
    self.functions.assert_page_title_contains("Trade Me")
"""

from __future__ import annotations

from playwright.sync_api import Page

from utils.actions import Actions


class Functions:
    """
    Reusable cross-cutting concerns for all PageObjects.
    Composes with Actions — never calls page.locator() directly.
    """

    # Common cookie banner selectors used across most NZ/AU sites
    COOKIE_ACCEPT_SELECTORS = [
        "button[id*='accept']",
        "button[id*='cookie']",
        "button[aria-label*='Accept']",
        "button[aria-label*='accept']",
        "button:has-text('Accept all')",
        "button:has-text('Accept cookies')",
        "button:has-text('I agree')",
        "[data-testid='cookie-accept']",
        "#onetrust-accept-btn-handler",
    ]

    def __init__(self, page: Page):
        self.page    = page
        self.actions = Actions(page)

    # ── cookie / consent ──────────────────────────────────────────

    def accept_cookies(self) -> bool:
        """
        Try common cookie accept button selectors.
        Returns True if a cookie banner was found and dismissed, else False.
        Silently does nothing if no banner is present.
        """
        for selector in self.COOKIE_ACCEPT_SELECTORS:
            try:
                if self.actions.is_visible(selector):
                    self.actions.click(selector)
                    return True
            except Exception:
                continue
        return False

    def dismiss_modal(self, selector: str) -> bool:
        """
        Dismiss a modal or overlay if it is visible.
        Returns True if dismissed.
        """
        return self.actions.click_if_visible(selector)

    # ── page assertions ───────────────────────────────────────────

    def assert_page_title_contains(self, expected: str) -> None:
        """Assert the browser tab title contains the expected substring."""
        actual = self.page.title()
        assert expected.lower() in actual.lower(), (
            f"Expected page title to contain '{expected}' but got '{actual}'"
        )

    def assert_url_contains(self, fragment: str) -> None:
        """Assert the current URL contains the expected fragment."""
        actual = self.page.url
        assert fragment in actual, (
            f"Expected URL to contain '{fragment}' but got '{actual}'"
        )

    def assert_element_text_contains(self, selector: str, expected: str) -> None:
        """Assert that an element's text contains the expected substring."""
        actual = self.actions.get_text(selector)
        assert expected.lower() in actual.lower(), (
            f"Expected text to contain '{expected}' but got '{actual}'"
        )

    def assert_element_visible(self, selector: str, message: str = "") -> None:
        """Assert an element is visible, with an optional failure message."""
        assert self.actions.is_visible(selector), (
            message or f"Expected element '{selector}' to be visible"
        )

    def assert_element_not_visible(self, selector: str, message: str = "") -> None:
        """Assert an element is NOT visible."""
        assert not self.actions.is_visible(selector), (
            message or f"Expected element '{selector}' to be hidden"
        )

    def assert_count_above(self, selector: str, minimum: int) -> None:
        """Assert the number of matching elements is at or above minimum."""
        actual = self.actions.count(selector)
        assert actual >= minimum, (
            f"Expected at least {minimum} elements matching '{selector}' "
            f"but found {actual}"
        )

    # ── waiting helpers ───────────────────────────────────────────

    def wait_for_url_change(self, original_url: str, timeout: int = 10_000) -> None:
        """Wait until the current URL is different from the original."""
        self.page.wait_for_function(
            f"() => window.location.href !== '{original_url}'",
            timeout=timeout,
        )

    def wait_for_text_in_element(
        self, selector: str, text: str, timeout: int = 10_000
    ) -> None:
        """Wait until an element's text contains the expected substring."""
        self.page.locator(selector).filter(has_text=text).wait_for(
            state="visible", timeout=timeout
        )

    # ── scroll utilities ──────────────────────────────────────────

    def scroll_to_bottom(self) -> None:
        """Scroll to the very bottom of the page."""
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def scroll_to_top(self) -> None:
        """Scroll back to the top of the page."""
        self.page.evaluate("window.scrollTo(0, 0)")

    # ── current page info ─────────────────────────────────────────

    def get_current_url(self) -> str:
        """Return the current page URL."""
        return self.page.url

    def get_page_title(self) -> str:
        """Return the current browser tab title."""
        return self.page.title()

    # ── auth helpers ──────────────────────────────────────────────

    def login(self, username_selector: str, password_selector: str,
              submit_selector: str, username: str, password: str) -> None:
        """
        Generic login flow.
        PageObjects call this with their specific selectors.
        Credentials come from TestContext or DataFactory — never hardcoded.
        """
        self.actions.fill(username_selector, username)
        self.actions.fill(password_selector, password)
        self.actions.click(submit_selector)
        self.actions.wait_for_page_load()

    # ── network helpers ───────────────────────────────────────────

    def wait_for_api_response(self, url_pattern: str, timeout: int = 15_000) -> dict:
        """
        Wait for a network response matching the URL pattern.
        Returns the parsed JSON body.
        Useful for asserting API calls triggered by UI actions.
        """
        with self.page.expect_response(
            lambda r: url_pattern in r.url and r.status == 200,
            timeout=timeout,
        ) as response_info:
            pass   # caller triggers the action before this point
        return response_info.value.json()
