"""
pages/trademe_listing_page.py

PageObject for the Trade Me property listing detail screen.
Handles reading listing details, agent info, media, and call-to-action buttons.

Access locators as:  self.loc["section"]["key"]
Never call page.locator() directly — always go through Actions.
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from locators.trademe_listing_locators import TRADEME_LISTING_LOCATORS
from utils.actions import Actions
from utils.functions import Functions


class TradeMeListingPage:
    """PageObject for the Trade Me property listing detail screen."""

    def __init__(self, page: Page):
        self.page      = page
        self.actions   = Actions(page)
        self.functions = Functions(page)
        self.loc       = TRADEME_LISTING_LOCATORS

    # ── page load ─────────────────────────────────────────────────

    @allure.step("Wait for listing detail page to load")
    def wait_for_load(self) -> None:
        """Wait until the listing title heading is visible."""
        self.actions.wait_for_page_load()
        self.actions.wait_for_visible(self.loc["page"]["loaded"])

    @allure.step("Check if listing detail container is present")
    def is_loaded(self) -> bool:
        """Return True if the main listing container is visible."""
        return self.actions.is_visible(self.loc["page"]["container"])

    # ── core listing details ──────────────────────────────────────

    @allure.step("Get listing title")
    def get_title(self) -> str:
        """Return the text of the listing title heading."""
        return self.actions.get_text(self.loc["details"]["title"])

    @allure.step("Get listing price")
    def get_price(self) -> str:
        """Return the displayed price text."""
        return self.actions.get_text(self.loc["details"]["price"])

    @allure.step("Get listing address")
    def get_address(self) -> str:
        """Return the property address text."""
        return self.actions.get_text(self.loc["details"]["address"])

    @allure.step("Get bedroom count")
    def get_bedrooms(self) -> str:
        """Return the bedrooms count text."""
        return self.actions.get_text(self.loc["details"]["bedrooms"])

    @allure.step("Get bathroom count")
    def get_bathrooms(self) -> str:
        """Return the bathrooms count text."""
        return self.actions.get_text(self.loc["details"]["bathrooms"])

    @allure.step("Get listing description")
    def get_description(self) -> str:
        """Return the full description text of the listing."""
        return self.actions.get_text(self.loc["details"]["description"])

    # ── agent / agency ────────────────────────────────────────────

    @allure.step("Get agent name")
    def get_agent_name(self) -> str:
        """Return the name of the listing agent."""
        return self.actions.get_text(self.loc["agent"]["name"])

    @allure.step("Get agent contact details")
    def get_agent_contact(self) -> str:
        """Return the agent's phone number or contact link text."""
        return self.actions.get_text(self.loc["agent"]["contact"])

    @allure.step("Check if agent logo is visible")
    def agent_logo_visible(self) -> bool:
        """Return True if the agency logo image is present."""
        return self.actions.is_visible(self.loc["agent"]["logo"])

    # ── media gallery ─────────────────────────────────────────────

    @allure.step("Check if photo gallery is visible")
    def photo_gallery_visible(self) -> bool:
        """Return True if the photo gallery section is present."""
        return self.actions.is_visible(self.loc["media"]["photo_gallery"])

    @allure.step("Check if first photo is visible")
    def first_photo_visible(self) -> bool:
        """Return True if the first gallery photo is present."""
        return self.actions.is_visible(self.loc["media"]["first_photo"])

    # ── call-to-action buttons ────────────────────────────────────

    @allure.step("Click Enquire button")
    def click_enquire(self) -> None:
        """Click the Enquire button to open the enquiry form."""
        self.actions.click(self.loc["actions"]["enquire_button"])

    @allure.step("Check if Enquire button is visible")
    def enquire_button_visible(self) -> bool:
        """Return True if the Enquire button is present on the page."""
        return self.actions.is_visible(self.loc["actions"]["enquire_button"])

    @allure.step("Click Save button")
    def click_save(self) -> None:
        """Click the Save / watchlist button."""
        self.actions.click(self.loc["actions"]["save_button"])

    @allure.step("Check if Save button is visible")
    def save_button_visible(self) -> bool:
        """Return True if the Save button is present on the page."""
        return self.actions.is_visible(self.loc["actions"]["save_button"])
