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

### Template
```python
"""
Locators for the {PageName} page.
URL: https://example.com/{path}

All CSS selectors for this page live here.
Never put raw selectors in page classes or test files.
"""

{PAGE_NAME}_LOCATORS = {
    # ── primary actions ──────────────────────────────────────
    "key_name":          "css-selector",
    "another_key":       "css-selector",

    # ── form fields ──────────────────────────────────────────
    "input_field":       "input.class-name",
    "submit_button":     "button[type='submit']",

    # ── result elements ──────────────────────────────────────
    "result_list":       ".results li",
    "result_count":      ".count strong",

    # ── navigation ───────────────────────────────────────────
    "filter_all":        "a[href='#/']",
    "filter_active":     "a[href='#/active']",
}
```

### Selector priority — always prefer in this order
1. `data-testid` attribute — most stable, survives CSS refactors
   `"button": "[data-testid='submit-btn']"`
2. ARIA role + name — semantic, accessible
   `"dialog": "[role='dialog'][aria-label='Confirm']"`
3. Unique CSS class — reasonably stable
   `"input": "input.new-todo"`
4. CSS combination — when class alone is not unique
   `"item": ".todo-list li label"`
5. Text content — only for labels that never change
   `"heading": "h1:has-text('Welcome')"`
6. XPath — LAST RESORT only, explain why in a comment

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
```python
"""
Page Object for the {PageName} page.
URL: https://example.com/{path}

Wraps all user interactions on this page into clean methods.
Tests call these methods — never raw Playwright commands.

Usage:
    page_obj = {PageName}Page(page)
    page_obj.navigate()
    page_obj.{action}()
"""
from playwright.sync_api import Page, expect
from locators.{page_name}_locators import {PAGE_NAME}_LOCATORS


class {PageName}Page:
    """Page Object for {PageName}. One instance per test."""

    URL = "https://example.com/{path}"   # class constant — not in locators

    def __init__(self, page: Page):
        """Initialise with a Playwright Page instance."""
        self.page = page

    # ── navigation ───────────────────────────────────────────
    def navigate(self):
        """Navigate to this page and wait for it to fully load."""
        self.page.goto(self.URL)
        self.page.wait_for_load_state("networkidle")

    # ── actions ──────────────────────────────────────────────
    def add_item(self, text: str):
        """Type text into the input field and press Enter."""
        self.page.fill({PAGE_NAME}_LOCATORS["new_input"], text)
        self.page.keyboard.press("Enter")

    def click_button(self, button_key: str = "submit_button"):
        """Click a button identified by its locator key."""
        self.page.click({PAGE_NAME}_LOCATORS[button_key])

    def select_filter(self, filter_name: str):
        """Click a filter tab by name: all | active | completed."""
        key = f"filter_{filter_name}"
        self.page.click({PAGE_NAME}_LOCATORS[key])

    # ── queries ──────────────────────────────────────────────
    def get_item_count(self) -> int:
        """Return the number of active items shown in the counter."""
        text = self.page.locator(
            {PAGE_NAME}_LOCATORS["result_count"]
        ).text_content()
        return int(text.strip())

    def get_all_items(self) -> list[str]:
        """Return text content of all visible list items."""
        return self.page.locator(
            {PAGE_NAME}_LOCATORS["result_list"]
        ).all_text_contents()

    def is_item_visible(self, text: str) -> bool:
        """Return True if an item with matching text is visible."""
        return self.page.locator(
            {PAGE_NAME}_LOCATORS["result_list"],
            has_text=text
        ).is_visible()

    def wait_for_element(self, locator_key: str):
        """Wait for an element to appear — use before fragile actions."""
        self.page.locator(
            {PAGE_NAME}_LOCATORS[locator_key]
        ).wait_for(state="visible")
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
