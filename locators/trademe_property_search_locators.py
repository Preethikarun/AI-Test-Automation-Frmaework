"""
locators/trademe_property_search_locators.py

Locator skeleton for trademe property_search screen.
Fill each empty string value from DevTools inspection.

Selector priority:
  data-testid > aria-label > name attribute > CSS class

Never use auto-generated class names (e.g. sc-abc123).
"""

# Selector priority: data-testid > aria-label > name > CSS class

TRADEME_PROPERTY_SEARCH_LOCATORS = {

    # -------------------------------------------------------------------------
    # SEARCH BAR
    # -------------------------------------------------------------------------
    "search_input": "",                  # inspect: main keyword/search text input field on the property search page
    "search_button": "",                 # inspect: primary Search / Find button next to the search input

    # -------------------------------------------------------------------------
    # PRICE FILTER
    # -------------------------------------------------------------------------
    "min_price_input": "",               # inspect: minimum price input field in the filter/refine panel
    "max_price_input": "",               # inspect: maximum price input field in the filter/refine panel

    # -------------------------------------------------------------------------
    # SUBURB FILTER
    # -------------------------------------------------------------------------
    "suburb_filter_input": "",           # inspect: suburb text input field in the filter/refine panel

    # -------------------------------------------------------------------------
    # BEDROOMS FILTER
    # -------------------------------------------------------------------------
    "bedrooms_dropdown": "",             # inspect: bedrooms select/dropdown element in the filter/refine panel

    # -------------------------------------------------------------------------
    # APPLY / SUBMIT FILTER
    # -------------------------------------------------------------------------
    "apply_filter_button": "",           # inspect: Apply / Refine / Update Results button that submits filter changes

    # -------------------------------------------------------------------------
    # SEARCH RESULTS LIST
    # -------------------------------------------------------------------------
    "results_container": "",             # inspect: outer container / section that wraps all listing cards in results
    "listing_cards": "",                 # inspect: repeating listing card elements within the results container
    "first_listing_card": "",            # inspect: first individual listing card (nth-child(1) or :first-of-type)
    "listing_card_price": "",            # inspect: price label displayed on each listing card in results
    "listing_card_suburb": "",           # inspect: suburb / location label displayed on each listing card
    "listing_card_bedrooms": "",         # inspect: bedrooms count badge/label on each listing card

    # -------------------------------------------------------------------------
    # LISTING DETAIL PAGE — HEADER / TITLE
    # -------------------------------------------------------------------------
    "detail_page_title": "",             # inspect: main heading / property title at the top of the listing detail page
    "detail_page_address": "",           # inspect: full address element on the listing detail page

    # -------------------------------------------------------------------------
    # LISTING DETAIL PAGE — PRICE
    # -------------------------------------------------------------------------
    "detail_page_price": "",             # inspect: price element displayed prominently on the listing detail page

    # -------------------------------------------------------------------------
    # LISTING DETAIL PAGE — AGENT INFO
    # -------------------------------------------------------------------------
    "detail_agent_name": "",             # inspect: agent or agency name element on the listing detail page
    "detail_agent_contact": "",          # inspect: agent contact number or email element on the listing detail page
    "detail_agent_logo": "",             # inspect: agent/agency logo image on the listing detail page

    # -------------------------------------------------------------------------
    # LISTING DETAIL PAGE — GENERAL
    # -------------------------------------------------------------------------
    "detail_page_container": "",         # inspect: outer wrapper/container of the entire listing detail page body

    # -------------------------------------------------------------------------
    # PAGINATION (results list)
    # -------------------------------------------------------------------------
    "pagination_container": "",          # inspect: pagination bar below the results listing
    "next_page_button": "",              # inspect: Next page arrow/button in pagination

    # -------------------------------------------------------------------------
    # NO RESULTS / EMPTY STATE
    # -------------------------------------------------------------------------
    "no_results_message": "",            # inspect: message element displayed when a search returns zero listings

    # -------------------------------------------------------------------------
    # LOADING / PROGRESS INDICATORS
    # -------------------------------------------------------------------------
    "results_loading_spinner": "",       # inspect: spinner or skeleton loader shown while results are fetching

}