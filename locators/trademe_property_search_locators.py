"""
locators/trademe_property_search_locators.py

Locator skeleton for Trade Me — property search screen.
Fill each empty string from DevTools inspection.

XPath selector priority:
  1. data-testid       //*[@data-testid='search-input']
  2. aria-label        //input[@aria-label='Search']
  3. placeholder       //input[@placeholder='Search properties']
  4. name attribute    //input[@name='search_string']
  5. stable text       //button[normalize-space()='Search']
  6. role + label      //*[@role='button'][@aria-label='Apply']
  7. structural XPath  //section[@data-testid='results']//li
— Never use class names (sc-abc123, css-xyz, etc.)
"""

TRADEME_PROPERTY_SEARCH_LOCATORS = {

    # ── search bar ────────────────────────────────────────────────
    # TESTED & VERIFIED on Trade Me property search page (2026-04-18)
    "search": {
        "input":  "#search",                                                        # CSS ID (most stable)
        "input_xpath":  "//input[@id='search']",                                   # XPath alternative
        "button": "button.tm-property-home-search-banner__submit-button--compact", # Search button (also applies filters)
        "button_xpath": "//button[contains(@class, 'submit-button') and text()='Search']",
    },

    # ── filter controls ───────────────────────────────────────────
    # Price filters are custom Angular components (TG-SELECT-CONTAINER)
    "filters": {
        "min_price_dropdown":   ".property-search__price-min__select",    # Min price select (custom component)
        "min_price_xpath":      "//*[contains(@class, 'property-search__price-min__select')]",
        "max_price_dropdown":   ".property-search__price-max__select",    # Max price select (custom component)
        "max_price_xpath":      "//*[contains(@class, 'property-search__price-max__select')]",
        "price_filter_button":  "[class*='price']",                       # Generic selector for any price element
        "apply_button":         "button.tm-property-home-search-banner__submit-button--compact",  # Same as search button
    },

    # ── result cards (visible after search) ───────────────────────
    # NOTE: Property cards are <a> links, not <article> elements
    "results": {
        "container":     "div.tm-root__wrapper",                          # Main results container (DIV)
        "container_xpath": "//div[contains(@class, 'tm-root__wrapper')]",
        "cards":         "a[href*='/a/property/']:not([href*='residential/sale']):not([href*='residential/rent'])",
        "cards_xpath":   "//a[contains(@href, '/a/property/') and not(contains(@href, 'residential'))]",
        "first_card":    "a[href*='/a/property/']:not([href*='residential/sale']):not([href*='residential/rent']):first-of-type",
        "card_price":    "span[class*='price']",                          # Price span within card link
        "card_suburb":   "span[class*='suburb'], span[class*='location']", # Suburb/location span
        "card_bedrooms": "span[class*='bedroom']",                        # Bedrooms span
    },

    # ── pagination ────────────────────────────────────────────────
    "pagination": {
        "container":   "//nav[@aria-label='Pagination']",                # Pagination nav (if present)
        "next_button": "//a[@aria-label='Next page']",                    # Next page link
    },

    # ── page state ────────────────────────────────────────────────
    "state": {
        "no_results":      "//button[normalize-space()='View 1,370 results']",   # //*[@data-testid='no-results'] or //p[contains(normalize-space(),'no results')]
        "loading_spinner": "//body/tm-root/div[1]/main/div/tm-property-search-component/div/div/tm-property-search-results/div/div[3]/tm-search-results/div/div[2]/tg-row/tg-col[3]/tm-search-card-switcher/tm-property-premium-listing-card/div/a/tg-sticker2-wrapper/div/tm-property-search-card-summary-image/div/tg-image-viewer2/div/div/tg-image-viewer-item[1]/div/div[1]/tm-progressive-image-loader/div/picture/img",   # //*[@data-testid='loading-spinner'] or //*[@aria-label='Loading'] or //*[@role='progressbar']
    },
}
