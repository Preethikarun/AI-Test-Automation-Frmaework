"""
Locators for the TradeMe Property Search page.
URL: https://www.trademe.co.nz/a/property/residential/sale

Organised as nested dicts by UI section.
Fill each empty string value from DevTools inspection.

Selector strategy (preferred order):
  1. ARIA role + accessible name          →  role=button[name='Search']
  2. Placeholder / user-facing attribute  →  //input[@placeholder='...']
  3. aria-label                           →  //input[@aria-label='...']
  4. Stable text content                  →  //button[normalize-space()='Apply']
  5. Structural XPath                     →  //section[@data-testid='results']//li
  (Never use auto-generated class names like sc-abc123)
"""

TRADEME_PROPERTY_SEARCH_LOCATORS = {

    # ── search bar ────────────────────────────────────────────────────────────
    "search": {
        "input":            "",     # //input[@aria-label='Search'] or [@placeholder='...']
        "button":           "",     # //button[normalize-space()='Search'] or [@aria-label='Search']
    },

    # ── filter panel ─────────────────────────────────────────────────────────
    "filters": {
        "min_price":        "",     # //input[@aria-label='Minimum price'] or [@placeholder='Min price']
        "max_price":        "",     # //input[@aria-label='Maximum price'] or [@placeholder='Max price']
        "suburb":           "",     # //input[@aria-label='Suburb'] or [@placeholder='Suburb']
        "bedrooms":         "",     # //select[@aria-label='Bedrooms'] or [@name='bedrooms']
        "apply_button":     "",     # //button[normalize-space()='Apply'] or [normalize-space()='Refine']
    },

    # ── results list ─────────────────────────────────────────────────────────
    "results": {
        "container":        "",     # //section[@data-testid='search-results'] or role=list
        "cards":            "",     # //section[...]//li or //article[contains(@class,'listing')]
        "first_card":       "",     # (//article[contains(@class,'listing')])[1]
        "card_price":       "",     # //article[...]//span[@data-testid='price'] or [@aria-label='Price']
        "card_suburb":      "",     # //article[...]//span[@data-testid='suburb'] or [@aria-label='Suburb']
        "card_bedrooms":    "",     # //article[...]//span[@data-testid='bedrooms'] or [@aria-label='Bedrooms']
    },

    # ── listing detail — header ───────────────────────────────────────────────
    "detail_header": {
        "title":            "",     # //h1[@data-testid='listing-title'] or role=heading[level=1]
        "address":          "",     # //address or //*[@data-testid='listing-address']
    },

    # ── listing detail — price ────────────────────────────────────────────────
    "detail_price": {
        "value":            "",     # //*[@data-testid='listing-price'] or [@aria-label='Listing price']
    },

    # ── listing detail — agent ────────────────────────────────────────────────
    "detail_agent": {
        "name":             "",     # //*[@data-testid='agent-name'] or [@aria-label='Agent name']
        "contact":          "",     # //a[@data-testid='agent-phone'] or [@aria-label='Agent phone']
        "logo":             "",     # //img[@data-testid='agent-logo'] or [@alt='Agency logo']
    },

    # ── listing detail — container ────────────────────────────────────────────
    "detail_page": {
        "container":        "",     # //main[@data-testid='listing-detail'] or role=main
    },

    # ── pagination ────────────────────────────────────────────────────────────
    "pagination": {
        "container":        "",     # //nav[@aria-label='Pagination'] or [@data-testid='pagination']
        "next_button":      "",     # //a[@aria-label='Next page'] or //button[normalize-space()='Next']
    },

    # ── empty / loading states ────────────────────────────────────────────────
    "state": {
        "no_results":       "",     # //*[@data-testid='no-results'] or [normalize-space()='No results found']
        "loading_spinner":  "",     # //*[@role='progressbar'] or [@data-testid='loading-spinner']
    },
}
