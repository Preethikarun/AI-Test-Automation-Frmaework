"""
Functions starting with test_ are automatically discovered by pytest.
The page argument is injected by conftest.py — you don't call it yourself.
assert is how you check an expected result — if it's False, the test fails.
"""
from pages.todo_page import TodoPage
# import pytest


class TestTodoApp:
    """Test suite for the Playwright demo Todo app."""

    def test_add_single_item(self, page):
        """Mode 4 example: simple test case addition."""
        todo = TodoPage(page)
        todo.navigate()
        todo.add_item("Build AI test framework")
        assert todo.get_item_count() == 1
        assert todo.is_item_visible("Build AI test framework")

    def test_add_multiple_items(self, page):
        todo = TodoPage(page)
        todo.navigate()
        todo.add_item("Day 1 — foundation")
        todo.add_item("Day 2 — AI agents")
        todo.add_item("Day 3 — CI/CD")
        assert todo.get_item_count() == 3

    def test_complete_item(self, page):
        todo = TodoPage(page)
        todo.navigate()
        todo.add_item("Complete me")
        todo.complete_item(index=0)
        # count drops to 0 active items
        assert todo.get_item_count() == 0

    def test_delete_item(self, page):
        todo = TodoPage(page)
        todo.navigate()
        todo.add_item("Delete me")
        todo.add_item("Keep me")
        todo.delete_item(index=0)
        items = todo.get_all_items()
        assert "Delete me" not in items
        assert "Keep me" in items
