"""
pages/trademe_search_page.py

PageObject for the Trade Me property search screen.
Handles navigation, search input, and filter interactions.

Access locators as:  self.loc["section"]["key"]
Never call page.locator() directly — always go through Actions.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from locators.trademe_property_search_locators import TRADEME_PROPERTY_SEARCH_LOCATORS
from utils.actions import Actions
from utils.functions import Functions


class TradeMeSearchPage:
    """PageObject for the Trade Me property search screen."""

    URL = "https://www.trademe.co.nz/a/property/residential/sale"

    def __init__(self, page: Page):
        self.page      = page
        self.actions   = Actions(page)
        self.functions = Functions(page)
        self.loc       = TRADEME_PROPERTY_SEARCH_LOCATORS

    # ── navigation ───────────────────────────────────────────────

    @allure.step("Navigate to Trade Me property search")
    def navigate(self) -> None:
        """Navigate to the property search page and wait for load."""
        self.page.goto(self.URL)
        self.actions.wait_for_page_load()
        # wait for the search input to confirm the page is interactive
        # (the locator dict has no "page" section — use "search"."input" as
        #  the readiness signal instead)
        self.actions.wait_for_visible(self.loc["search"]["input"])

    # ── search bar ───────────────────────────────────────────────

    @allure.step("Enter search term: '{term}'")
    def enter_search_term(self, term: str) -> None:
        """Type a search term into the keyword input."""
        self.actions.wait_for_visible(self.loc["search"]["input"])
        self.actions.fill(self.loc["search"]["input"], term)

    @allure.step("Submit search")
    def submit_search(self) -> None:
        """Press Enter on the search input to submit (avoids overlay click issues)."""
        self.actions.wait_for_visible(self.loc["search"]["input"])
        # Focus the input and press Enter to submit
        self.page.locator(self.loc["search"]["input"]).focus()
        self.actions.press_key("Enter")
        self.actions.wait_for_page_load()

    @allure.step("Search for: '{term}'")
    def search_for(self, term: str) -> None:
        """Enter a term and submit — combined convenience method."""
        self.enter_search_term(term)
        self.submit_search()

    # ── price filter ─────────────────────────────────────────────

    @allure.step("Set price filter: ${min_price} - ${max_price}")
    def apply_price_filter(self, min_price: str, max_price: str) -> None:
        """
        Fill the min and max price filter inputs and apply.

        Args:
            min_price: minimum price as a string (e.g. "500000")
            max_price: maximum price as a string (e.g. "800000")
        """
        self.actions.fill(self.loc["filters"]["min_price"], min_price)
        self.actions.fill(self.loc["filters"]["max_price"], max_price)
        self.actions.click(self.loc["filters"]["apply_button"])
        self.actions.wait_for_page_load()

    # ── suburb filter ────────────────────────────────────────────

    @allure.step("Filter by suburb: '{suburb}'")
    def apply_suburb_filter(self, suburb: str) -> None:
        """Type a suburb name into the location filter and apply."""
        self.actions.fill(self.loc["filters"]["suburb"], suburb)
        self.actions.click(self.loc["filters"]["apply_button"])
        self.actions.wait_for_page_load()

    # ── bedrooms filter ──────────────────────────────────────────

    @allure.step("Filter by bedrooms: '{value}'")
    def select_bedrooms(self, value: str) -> None:
        """Select a bedroom count from the bedrooms dropdown."""
        self.actions.select(self.loc["filters"]["bedrooms"], value)
        self.actions.click(self.loc["filters"]["apply_button"])
        self.actions.wait_for_page_load()

    # ── state checks ─────────────────────────────────────────────

    @allure.step("Check if results container is visible")
    def results_visible(self) -> bool:
        return self.actions.is_visible(self.loc["results"]["container"])

    @allure.step("Check if no-results message is shown")
    def no_results_shown(self) -> bool:
        return self.actions.is_visible(self.loc["state"]["no_results"])
