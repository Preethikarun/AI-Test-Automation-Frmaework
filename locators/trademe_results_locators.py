"""
locators/trademe_results_locators.py

Locator skeleton for Trade Me — search results screen.
Fill each empty string from DevTools inspection.

XPath selector priority:
  1. data-testid       //*[@data-testid='result-count']
  2. aria-label        //input[@aria-label='Minimum price']
  3. placeholder       //input[@placeholder='Min price']
  4. name attribute    //input[@name='price_min']
  5. stable text       //button[normalize-space()='Apply']
  6. role + label      //*[@role='button'][@aria-label='Next page']
  7. structural XPath  //nav[@aria-label='Pagination']//li
— Never use class names (sc-abc123, css-xyz, etc.)

INSPECTION TIPS
- Open each filter panel before inspecting — inner inputs only appear
    when the panel is expanded.
- "View N Results" button text changes dynamically — use:
      //button[contains(normalize-space(),'result')]
- Listing cards repeat — target all with:
      //*[@data-testid='listing-card']
"""

TRADEME_RESULTS_LOCATORS = {

    # ── results header ────────────────────────────────────────────
    "header": {
        "result_count": "//p[contains(normalize-space(),'properties')]",   # Result count text
        "sort_select":  "//select[@aria-label='Sort by']",                 # Sort dropdown
    },

    # ── listing cards ─────────────────────────────────────────────
    "cards": {
        "list":       "div.tm-root__wrapper",                             # Container with all result cards
        "item":       "a[href*='/a/property/']:not([href*='residential/sale'])", # Individual property card link
        "first_item": "a[href*='/a/property/']:not([href*='residential/sale']) >> nth=0", # First card only
        "price":      "span[class*='price']",                            # Price within card
        "suburb":     "span[class*='suburb']",                           # Suburb within card
        "bedrooms":   "span[class*='bedroom']",                          # Bedrooms within card
    },

    # ── price filter panel ────────────────────────────────────────
    "price_filter": {
        "price_filter_dropdown":  "button.tm-drop-down-tag__dropdown-button:has-text('Price')",  # Price filter dropdown button
        "min_input":    "select[name='min_option']",                        # Minimum price select dropdown
        "max_input":    "select[name='max_option']",                        # Maximum price select dropdown
        "apply_button": "button.tm-drop-down-tag__dropdown-footer-button:has-text('View')" # Apply/View results button
    },

    # ── suburb filter panel ───────────────────────────────────────
    "suburb_filter": {
        "open_button":  "//button[@aria-label='Location']",              # Location/Suburb filter toggle
        "input":        "//input[@placeholder='Suburb']",                 # Suburb input
        "apply_button": "//button[contains(normalize-space(),'View')]",   # Apply/View results button
    },

    # ── bedrooms filter panel ─────────────────────────────────────
    "bedrooms_filter": {
        "open_button":  "//button[@aria-label='Bedrooms']",              # Bedrooms filter toggle
        "select":       "//select[@aria-label='Bedrooms']",               # Bedrooms select
        "apply_button": "//button[contains(normalize-space(),'View')]",   # Apply/View results button
    },

    # ── pagination ────────────────────────────────────────────────
    "pagination": {
        "container":   "//nav[@aria-label='Pagination']",                # Pagination nav
        "next_button": "//a[@aria-label='Next page']",                    # Next page link
    },

    # ── page state ────────────────────────────────────────────────
    "state": {
        "no_results":      "//p[contains(normalize-space(),'no results')]",  # No results message
        "loading_spinner": "//*[@role='progressbar']",                       # Loading indicator
    },
}
