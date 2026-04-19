"""
facade/trademe_facade.py

Trade Me sample facade — used as the reference implementation
for how any app's facade should be structured.

Primary flow covered:
Property Search → Apply Filter → View Listing Detail

This facade is Trade Me specific.
For any other app, create {app}_facade.py following the same pattern:
- __init__ accepts page + optional TestContext
- One method per business flow
- All methods return the final PageObject for assertions
- @allure.step on every method
- Assertion helpers at the bottom (never assert in step definitions)

Step definitions call this. E2E Specs call this.
PageObjects are never called directly from steps or tests.
"""

from __future__ import annotations

from typing import Optional

import allure
from playwright.sync_api import Page

from pages.trademe_search_page import TradeMeSearchPage
from pages.trademe_results_page import TradeMeResultsPage
from pages.trademe_listing_page import TradeMeListingPage
from api.runner import Runner, RunResult
from context import TestContext


class TradeMeFacade:
    """
    Orchestrates Trade Me flows.

    Generic framework note:
        This class is the sample implementation.
        Copy this pattern for every new app under test.
        Only the page imports and method implementations change.
        The structure (sections, naming, return types) stays identical.
    """

    # API definition paths — relative to project root
    PROPERTY_SEARCH_DEF = "testCases/api/rest/property_search.json"

    def __init__(self, page: Page, tc: Optional[TestContext] = None):
        self.page     = page
        self.tc       = tc

        # instantiate all pages this facade needs
        self._search  = TradeMeSearchPage(page)
        self._results = TradeMeResultsPage(page)
        self._listing = TradeMeListingPage(page)

    # ══════════════════════════════════════════════════════════════
    # SECTION 1 — Primary flow: Search → Filter → Listing Detail
    # ══════════════════════════════════════════════════════════════

    @allure.step("Trade Me: navigate to property search page")
    def navigate_to_search_page(self) -> None:
        """
        Open the Trade Me property search page and wait for it to load.
        Called by BDD Background steps before any search action.

        BDD step:
            Given the Trade Me property search page is open
        """
        self._search.navigate()

    @allure.step("Trade Me: search → filter → view first listing detail")
    def search_filter_and_view_detail(
        self,
        term:      str,
        min_price: str = "",
        max_price: str = "",
        bedrooms:  str = "",
    ) -> TradeMeListingPage:
        """
        Primary test flow — the full property search journey.

        1. Navigate to property search
        2. Enter search term
        3. Apply price filter (optional)
        4. Apply bedroom filter (optional)
        5. Open the first listing
        6. Return listing detail page for assertions

        BDD step:
            @when('I search for "{term}", filter and open the first listing')

        E2E Spec:
            listing = facade.search_filter_and_view_detail(
                "Wellington homes", min_price="500000", max_price="800000"
            )
            assert listing.is_loaded()
            assert listing.get_price() != ""
        """
        with allure.step(f"Navigate and search for '{term}'"):
            self._search.navigate()
            self._search.search_for(term)
            self._results.wait_for_results()

        with allure.step("Apply filters"):
            if min_price or max_price:
                self._results.apply_price_filter(min_price, max_price)
            if bedrooms:
                self._results.filter_by_bedrooms(bedrooms)

        with allure.step("Open first listing"):
            self._results.open_first_listing()

        with allure.step("Verify listing detail page loaded"):
            self._listing.wait_for_load()

        return self._listing

    @allure.step("Trade Me: search → filter → view listing at position {index}")
    def search_filter_and_view_listing_at(
        self,
        term:      str,
        index:     int,
        min_price: str = "",
        max_price: str = "",
    ) -> TradeMeListingPage:
        """
        Same as search_filter_and_view_detail but opens a specific
        listing position (0-based index) instead of the first.

        BDD step:
            @when('I search for "{term}" and open listing {index}')
        """
        with allure.step(f"Navigate and search for '{term}'"):
            self._search.navigate()
            self._search.search_for(term)
            self._results.wait_for_results()

        with allure.step("Apply price filter"):
            if min_price or max_price:
                self._results.apply_price_filter(min_price, max_price)

        with allure.step(f"Open listing at position {index}"):
            self._results.open_listing_at(index)
            self._listing.wait_for_load()

        return self._listing

    # ══════════════════════════════════════════════════════════════
    # SECTION 2 — Search + Filter only (no detail navigation)
    # ══════════════════════════════════════════════════════════════

    @allure.step("Trade Me: search only for '{term}'")
    def search_only(self, term: str) -> TradeMeResultsPage:
        """
        Navigate and search. No filter applied.
        Returns results page for count / visibility assertions.

        BDD step:
            @when('I search for "{term}"')
        """
        self._search.navigate()
        self._search.search_for(term)
        self._results.wait_for_results()
        return self._results

    @allure.step("Trade Me: search and filter — '{term}' ${min_price}–${max_price}")
    def search_and_filter(
        self,
        term:      str,
        min_price: str = "",
        max_price: str = "",
    ) -> TradeMeResultsPage:
        """
        Search and apply price filter.
        Returns results page for count / visibility assertions.

        BDD step:
            @when('I search for "{term}" between "${min}" and "${max}"')
        """
        self._search.navigate()
        self._search.search_for(term)
        self._results.wait_for_results()

        if min_price or max_price:
            self._results.apply_price_filter(min_price, max_price)

        return self._results

    @allure.step("Trade Me: search and filter by suburb '{suburb}'")
    def search_and_filter_by_suburb(
        self,
        term:   str,
        suburb: str,
    ) -> TradeMeResultsPage:
        """Search then filter by suburb name."""
        self._search.navigate()
        self._search.search_for(term)
        self._results.wait_for_results()
        self._results.filter_by_suburb(suburb)
        return self._results

    # ══════════════════════════════════════════════════════════════
    # SECTION 3 — API + UI combined E2E flows
    # ══════════════════════════════════════════════════════════════

    @allure.step("E2E: API confirms → UI searches → detail view loaded")
    def api_confirms_ui_searches_and_views_detail(
        self,
        term:      str,
        min_price: str = "",
        max_price: str = "",
    ) -> dict:
        """
        Full E2E flow:
        1. API confirms property data exists in backend
        2. UI searches, filters, and opens listing detail
        3. Returns combined result dict for independent assertions

        One Playwright trace covers all three steps.
        Windsurf generates both API test and UI test from same trace.

        Returns:
        {
            "api_passed":       bool,
            "api_response":     APIResponse,
            "ui_has_results":   bool,
            "ui_count":         int,
            "listing_loaded":   bool,
            "listing_price":    str,
            "listing_title":    str,
        }

        Used by: tests/e2e/test_e2e_property.py
        """
        result = {
            "api_passed":     False,
            "api_response":   None,
            "ui_has_results": False,
            "ui_count":       0,
            "listing_loaded": False,
            "listing_price":  "",
            "listing_title":  "",
        }

        # Step 1 — API confirms backend has data
        with allure.step("API: confirm property data in backend"):
            api_result: RunResult = Runner.run(self.PROPERTY_SEARCH_DEF)
            result["api_passed"]   = api_result.passed
            result["api_response"] = api_result.response

            if self.tc:
                self.tc.post_back(api_result.response)

            allure.attach(
                f"status={api_result.response.status}  "
                f"mocked={api_result.response.mocked}  "
                f"passed={api_result.passed}",
                name="API result",
                attachment_type=allure.attachment_type.TEXT,
            )

        # Step 2 — UI searches and filters
        with allure.step("UI: search and apply filters"):
            results_page             = self.search_and_filter(
                term, min_price, max_price
            )
            result["ui_has_results"] = results_page.has_results()
            result["ui_count"]       = results_page.get_result_count()

        # Step 3 — Open first listing detail
        if result["ui_has_results"]:
            with allure.step("UI: open first listing detail"):
                results_page.open_first_listing()
                self._listing.wait_for_load()
                result["listing_loaded"] = self._listing.is_loaded()
                result["listing_price"]  = self._listing.get_price()
                result["listing_title"]  = self._listing.get_title()

            allure.attach(
                f"listing_loaded={result['listing_loaded']}\n"
                f"title={result['listing_title']}\n"
                f"price={result['listing_price']}",
                name="Listing detail",
                attachment_type=allure.attachment_type.TEXT,
            )

        return result

    # ══════════════════════════════════════════════════════════════
    # SECTION 4 — Assertion helpers
    # Called from step definitions — assertions never in step code
    # ══════════════════════════════════════════════════════════════

    def assert_has_results(self) -> None:
        """Assert results page has at least one listing."""
        count = self._results.get_result_count()
        assert count > 0, (
            f"Expected at least one listing but found {count}"
        )

    def assert_result_count_above(self, minimum: int) -> None:
        """Assert result count is at or above minimum."""
        count = self._results.get_result_count()
        assert count >= minimum, (
            f"Expected at least {minimum} listings but found {count}"
        )

    def assert_listing_title_contains(self, text: str) -> None:
        """Assert listing detail title contains expected text."""
        title = self._listing.get_title()
        assert text.lower() in title.lower(), (
            f"Expected '{text}' in title but got '{title}'"
        )

    def assert_listing_price_present(self) -> None:
        """Assert listing detail shows a price."""
        price = self._listing.get_price()
        assert price, "Expected a price on the listing detail page but got empty string"

    def assert_listing_loaded(self) -> None:
        """Assert listing detail page is fully loaded."""
        assert self._listing.is_loaded(), (
            "Listing detail page did not load correctly"
        )
