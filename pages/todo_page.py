"""
Page object model for the TodoMVC app.
"""
from playwright.sync_api import Page
from locators.todo_locators import TODO_LOCATORS


class TodoPage:
    """Encapsulates actions and queries for the TodoMVC page."""

    URL = "https://demo.playwright.dev/todomvc"

    def __init__(self, page: Page):
        self.page = page

    # ── navigation ──────────────────────────────
    def navigate(self) -> None:
        self.page.goto(self.URL)
        self.page.wait_for_load_state("networkidle")

    # ── actions ─────────────────────────────────
    def add_item(self, text: str) -> None:
        self.page.fill(TODO_LOCATORS["new_input"], text)
        self.page.keyboard.press("Enter")

    def complete_item(self, index: int = 0) -> None:
        checkboxes = self.page.locator(TODO_LOCATORS["item_checkbox"])
        checkboxes.nth(index).click()

    def delete_item(self, index: int = 0) -> None:
        item = self.page.locator(TODO_LOCATORS["todo_items"]).nth(index)
        item.hover()
        item.locator("button.destroy").click()

    def clear_completed(self) -> None:
        self.page.click(TODO_LOCATORS["clear_completed"])

    # ── queries ─────────────────────────────────
    def get_item_count(self) -> int:
        count_text = self.page.locator(TODO_LOCATORS["todo_count"]).text_content()
        return int(count_text.strip())

    def get_all_items(self) -> list[str]:
        return self.page.locator(TODO_LOCATORS["item_label"]).all_text_contents()

    def is_item_visible(self, text: str) -> bool:
        return self.page.locator(TODO_LOCATORS["todo_items"], has_text=text).is_visible()