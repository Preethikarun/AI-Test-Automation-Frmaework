"""
This is a class. __init__ runs once when you create it. 
It saves# Solution for Failing Job

The job failed due to **PEP 8 style violations** detected by a linting tool (likely flake8). Here are the issues and fixes:

## Issues Found

1. **`pages/todo_page.py:51:1` - W293**: Blank line contains whitespace
2. **`pages/todo_page.py:56:23` - W292**: No newline at end of file
3. **`tests/test_todo.py:9:1` - E302**: Expected 2 blank lines, found 1
4. **`tests/test_todo.py:45:1` - W293**: Blank line contains whitespace

## Fixes

### 1. Fix `pages/todo_page.py`

Remove the trailing whitespace on line 51  the page object as self.page so every method can use it. 
def defines each method. 
self.page.fill() is calling Playwright's fill method. 
: str and : int are type hints — they tell you what type the argument should be.
"""
from playwright.sync_api import Page, expect
from locators.todo_locators import TODO_LOCATORS


class TodoPage:
    URL = "https://demo.playwright.dev/todomvc"

    def __init__(self, page: Page):
        self.page = page

# ── navigation ──────────────────────────────
    def navigate(self):
        self.page.goto(self.URL)
        self.page.wait_for_load_state("networkidle")

# ── actions ─────────────────────────────────
    def add_item(self, text: str):
        self.page.fill(TODO_LOCATORS["new_input"], text)
        self.page.keyboard.press("Enter")

    def complete_item(self, index: int = 0):
        checkboxes = self.page.locator(TODOand add a newline at the end of the file:

```python
"""
This is a class. __init__ runs once when you create it. 
It saves the page object as self.page so every method can use it. 
def defines each method. 
self.page.fill() is calling Playwright's fill method. 
: str and : int are type hints — they tell you what type the argument should be.
"""
from playwright.sync_api import Page, expect
from locators.todo_locators import TODO_LOCATORS


class TodoPage:
    URL = "https://demo.playwright.dev/todomvc"

    def __init__(self, page: Page):
        self.page = page

# ── navigation ──────────────────────────────
    def navigate(self):
        self.page.goto(self.URL)
        self.page.wait_for_load_state("networkidle")

# ── actions ─────────────────────────────────
    def add_item(self_LOCATORS["item_checkbox"])
        checkboxes.nth(index).click()

    def delete_item(self, index: int = 0):
        item = self.page.locator(TODO_LOCATORS["todo_items"]).nth(index)
        item.hover()
        item.locator("button.destroy").click()

    def clear_completed(self):
        self.page.click(TODO_LOCATORS["clear_completed"])

# ── queries ─────────────────────────────────
    def get_item_count(self) -> int:
        count_text = self.page.locator(
            TODO_LOCATORS["todo_count"]
        ).text_content()
        return int(count_text.strip())

    def get_all_items(self) -> list:
        return self.page.locator(
            TODO_LOCATORS["item_label"]
        ).all_text_contents()

    def is_item_visible(self, text: str) -> bool:
        return self.page.locator(
            TODO_LOCATORS["todo_items"],
            has_text=text
        ).is_visible()
        
