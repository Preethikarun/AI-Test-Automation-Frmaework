# BDD_SKILL.md
# Read this completely before generating any .feature file or step definitions.

## What BDD is and why this framework uses it

BDD (Behaviour Driven Development) is a way of writing tests that
everyone can read — developers, testers, product managers, and
business stakeholders. Gherkin is the language. behave is the
Python runner.

In this framework BDD serves two purposes:
1. **Living documentation** — the `.feature` files describe exactly
   what the app does, readable by non-engineers
2. **Executable tests** — behave runs the `.feature` files against
   the real app via the step definitions in `steps/`

Agent 2 (bdd_generator_agent.py) generates both files from the
plain-English test cases produced by Agent 1.

---

## Two-file rule — always both together

Every BDD feature requires EXACTLY TWO files:

```
features/{page_name}.feature    ← Gherkin scenarios
steps/{page_name}_steps.py      ← Python behave implementations
```

Agent 2 generates both and presents them together in one approval
gate. Approve both or reject both — they are always a pair.

---

## File 1 — Feature file pattern

### Location
```
features/{page_name}.feature
```

### Template — complete feature file
```gherkin
Feature: {Feature name — noun describing the capability}
  As a {type of user}
  I want to {goal they are trying to achieve}
  So that {the benefit or outcome they get}

  Background:
    Given the {page name} is open

  @smoke @ui
  Scenario: {Concrete outcome — what the user achieves}
    Given {starting state — what is already true}
    When I {single user action — one action only}
    Then {observable result — what the user sees}

  @regression @ui
  Scenario: {Another concrete outcome}
    Given {starting state}
    And {additional precondition}
    When I {action}
    Then {result}
    And {additional result}
```

### Feature file rules — non-negotiable

**Rule 1 — Scenario names describe OUTCOMES not actions:**
```gherkin
# WRONG — describes an action
Scenario: Add three items to the list

# CORRECT — describes the outcome
Scenario: User sees three items after adding them sequentially
```

**Rule 2 — One When per scenario:**
```gherkin
# WRONG — two actions in one scenario
Scenario: Complete and delete an item
  When I complete item 1
  And I delete item 1   ← second action belongs in its own scenario

# CORRECT — one action per scenario
Scenario: Completing an item removes it from the active count
  When I complete todo item 1
  Then the todo count shows 0
```

**Rule 3 — Given sets state, never performs an action:**
```gherkin
# WRONG — Given performing an action
Given I click the login button

# CORRECT — Given describing state
Given the user is logged in
Given the todo list has 3 items
```

**Rule 4 — Use concrete values, not vague descriptions:**
```gherkin
# WRONG — vague
When I add some items
Then the count increases

# CORRECT — concrete and verifiable
When I add a todo item "Buy milk"
Then the todo count shows 1
```

**Rule 5 — Tags on every scenario — always two:**
```gherkin
@smoke @ui          ← category + type
@regression @ui
@regression @api
@flaky @ui          ← quarantined tests
```

### Background — use for repeated Given steps
If every scenario in the feature starts with the same Given step,
move it to Background:

```gherkin
Feature: Todo application

  Background:
    Given the todo app is open    ← runs before every scenario

  @smoke @ui
  Scenario: Add a single item
    When I add a todo item "Buy milk"
    Then the todo count shows 1
    # No need to repeat "Given the todo app is open" here
```

---

## File 2 — Step definitions pattern

### Location
```
steps/{page_name}_steps.py
```

### Template — complete step definitions file
```python
"""
Step definitions for {feature name} scenarios.
These implement the Gherkin steps in features/{page_name}.feature.

Each function matches one Gherkin step — exact text match.
String parameters use "{value}" — int parameters use {count:d}.
"""
from behave import given, when, then
from pages.{page_name}_page import {PageName}Page


# ── helper ───────────────────────────────────────────────────
def get_{page_name}(context) -> {PageName}Page:
    """
    Get or create the page object on context.
    Behave passes `context` between steps — we store the page
    object on it so every step in a scenario shares one instance.
    """
    if not hasattr(context, "{page_name}"):
        context.{page_name} = {PageName}Page(context.page)
    return context.{page_name}


# ── given steps ──────────────────────────────────────────────
@given("the {page_name} is open")
def step_open_page(context):
    """Navigate to the page."""
    get_{page_name}(context).navigate()


@given("{page_name} has {count:d} items")
def step_precondition_items(context, count: int):
    """Add a number of items as a precondition."""
    page = get_{page_name}(context)
    page.navigate()
    for i in range(count):
        page.add_item(f"Precondition item {i + 1}")


# ── when steps ───────────────────────────────────────────────
@when('I add a {page_name} item "{text}"')
def step_add_item(context, text: str):
    """Add a single item with the given text."""
    get_{page_name}(context).add_item(text)


@when("I complete {page_name} item {index:d}")
def step_complete_item(context, index: int):
    """Complete the item at position index (1-based in Gherkin)."""
    get_{page_name}(context).complete_item(index - 1)  # 0-based internally


@when("I delete {page_name} item {index:d}")
def step_delete_item(context, index: int):
    """Delete the item at position index (1-based in Gherkin)."""
    get_{page_name}(context).delete_item(index - 1)


# ── then steps ───────────────────────────────────────────────
@then("the {page_name} count shows {count:d}")
def step_check_count(context, count: int):
    """Verify the active item counter shows the expected number."""
    actual = get_{page_name}(context).get_item_count()
    assert actual == count, (
        f"Expected counter to show {count} but got {actual}"
    )


@then('the item "{text}" is visible')
def step_item_visible(context, text: str):
    """Verify an item with matching text is visible."""
    assert get_{page_name}(context).is_item_visible(text), (
        f"Expected item '{text}' to be visible but it was not found"
    )


@then('the item "{text}" is not visible')
def step_item_not_visible(context, text: str):
    """Verify an item with matching text is NOT visible."""
    assert not get_{page_name}(context).is_item_visible(text), (
        f"Expected item '{text}' to be hidden but it was still visible"
    )
```

