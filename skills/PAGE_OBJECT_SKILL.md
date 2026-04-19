# PAGE_OBJECT_SKILL.md
# Read this completely before generating any locator file or page class.

## What is the Page Object Model and why we use it

The Page Object Model (POM) is a design pattern where every page of
the application has its own Python class. The class holds all the
actions a user can perform on that page. This means:

- When a selector breaks, you fix it in ONE place — not across 50 tests
- Tests read like plain English — `login_page.enter_password("secret")`
- Adding a new test takes minutes, not hours
- Agent 3 (self-heal) knows exactly which file to patch

## The two-file rule — always both, never one

Every page in the application requires EXACTLY TWO files:

```
locators/{page_name}_locators.py   ← CSS selectors dictionary
pages/{page_name}_page.py          ← Page Object class
```

If you create one, you must create the other. They are always a pair.

---

## File 1 — Locators file pattern

### Location
```
locators/{page_name}_locators.py
```

### Naming convention
- File name: `{page_name}_locators.py` — lowercase with underscores
- Dict name: `{PAGE_NAME}_LOCATORS` — UPPER_SNAKE_CASE
- Key names: `"snake_case_key"` — lowercase strings
- One dict per file — one page per file

### Template — nested sections dict (REQUIRED format)
Locators use a two-level nested dict.  Top-level keys are logical UI
sections (search, filters, results, state).  Inner keys are element names.
All values are empty strings — the tester fills them from DevTools.

```python
"""
locators/{page_name}_locators.py

XPath selector priority:
  data-testid > aria-label > placeholder > name > stable text > structural XPath
Never use CSS class selectors or auto-generated class names.
"""

{PAGE_NAME}_LOCATORS = {

    # ── search / form ─────────────────────────────────────────
    "search": {
        "input":  "",   # //input[@aria-label='Search'] or //input[@placeholder='...']
        "button": "",   # //button[normalize-space()='Search'] or //button[@aria-label='Search']
    },

    # ── filters ───────────────────────────────────────────────
    "filters": {
        "min_price":    "",   # //input[@aria-label='Minimum price'] or //input[@name='price_min']
        "apply_button": "",   # //button[normalize-space()='Apply'] or //*[@data-testid='apply']
    },

    # ── results ───────────────────────────────────────────────
    "results": {
        "container": "",   # //section[@data-testid='results'] or //*[@role='list']
        "cards":     "",   # //*[@data-testid='listing-card']
    },

    # ── page state ────────────────────────────────────────────
    "state": {
        "loading_spinner": "",   # //*[@role='progressbar'] or //*[@aria-label='Loading']
        "no_results":      "",   # //*[@data-testid='no-results']
    },
}
```

### Selector priority — XPath only, in this order
This project uses XPath exclusively. CSS class selectors are banned
because auto-generated class names (sc-abc123, css-xyz) break silently.

1. `data-testid`      `//input[@data-testid='search-input']`        most stable
2. `aria-label`       `//input[@aria-label='Search properties']`
3. `placeholder`      `//input[@placeholder='Search Trade Me']`
4. `name` attribute   `//input[@name='search_string']`
5. stable text        `//button[normalize-space()='Search']`
6. role + label       `//*[@role='button'][@aria-label='Apply']`
7. structural XPath   `//section[@data-testid='results']//li`       last resort

NEVER use:
- CSS class selectors  `.new-todo`, `input.something`
- Auto-generated names `sc-abc123`, `css-xyz`
- Positional CSS       `div:nth-child(3)`

### Alignment rule
Align selector values with spaces so all values start at the same
column. This makes diffs readable and the file scannable at a glance:

```python
# CORRECT — aligned
TODO_LOCATORS = {
    "new_input":       "input.new-todo",
    "todo_items":      ".todo-list li",
    "todo_count":      ".todo-count strong",
    "clear_completed": "button.clear-completed",
}

# WRONG — not aligned
TODO_LOCATORS = {
    "new_input": "input.new-todo",
    "todo_items": ".todo-list li",
    "todo_count": ".todo-count strong",
}
```

### What NEVER goes in a locators file
- No imports (except TYPE_CHECKING)
- No functions or classes
- No logic — pure data only
- No URLs — URLs live in the page class as URL constant

---

## File 2 — Page class pattern

### Location
```
pages/{page_name}_page.py
```

### Naming convention
- File name: `{page_name}_page.py` — lowercase with underscores
- Class name: `{PageName}Page` — PascalCase + Page suffix
- Example: `todo_page.py` → `TodoPage`

### Template — complete page class

CRITICAL RULES for page classes in this framework:
- NEVER call `page.locator()`, `page.fill()`, `page.click()` directly
- ALWAYS use the `Actions` and `Functions` wrappers from utils/
- Locator access is ALWAYS two-level: `self.loc["section"]["key"]`
- Use `domcontentloaded` (not `networkidle`) — networkidle times out on ad-heavy sites
- Every public method must have `@allure.step`

