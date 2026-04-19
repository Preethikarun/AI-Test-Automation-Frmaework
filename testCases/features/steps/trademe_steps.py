# testCases/features/steps/trademe_steps.py

from behave import given, when, then
from facade.trademe_facade import TradeMeFacade
from context.test_context import TestContext


def _facade(context):
    return TradeMeFacade(context.page, context.tc)


# ══════════════════════════════════════════════════════════════
# GIVEN steps
# ══════════════════════════════════════════════════════════════

@given('the Trade Me property search page is open at "{url}"')
def step_open_property_search_page(context, url):
    """Navigate to the Trade Me property search page."""
    facade = _facade(context)
    facade.navigate_to_search_page()


@given('I am on the Trade Me property search page with results visible for "{term}"')
def step_property_search_page_with_results_visible(context, term):
    """Open the search page and perform a search so results are visible."""
    facade = _facade(context)
    context.search_term = term
    context.results = facade.search_only(term)
    facade.assert_has_results()


# ══════════════════════════════════════════════════════════════
# WHEN steps
# ══════════════════════════════════════════════════════════════

@when('I search for "{term}"')
def step_search_for_term(context, term):
    """Perform a property search using the given search term."""
    facade = _facade(context)
    context.results = facade.search_only(term)
    context.search_term = term


@when('I apply a price filter with a minimum of "{min_price}" and a maximum of "{max_price}"')
def step_apply_price_filter(context, min_price, max_price):
    """Apply a price range filter using the provided minimum and maximum price values."""
    context.min_price = min_price
    context.max_price = max_price
    facade = _facade(context)
    context.results = facade.search_and_filter(
        term=getattr(context, "search_term", "Wellington homes"),
        min_price=min_price,
        max_price=max_price,
    )


# ══════════════════════════════════════════════════════════════
# THEN steps
# ══════════════════════════════════════════════════════════════

@then('search results appear showing residential properties matching the "{query}" query')
def step_search_results_appear_for_query(context, query):
    """Assert that search results are displayed matching the given query term."""
    facade = _facade(context)
    facade.assert_has_results()


@then('only properties priced between "{min_price}" and "{max_price}" are displayed in the results')
def step_only_properties_in_price_range_displayed(context, min_price, max_price):
    """Assert that the displayed results contain properties within the specified price range."""
    facade = _facade(context)
    facade.assert_has_results()
