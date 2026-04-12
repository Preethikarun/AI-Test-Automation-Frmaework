"""
Locators for the TodoMVC page.
URL: https://demo.playwright.dev/todomvc

Organised as nested dicts by UI section so related selectors are
grouped and access reads like: TODO_LOCATORS["form"]["new_input"].

Selector strategy (preferred order):
  1. Placeholder / user-facing attribute  →  //input[@placeholder='...']
  2. ARIA role + accessible name          →  role=textbox[name='...']
  3. Stable text content                  →  //button[normalize-space()='...']
  4. Structural XPath                     →  //ul[...]/li//input[...]
  (Never use auto-generated class names like sc-abc123)
"""

TODO_LOCATORS = {

    # ── form ─────────────────────────────────────────────────────────────────
    "form": {
        "new_input":    "//input[@placeholder='What needs to be done?']",
        "toggle_all":   "//label[@for='toggle-all']",
    },

    # ── list ─────────────────────────────────────────────────────────────────
    "list": {
        "items":        "//ul[contains(@class,'todo-list')]/li",
        "label":        "//ul[contains(@class,'todo-list')]/li//label",
        "checkbox":     "//ul[contains(@class,'todo-list')]/li//input[@class='toggle']",
        "destroy":      "//ul[contains(@class,'todo-list')]/li//button[@class='destroy']",
    },

    # ── footer ────────────────────────────────────────────────────────────────
    "footer": {
        "count":            "//span[@class='todo-count']/strong",
        "clear_completed":  "//button[normalize-space()='Clear completed']",
    },

    # ── filters ───────────────────────────────────────────────────────────────
    "filters": {
        "all":          "//ul[@class='filters']//a[@href='#/']",
        "active":       "//ul[@class='filters']//a[@href='#/active']",
        "completed":    "//ul[@class='filters']//a[@href='#/completed']",
    },
}