```python
"""
pages/{page_name}_page.py

PageObject for the {AppName} {ScreenName} screen.
Access locators as: self.loc["section"]["key"]
Never call page.locator() directly — always go through Actions or Functions.
"""
import allure
from playwright.sync_api import Page
from locators.{page_name}_locators import {PAGE_NAME}_LOCATORS
from utils.actions import Actions
from utils.functions import Functions


class {PageName}Page:
    """PageObject for {PageName}. One instance per scenario."""

    URL = "https://example.com/{path}"

    def __init__(self, page: Page):
        self.page      = page
        self.actions   = Actions(page)
        self.functions = Functions(page)
        self.loc       = {PAGE_NAME}_LOCATORS

    # ── navigation ───────────────────────────────────────────
    @allure.step("Navigate to {PageName}")
    def navigate(self) -> None:
        """Navigate and wait for the primary element to be interactive."""
        self.page.goto(self.URL)
        self.actions.wait_for_page_load()          # uses domcontentloaded
        self.actions.wait_for_visible(self.loc["search"]["input"])

    # ── actions ──────────────────────────────────────────────
    @allure.step("Enter search term: '{term}'")
    def search_for(self, term: str) -> None:
        """Fill the search box and submit."""
        self.actions.wait_for_visible(self.loc["search"]["input"])
        self.actions.fill(self.loc["search"]["input"], term)
        self.actions.click(self.loc["search"]["button"])
        self.actions.wait_for_page_load()

    # ── queries ──────────────────────────────────────────────
    @allure.step("Check results are visible")
    def results_visible(self) -> bool:
        """Return True if the results container is visible."""
        return self.actions.is_visible(self.loc["results"]["container"])
```

### Method naming conventions
Always use these prefixes so tests read like plain English:

| Prefix | Returns | Example |
|--------|---------|---------|
| `navigate()` | None | `page.navigate()` |
| `add_`, `create_`, `submit_` | None | `page.add_item("text")` |
| `click_`, `select_`, `toggle_` | None | `page.click_button()` |
| `fill_`, `enter_`, `type_` | None | `page.fill_search("query")` |
| `get_` | str, int, list | `page.get_item_count()` |
| `is_`, `has_`, `can_` | bool | `page.is_item_visible("text")` |
| `wait_for_` | None | `page.wait_for_element("dialog")` |

### Three sections — always in this order
```python
# ── navigation ───   navigate() always first
# ── actions ─────   verbs that change state
# ── queries ─────   getters that read state
```

### What NEVER goes in a page class
- No assertions — assertions belong in test classes
- No raw CSS strings — always use LOCATORS["key"]
- No test data — test data belongs in fixtures/
- No business logic — page objects are UI wrappers only
- No print() statements — use Playwright's built-in tracing

---

## Real example — TodoPage (reference implementation)

This is the complete working example already in the project.
Use this as the reference when generating new page objects.

```python
# locators/todo_locators.py
TODO_LOCATORS = {
    "new_input":       "input.new-todo",
    "todo_items":      ".todo-list li",
    "item_label":      ".todo-list li label",
    "item_checkbox":   ".todo-list li .toggle",
    "todo_count":      ".todo-count strong",
    "clear_completed": "button.clear-completed",
    "toggle_all":      "label[for='toggle-all']",
    "filter_all":      "a[href='#/']",
    "filter_active":   "a[href='#/active']",
    "filter_completed":"a[href='#/completed']",
}
```

```python
# pages/todo_page.py
from playwright.sync_api import Page, expect
from locators.todo_locators import TODO_LOCATORS

class TodoPage:
    URL = "https://demo.playwright.dev/todomvc"

    def __init__(self, page: Page):
        self.page = page

    # ── navigation ───────────────────────────────────────────
    def navigate(self):
        self.page.goto(self.URL)
        self.page.wait_for_load_state("networkidle")

    # ── actions ──────────────────────────────────────────────
    def add_item(self, text: str):
        self.page.fill(TODO_LOCATORS["new_input"], text)
        self.page.keyboard.press("Enter")

    def complete_item(self, index: int = 0):
        self.page.locator(TODO_LOCATORS["item_checkbox"]).nth(index).click()

    def delete_item(self, index: int = 0):
        item = self.page.locator(TODO_LOCATORS["todo_items"]).nth(index)
        item.hover()
        item.locator("button.destroy").click()

    # ── queries ──────────────────────────────────────────────
    def get_item_count(self) -> int:
        text = self.page.locator(TODO_LOCATORS["todo_count"]).text_content()
        return int(text.strip())

    def get_all_items(self) -> list[str]:
        return self.page.locator(TODO_LOCATORS["item_label"]).all_text_contents()

    def is_item_visible(self, text: str) -> bool:
        return self.page.locator(
            TODO_LOCATORS["todo_items"], has_text=text
        ).is_visible()
```

---

## Checklist before submitting any POM

- [ ] Two files created: locators file AND page class
- [ ] Dict name is UPPER_SNAKE_CASE
- [ ] All selectors aligned with spaces
- [ ] Class name is PascalCase ending in Page
- [ ] URL is a class constant, not in locators
- [ ] Methods in three sections: navigation / actions / queries
- [ ] All methods have type hints and docstrings
- [ ] No assertions in page class
- [ ] No raw selectors in page class
- [ ] `__init__.py` exists in locators/ and pages/
