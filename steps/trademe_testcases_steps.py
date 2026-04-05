```python
from behave import given, when, then
from pages.todo_page import TodoPage


def get_todo(context):
    if not hasattr(context, 'todo'):
        context.todo = TodoPage(context.driver)
    return context.todo


@given('the Trade Me Property page is open')
def step_open_trade_me_property_page(context):
    todo = get_todo(context)
    todo.open()
    assert todo.is_page_loaded(), "Trade Me Property page failed to load"


@when('I search for "{search_term}"')
def step_search_for_term(context, search_term):
    todo = get_todo(context)
    todo.search(search_term)
    assert todo.search_was_submitted(), (
        f"Search for '{search_term}' was not submitted successfully"
    )


@then('search results for "{search_term}" are displayed')
def step_search_results_displayed(context, search_term):
    todo = get_todo(context)
    results_visible = todo.are_search_results_displayed(search_term)
    assert results_visible, (
        f"Expected search results for '{search_term}' to be displayed, but none were found"
    )


@given('the search results page for "{search_term}" is displayed')
def step_search_results_page_displayed(context, search_term):
    todo = get_todo(context)
    todo.open()
    todo.search(search_term)
    results_visible = todo.are_search_results_displayed(search_term)
    assert results_visible, (
        f"Expected to be on search results page for '{search_term}', but results were not found"
    )


@when('I filter results by price from "{min_price}" to "{max_price}"')
def step_filter_by_price_range(context, min_price, max_price):
    todo = get_todo(context)
    todo.apply_price_filter(min_price, max_price)
    assert todo.price_filter_was_applied(), (
        f"Price filter from '{min_price}' to '{max_price}' was not applied successfully"
    )


@then('refined search results filtered by price range "{min_price}" to "{max_price}" are displayed')
def step_refined_results_displayed(context, min_price, max_price):
    todo = get_todo(context)
    results_filtered = todo.are_filtered_results_displayed(min_price, max_price)
    assert results_filtered, (
        f"Expected refined search results filtered by price range '{min_price}' to '{max_price}' "
        f"to be displayed, but filtered results were not found"
    )
```