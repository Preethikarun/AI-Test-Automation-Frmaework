"""
pages/trademe_results_page.py

PageObject for the Trade Me property search results screen.
Handles result card inspection, filter interactions, sorting, and pagination.

Access locators as:  self.loc["section"]["key"]
Never call page.locator() directly — always go through Actions.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from locators.trademe_results_locators import TRADEME_RESULTS_LOCATORS
from utils.actions import Actions
from utils.functions import Functions


class TradeMeResultsPage:
    """PageObject for the Trade Me property search results screen."""

    def __init__(self, page: Page):
        self.page      = page
        self.actions   = Actions(page)
        self.functions = Functions(page)
        self.loc       = TRADEME_RESULTS_LOCATORS

    # ── result count / header ─────────────────────────────────────

    @allure.step("Get result count text")
    def get_result_count_text(self) -> str:
        """Return the raw text of the result count heading."""
        return self.actions.get_text(self.loc["header"]["result_count"])

    @allure.step("Sort results by: '{option}'")
    def sort_by(self, option: str) -> None:
        """Select a sort option from the sort dropdown."""
        self.actions.select(self.loc["header"]["sort_select"], option)
        self.actions.wait_for_page_load()

    # ── listing cards ─────────────────────────────────────────────

    @allure.step("Count visible listing cards")
    def count_cards(self) -> int:
        """Return the number of visible listing cards on the page."""
        return self.actions.count(self.loc["cards"]["item"])

    @allure.step("Get price of card at index {index}")
    def get_card_price(self, index: int = 0) -> str:
        """Return the price text from the card at the given zero-based index."""
        items = self.actions.get_all_texts(self.loc["cards"]["price"])
        return items[index] if items else ""

    @allure.step("Get suburb of card at index {index}")
    def get_card_suburb(self, index: int = 0) -> str:
        """Return the suburb text from the card at the given zero-based index."""
        items = self.actions.get_all_texts(self.loc["cards"]["suburb"])
        return items[index] if items else ""

    @allure.step("Get bedrooms of card at index {index}")
    def get_card_bedrooms(self, index: int = 0) -> str:
        """Return the bedrooms text from the card at the given zero-based index."""
        items = self.actions.get_all_texts(self.loc["cards"]["bedrooms"])
        return items[index] if items else ""

    @allure.step("Click first listing card")
    def click_first_card(self) -> None:
        """Click the first listing card to open the detail page."""
        self.actions.click(self.loc["cards"]["first_item"])
        self.actions.wait_for_page_load()

    # ── price filter ──────────────────────────────────────────────

    @allure.step("Open price filter panel")
    def open_price_filter(self) -> None:
        """Click the Price filter dropdown to reveal the price inputs."""
        self.functions.accept_cookies()
        self.actions.wait_for_visible(
            self.loc["price_filter"]["price_filter_dropdown"], timeout=30_000
        )
        self.actions.scroll_into_view(self.loc["price_filter"]["price_filter_dropdown"])
        self.actions.click(self.loc["price_filter"]["price_filter_dropdown"])
        self.actions.wait_for_visible(self.loc["price_filter"]["min_input"])

    @allure.step("Apply price filter: ${min_price} - ${max_price}")
    def apply_price_filter(self, min_price: str, max_price: str) -> None:
        """
        Open price filter, fill min/max inputs, and apply.

        Args:
            min_price: minimum price as a string (e.g. "500000")
            max_price: maximum price as a string (e.g. "800000")
        """
        self.open_price_filter()
        self.actions.select(self.loc["price_filter"]["min_input"], min_price)
        self.actions.select(self.loc["price_filter"]["max_input"], max_price)
        self.actions.click(self.loc["price_filter"]["apply_button"])
        self.actions.wait_for_page_load()

    # ── suburb filter ─────────────────────────────────────────────

    @allure.step("Open suburb filter panel")
    def open_suburb_filter(self) -> None:
        """Click the Location filter button to reveal the suburb input."""
        self.actions.click(self.loc["suburb_filter"]["open_button"])
        self.actions.wait_for_visible(self.loc["suburb_filter"]["input"])

    @allure.step("Apply suburb filter: '{suburb}'")
    def apply_suburb_filter(self, suburb: str) -> None:
        """Open suburb filter, type suburb name, and apply."""
        self.open_suburb_filter()
        self.actions.fill(self.loc["suburb_filter"]["input"], suburb)
        self.actions.click(self.loc["suburb_filter"]["apply_button"])
        self.actions.wait_for_page_load()

    # ── bedrooms filter ───────────────────────────────────────────

    @allure.step("Open bedrooms filter panel")
    def open_bedrooms_filter(self) -> None:
        """Click the Bedrooms filter button to reveal the bedrooms select."""
        self.actions.click(self.loc["bedrooms_filter"]["open_button"])
        self.actions.wait_for_visible(self.loc["bedrooms_filter"]["select"])

    @allure.step("Apply bedrooms filter: '{value}'")
    def apply_bedrooms_filter(self, value: str) -> None:
        """Open bedrooms filter, select value, and apply."""
        self.open_bedrooms_filter()
        self.actions.select(self.loc["bedrooms_filter"]["select"], value)
        self.actions.click(self.loc["bedrooms_filter"]["apply_button"])
        self.actions.wait_for_page_load()

    # ── pagination ────────────────────────────────────────────────

    @allure.step("Check if pagination is visible")
    def pagination_visible(self) -> bool:
        """Return True if the pagination nav is present."""
        return self.actions.is_visible(self.loc["pagination"]["container"])

    @allure.step("Go to next page")
    def go_to_next_page(self) -> None:
        """Click the Next page button and wait for load."""
        self.actions.click(self.loc["pagination"]["next_button"])
        self.actions.wait_for_page_load()

    # ── filter aliases (facade-facing names) ─────────────────────

    @allure.step("Filter by suburb: '{suburb}'")
    def filter_by_suburb(self, suburb: str) -> None:
        """Alias for apply_suburb_filter — used by TradeMeFacade."""
        self.apply_suburb_filter(suburb)

    @allure.step("Filter by bedrooms: '{value}'")
    def filter_by_bedrooms(self, value: str) -> None:
        """Alias for apply_bedrooms_filter — used by TradeMeFacade."""
        self.apply_bedrooms_filter(value)

    # ── navigation into listings ──────────────────────────────────

    @allure.step("Open first listing card")
    def open_first_listing(self) -> None:
        """Click the first listing card to navigate to the detail page."""
        self.click_first_card()

    @allure.step("Open listing at position {index}")
    def open_listing_at(self, index: int) -> None:
        """Click the listing card at the given zero-based index."""
        items = self.page.locator(self.loc["cards"]["item"])
        items.nth(index).click()
        self.actions.wait_for_page_load()

    # ── wait helpers ──────────────────────────────────────────────

    @allure.step("Wait for results to be visible")
    def wait_for_results(self) -> None:
        """Wait until the results card list is visible on the page."""
        self.actions.wait_for_visible(self.loc["cards"]["list"])

    # ── state checks ─────────────────────────────────────────────

    @allure.step("Check if results cards list is visible")
    def results_visible(self) -> bool:
        """Return True if at least one listing card is present."""
        return self.actions.is_visible(self.loc["cards"]["list"])

    @allure.step("Check if results are present (alias)")
    def has_results(self) -> bool:
        """Return True if results are present — alias used by TradeMeFacade."""
        return self.results_visible()

    @allure.step("Get result count as integer")
    def get_result_count(self) -> int:
        """Return the number of visible listing cards as an integer."""
        return self.count_cards()

    @allure.step("Check if no-results message is shown")
    def no_results_shown(self) -> bool:
        """Return True if the empty-state 'no results' message is visible."""
        return self.actions.is_visible(self.loc["state"]["no_results"])

    @allure.step("Check if loading spinner is visible")
    def is_loading(self) -> bool:
        """Return True if the loading spinner/progressbar is present."""
        return self.actions.is_visible(self.loc["state"]["loading_spinner"])
