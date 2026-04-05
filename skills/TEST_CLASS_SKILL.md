# TEST_CLASS_SKILL.md
# Read this completely before generating any pytest test class.

## What a test class is and why it is structured this way

A test class groups related tests for one feature or page.
Every test in the class is completely independent — it sets up
its own state, does one thing, and asserts the result.

In this framework test classes are in `tests/` and they:
- Import the Page Object — never touch Playwright directly
- Are tagged with markers so CI can run subsets
- Follow Arrange → Act → Assert every single time
- Write to `reports/failures.json` on failure via conftest.py

---

## File location and naming

```
tests/test_{feature_name}.py
```

| Thing | Convention | Example |
|-------|-----------|---------|
| File name | `test_{feature}.py` | `test_todo.py` |
| Class name | `Test{Feature}` | `TestTodoApp` |
| Method name | `test_{what_it_proves}` | `test_add_single_item` |

---

## Template — complete test class

```python
"""
Tests for {Feature} — {one line description of what is tested}.

Covers:
- {happy path scenario}
- {edge case scenario}
- {negative scenario}

Run all:   pytest tests/test_{feature}.py -v
Run smoke: pytest tests/test_{feature}.py -v -m smoke
"""
import pytest
from pages.{page_name}_page import {PageName}Page


class Test{Feature}:
    """Test suite for {feature description}."""

    # ── smoke tests ──────────────────────────────────────────
    @pytest.mark.smoke
    @pytest.mark.ui
    def test_{happy_path}(self, page):
        """{One sentence: what does this test prove?}"""
        # Arrange
        {page_obj} = {PageName}Page(page)
        {page_obj}.navigate()

        # Act
        {page_obj}.{action}({input})

        # Assert
        assert {page_obj}.{query}() == {expected}

    # ── regression tests ─────────────────────────────────────
    @pytest.mark.regression
    @pytest.mark.ui
    def test_{edge_case}(self, page):
        """{One sentence: what does this test prove?}"""
        # Arrange
        {page_obj} = {PageName}Page(page)
        {page_obj}.navigate()

        # Act
        {page_obj}.{action}()

        # Assert
        assert {page_obj}.{query}()
```

---

## Markers — tag every test with exactly two marks

Every test gets exactly TWO `@pytest.mark` decorators:
1. **Test category** — how critical is this test?
2. **Test type** — what does it test?

### Category markers
| Marker | When to use |
|--------|------------|
| `@pytest.mark.smoke` | Must pass on every push · critical path only |
| `@pytest.mark.regression` | Full suite · runs nightly or on release |
| `@pytest.mark.flaky` | Known unstable · quarantined · runs separately |

### Type markers
| Marker | When to use |
|--------|------------|
| `@pytest.mark.ui` | Playwright browser tests |
| `@pytest.mark.api` | REST/SOAP/GraphQL tests |

### Example — correct marker usage
```python
@pytest.mark.smoke      # category
@pytest.mark.ui         # type
def test_login_happy_path(self, page):
    ...

@pytest.mark.regression # category
@pytest.mark.ui         # type
def test_login_wrong_password(self, page):
    ...

@pytest.mark.flaky      # category — quarantined
@pytest.mark.ui         # type
def test_animation_timing(self, page):
    ...
```

---

## Arrange → Act → Assert — always this order

Every test follows this three-part structure with blank lines between:

```python
def test_add_item_updates_counter(self, page):
    """Adding one item makes the counter show 1."""
    # Arrange — set up the starting state
    todo = TodoPage(page)
    todo.navigate()

    # Act — do the one thing being tested
    todo.add_item("Buy milk")

    # Assert — check the one expected outcome
    assert todo.get_item_count() == 1
```

### Rules for each section
**Arrange:**
- Create the page object
- Navigate to the page
- Set up any preconditions (add items, log in, etc.)
- Never put assertions here

**Act:**
- One action only — the thing being tested
- If you need two actions, write two tests
- Never put assertions here

**Assert:**
- One assertion per test where possible
- Use the page object's query methods — never raw Playwright
- Include a meaningful failure message:
  `assert count == 3, f"Expected 3 items but got {count}"`

---

## Test independence — the golden rule

Every test must work whether run alone or as part of the full suite.
This means:

```python
# WRONG — depends on another test having run first
def test_complete_item(self, page):
    todo = TodoPage(page)
    # BUG: assumes test_add_item ran first and left an item
    todo.complete_item(0)
    assert todo.get_item_count() == 0

# CORRECT — sets up its own state
def test_complete_item(self, page):
    todo = TodoPage(page)
    todo.navigate()
    todo.add_item("Complete me")   # arrange its own precondition
    todo.complete_item(0)
    assert todo.get_item_count() == 0
```

---

## Docstrings — required on every test

Every test method needs a one-sentence docstring that explains
what the test PROVES, not what it does:

```python
# WRONG — describes actions
def test_add_item(self, page):
    """Navigate to app, type text, press enter, check count."""

# CORRECT — states the proof
def test_add_item(self, page):
    """Adding one item increments the active item counter to 1."""
```

---

## Parameterised tests — for data-driven scenarios

When the same test logic applies to multiple inputs:

```python
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.parametrize("item_text,expected_count", [
    ("Single item",   1),
    ("Another item",  1),
])
def test_add_item_with_various_text(
    self, page, item_text, expected_count
):
    """Adding any text item creates exactly one active item."""
    todo = TodoPage(page)
    todo.navigate()
    todo.add_item(item_text)
    assert todo.get_item_count() == expected_count
```

---

## Bug fix tests — TDD pattern (critical)

When a bug is reported, the test comes FIRST:

```python
# Step 1: write this test BEFORE the fix
# It must FAIL on first run — that proves the bug exists
@pytest.mark.regression
@pytest.mark.ui
def test_bug_clear_completed_not_visible_when_no_completed_items(
    self, page
):
    """
    BUG FIX TEST: clear-completed button must be hidden
    when there are no completed items.
    GitHub issue #42 — reported 2025-04-01.
    """
    todo = TodoPage(page)
    todo.navigate()
    todo.add_item("Active item")
    # no items completed — button should not be visible
    assert not todo.is_clear_completed_visible(), (
        "Clear completed button should be hidden when "
        "no items are completed"
    )

# Step 2: run it — confirm FAIL
# Step 3: fix the bug
# Step 4: run it again — confirm PASS
# Step 5: commit both the fix and this test together
```

---

## Real example — TestTodoApp (reference implementation)

```python
import pytest
from pages.todo_page import TodoPage


class TestTodoApp:
    """Test suite for the Playwright demo Todo app."""

    @pytest.mark.smoke
    @pytest.mark.ui
    def test_add_single_item(self, page):
        """Adding one item makes the counter show 1."""
        todo = TodoPage(page)
        todo.navigate()
        todo.add_item("Build AI test framework")
        assert todo.get_item_count() == 1
        assert todo.is_item_visible("Build AI test framework")

    @pytest.mark.regression
    @pytest.mark.ui
    def test_add_multiple_items(self, page):
        """Adding three items makes the counter show 3."""
        todo = TodoPage(page)
        todo.navigate()
        todo.add_item("Day 1 foundation")
        todo.add_item("Day 2 AI agents")
        todo.add_item("Day 3 CI/CD")
        assert todo.get_item_count() == 3

    @pytest.mark.regression
    @pytest.mark.ui
    def test_complete_item_decrements_counter(self, page):
        """Completing an item removes it from the active counter."""
        todo = TodoPage(page)
        todo.navigate()
        todo.add_item("Complete me")
        todo.complete_item(index=0)
        assert todo.get_item_count() == 0

    @pytest.mark.regression
    @pytest.mark.ui
    def test_delete_item_removes_only_that_item(self, page):
        """Deleting item 1 of 2 leaves only item 2 visible."""
        todo = TodoPage(page)
        todo.navigate()
        todo.add_item("Delete me")
        todo.add_item("Keep me")
        todo.delete_item(index=0)
        items = todo.get_all_items()
        assert "Delete me" not in items
        assert "Keep me" in items
```

---

## Checklist before submitting any test class

- [ ] File name follows `test_{feature}.py` pattern
- [ ] Class name follows `Test{Feature}` pattern
- [ ] Every method name follows `test_{what_it_proves}` pattern
- [ ] Every method has a docstring — one sentence, states the proof
- [ ] Every method has exactly TWO markers (category + type)
- [ ] Every method follows Arrange → Act → Assert with blank lines
- [ ] No shared state between tests — each test sets up its own
- [ ] No raw Playwright calls — all via page object methods
- [ ] No assertions in Arrange or Act sections
- [ ] Bug fix tests are written BEFORE the fix and marked as such
- [ ] `__init__.py` exists in tests/