### Step definition rules

**Rule 1 — Exact text match between Gherkin and decorator:**
```python
# Gherkin:  When I add a todo item "Buy milk"
@when('I add a todo item "{text}"')    ← must match exactly
def step_add_item(context, text: str):
```

**Rule 2 — String parameters use quotes in Gherkin:**
```gherkin
When I add a todo item "Buy milk"     ← quotes capture the string
```
```python
@when('I add a todo item "{text}"')   ← {text} extracts it
def step_add_item(context, text: str):
```

**Rule 3 — Integer parameters use :d in decorator:**
```gherkin
Then the todo count shows 3           ← no quotes — integer
```
```python
@then("the todo count shows {count:d}")   ← :d extracts integer
def step_check_count(context, count: int):
```

**Rule 4 — Use the helper function, not direct page creation:**
```python
# WRONG — creates a new page object, loses state from previous steps
@when('I add a todo item "{text}"')
def step_add_item(context, text):
    TodoPage(context.page).add_item(text)   ← new instance, loses state

# CORRECT — shares the same instance across all steps in the scenario
@when('I add a todo item "{text}"')
def step_add_item(context, text):
    get_todo(context).add_item(text)        ← same instance
```

**Rule 5 — Assertion messages must explain the failure:**
```python
# WRONG — pytest message is useless
assert actual == 3

# CORRECT — message explains what went wrong
assert actual == 3, (
    f"Expected counter to show 3 active items but got {actual}. "
    f"Check that completed items are being excluded from the count."
)
```

**Rule 6 — Index convention — Gherkin is 1-based, Python is 0-based:**
```gherkin
When I complete todo item 1    ← humans count from 1
```
```python
@when("I complete todo item {index:d}")
def step_complete(context, index: int):
    get_todo(context).complete_item(index - 1)   ← subtract 1 for Python
```

---

## Real example — todo.feature + todo_steps.py

### features/todo.feature
```gherkin
Feature: Todo application
  As a user
  I want to manage my daily tasks
  So that I can stay organised

  Background:
    Given the todo app is open

  @smoke @ui
  Scenario: User sees one item after adding it
    When I add a todo item "Build AI test framework"
    Then the todo count shows 1
    And the item "Build AI test framework" is visible

  @regression @ui
  Scenario: User sees three items after adding them sequentially
    When I add a todo item "Day 1 foundation"
    And I add a todo item "Day 2 AI agents"
    And I add a todo item "Day 3 CI/CD"
    Then the todo count shows 3

  @regression @ui
  Scenario: Completing an item removes it from the active count
    And I add a todo item "Complete me"
    When I complete todo item 1
    Then the todo count shows 0

  @regression @ui
  Scenario: Deleting item one of two leaves only the second item
    And I add a todo item "Delete me"
    And I add a todo item "Keep me"
    When I delete todo item 1
    Then the item "Delete me" is not visible
    And the item "Keep me" is visible
```

### steps/todo_steps.py
```python
from behave import given, when, then
from pages.todo_page import TodoPage


def get_todo(context) -> TodoPage:
    if not hasattr(context, "todo"):
        context.todo = TodoPage(context.page)
    return context.todo


@given("the todo app is open")
def step_open(context):
    get_todo(context).navigate()


@when('I add a todo item "{text}"')
def step_add(context, text: str):
    get_todo(context).add_item(text)


@when("I complete todo item {index:d}")
def step_complete(context, index: int):
    get_todo(context).complete_item(index - 1)


@when("I delete todo item {index:d}")
def step_delete(context, index: int):
    get_todo(context).delete_item(index - 1)


@then("the todo count shows {count:d}")
def step_count(context, count: int):
    actual = get_todo(context).get_item_count()
    assert actual == count, (
        f"Expected {count} active items but got {actual}"
    )


@then('the item "{text}" is visible')
def step_visible(context, text: str):
    assert get_todo(context).is_item_visible(text), (
        f"Item '{text}' not visible"
    )


@then('the item "{text}" is not visible')
def step_not_visible(context, text: str):
    assert not get_todo(context).is_item_visible(text), (
        f"Item '{text}' should not be visible"
    )
```

---

## Running BDD tests with behave

```bash
# run all feature files
behave features/

# run one feature file
behave features/todo.feature

# run scenarios tagged smoke
behave features/ --tags=smoke

# run scenarios tagged regression but not flaky
behave features/ --tags=regression --tags=~flaky

# run with verbose output
behave features/ --no-capture -v
```

---

## Checklist before submitting any BDD pair

### Feature file
- [ ] Feature has a user story: As a / I want / So that
- [ ] Background used for repeated Given steps
- [ ] Every scenario name describes an OUTCOME not an action
- [ ] Maximum one When per scenario
- [ ] Given only describes state — no actions in Given
- [ ] Concrete values used — no vague descriptions
- [ ] Every scenario has exactly two tags: category + type
- [ ] Integer parameters have no quotes in Gherkin
- [ ] String parameters have quotes in Gherkin

### Step definitions
- [ ] Helper function `get_{page}(context)` defined at the top
- [ ] Every step uses the helper — no direct `Page(context.page)`
- [ ] String parameters use `"{text}"` in decorator
- [ ] Integer parameters use `{count:d}` in decorator
- [ ] Gherkin 1-based index converted to 0-based in Python
- [ ] Every assertion has a meaningful failure message
- [ ] Docstring on every step function
- [ ] `__init__.py` exists in steps/
- [ ] Step text matches Gherkin exactly — case sensitive
