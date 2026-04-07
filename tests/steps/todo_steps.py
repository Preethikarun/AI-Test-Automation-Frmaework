```python
from behave import given, when, then
from pages.todo_page import TodoPage


def get_todo(context):
    if not hasattr(context, 'todo'):
        context.todo = TodoPage(context.driver)
    return context.todo


@given('the Trade Me Property residential sale page is open')
def step_open_trade_me_property_page(context):
    page = get_todo(context)
    page.open_residential_sale_page()
    assert page.is_page_loaded(), "Trade Me Property residential sale page failed to load"


@when('I search for "{search_term}"')
def step_search_for_term(context, search_term):
    page = get_todo(context)
    page.search_for(search_term)


@given('search results for "{search_term}" are displayed')
def step_given_search_results_displayed(context, search_term):
    page = get_todo(context)
    page.search_for(search_term)
    assert page.are_search_results_displayed(search_term), (
        f"Expected search results for '{search_term}' to be displayed, but they were not found"
    )


@then('search results for "{search_term}" are displayed')
def step_then_search_results_displayed(context, search_term):
    page = get_todo(context)
    assert page.are_search_results_displayed(search_term), (
        f"Expected search results for '{search_term}' to be displayed, but they were not found"
    )


@when('I filter results by price from "{min_price}" to "{max_price}"')
def step_filter_by_price(context, min_price, max_price):
    page = get_todo(context)
    page.filter_by_price(min_price, max_price)


@then('refined search results filtered by price range "{min_price}" to "{max_price}" are displayed')
def step_verify_price_filtered_results(context, min_price, max_price):
    page = get_todo(context)
    assert page.are_price_filtered_results_displayed(min_price, max_price), (
        f"Expected refined search results filtered by price range '{min_price}' to '{max_price}' "
        f"to be displayed, but they were not found"
    )
```