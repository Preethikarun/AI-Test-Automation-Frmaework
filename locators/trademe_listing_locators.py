"""
locators/trademe_listing_locators.py

Locator skeleton for Trade Me — listing detail screen.
Fill each empty string from DevTools inspection.

XPath selector priority:
  1. data-testid       //*[@data-testid='listing-price']
  2. aria-label        //h1[@aria-label='Listing title']
  3. stable text       //button[normalize-space()='Enquire']
  4. role + label      //*[@role='heading'][@aria-level='1']
  5. structural XPath  //section[@data-testid='agent-info']//a
— Never use class names (sc-abc123, css-xyz, etc.)
"""

TRADEME_LISTING_LOCATORS = {

    # ── page load markers ─────────────────────────────────────────
    "page": {
        "loaded":    "//h1[@data-testid='listing-title']",                # Page title indicates page load
        "container": "//main[@role='main']",                             # Main content area
    },

    # ── core listing details ──────────────────────────────────────
    "details": {
        "title":       "//h1[@data-testid='listing-title']",             # Listing title
        "price":       "//*[@data-testid='listing-price']",              # Property price
        "address":     "//*[@data-testid='listing-address']",            # Full address
        "bedrooms":    "//*[@data-testid='bedrooms']",                   # Bedrooms count
        "bathrooms":   "//*[@data-testid='bathrooms']",                  # Bathrooms count
        "description": "//section[@aria-label='Description']",           # Property description
    },

    # ── agent / agency ────────────────────────────────────────────
    "agent": {
        "name":    "//section[@data-testid='agent-info']//h2",           # Agent name
        "contact": "//a[starts-with(@href,'tel:')]",                     # Phone number link
        "logo":    "//section[@data-testid='agent-info']//img[@alt]",    # Agency logo
    },

    # ── photo gallery ─────────────────────────────────────────────
    "media": {
        "photo_gallery": "//*[@aria-label='Property photos']",           # Photo gallery container
        "first_photo":   "(//*[@aria-label='Property photos']//img)[1]", # First photo
    },

    # ── call-to-action buttons ────────────────────────────────────
    "actions": {
        "enquire_button": "//button[normalize-space()='Enquire']",       # Enquire button
        "save_button":    "//button[@aria-label='Save listing']",        # Save/Favourite button
    },
}
