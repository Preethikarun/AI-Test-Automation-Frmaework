import requests
from behave import given, when, then
from facade.trademe_facade import TrademeFacade


def _facade(context):
    """Helper to instantiate the TrademeFacade with the current page and test context."""
    return TrademeFacade(context.page, context.tc)


# ---------------------------------------------------------------------------
# GIVEN steps
# ---------------------------------------------------------------------------

@given('the Trade Me property search page is open')
def step_given_trademe_property_search_page_is_open(context):
    """Open the Trade Me property search page via the facade."""
    facade = _facade(context)
    facade.open_property_search_page()


@given('search results are displayed for "{search_term}"')
def step_given_search_results_displayed_for(context, search_term):
    """Perform a search so that results are already on screen before the When step."""
    facade = _facade(context)
    facade.open_property_search_page()
    context.results = facade.enter_search_term_and_submit(search_term)


@given('filtered search results are visible')
def step_given_filtered_search_results_visible(context):
    """Ensure filtered search results are visible by performing a default search and price filter."""
    facade = _facade(context)
    facade.open_property_search_page()
    facade.enter_search_term_and_submit("Wellington homes")
    facade.apply_price_filter("500000", "800000")
    context.results = facade.get_current_listings()


@given('price-filtered search results are displayed')
def step_given_price_filtered_search_results_displayed(context):
    """Set up price-filtered search results before bedroom filtering."""
    facade = _facade(context)
    facade.open_property_search_page()
    facade.enter_search_term_and_submit("Wellington homes")
    facade.apply_price_filter("500000", "800000")
    context.results = facade.get_current_listings()


@given('a listing detail page is open')
def step_given_listing_detail_page_is_open(context):
    """Navigate to a listing detail page by searching and clicking the first result."""
    facade = _facade(context)
    facade.open_property_search_page()
    facade.enter_search_term_and_submit("Wellington homes")
    context.listing = facade.click_first_listing()


@given('the Trade Me property search API is available and the property search page is open')
def step_given_api_available_and_page_open(context):
    """Verify the Trade Me property search API is reachable and open the property search page."""
    facade = _facade(context)
    facade.open_property_search_page()
    facade.verify_api_is_available()


# ---------------------------------------------------------------------------
# WHEN steps
# ---------------------------------------------------------------------------

@when('I enter "{search_term}" in the search box and click the Search button')
def step_when_enter_search_term_and_click_search(context, search_term):
    """Enter a search term in the search box and submit the search."""
    facade = _facade(context)
    context.results = facade.enter_search_term_and_submit(search_term)


@when('I enter "{min_price}" in the minimum price field, enter "{max_price}" in the maximum price field, and click Apply Filter')
def step_when_enter_price_range_and_apply_filter(context, min_price, max_price):
    """Enter minimum and maximum price values and apply the price range filter."""
    facade = _facade(context)
    facade.apply_price_filter(min_price, max_price)
    context.results = facade.get_current_listings()


@when('I click on the first listing card in the results')
def step_when_click_first_listing_card(context):
    """Click the first listing card displayed in the search results."""
    facade = _facade(context)
    context.listing = facade.click_first_listing()


@when('I enter "{suburb}" in the suburb filter field and click Apply Filter')
def step_when_enter_suburb_filter_and_apply(context, suburb):
    """Enter a suburb name in the suburb filter field and apply the filter."""
    facade = _facade(context)
    facade.apply_suburb_filter(suburb)
    context.results = facade.get_current_listings()


@when('I select "{bedrooms}" from the bedrooms dropdown and click Apply Filter')
def step_when_select_bedrooms_and_apply_filter(context, bedrooms):
    """Select the number of bedrooms from the dropdown and apply the filter."""
    facade = _facade(context)
    facade.apply_bedrooms_filter(bedrooms)
    context.results = facade.get_current_listings()


@when('I verify the price element is visible on the page')
def step_when_verify_price_element_visible(context):
    """Check that the price element is visible on the listing detail page."""
    facade = _facade(context)
    context.tc.price_element = facade.get_price_element()
    assert context.tc.price_element is not None, "Price element was not found on the listing detail page"


@when('I enter "{search_term}" in the search box, click Search, apply a price filter of "{min_price}" to "{max_price}", and click the first listing')
def step_when_e2e_search_filter_and_click_first_listing(context, search_term, min_price, max_price):
    """Full end-to-end: search, apply price filter, then click the first listing."""
    facade = _facade(context)
    facade.enter_search_term_and_submit(search_term)
    facade.apply_price_filter_by_label(min_price, max_price)
    context.listing = facade.click_first_listing()


@when('I call the property search API for "{location}", verify the API returns listings, search the UI for "{search_term}", and verify the displayed results')
def step_when_api_search_and_ui_verify(context, location, search_term):
    """Call the property search API for a location, then search the UI and verify both return listings."""
    facade = _facade(context)
    context.tc.api_response = facade.call_property_search_api(location)
    assert context.tc.api_response is not None, "API response must not be None"
    facade.assert_api_returns_listings(context.tc.api_response)
    context.results = facade.enter_search_term_and_submit(search_term)
    assert context.results is not None, "UI search results must not be None"


# ---------------------------------------------------------------------------
# THEN steps
# ---------------------------------------------------------------------------

@then('at least one property listing is displayed in the results')
def step_then_at_least_one_listing_displayed(context):
    """Assert that at least one property listing is shown in the search results."""
    facade = _facade(context)
    facade.assert_at_least_one_listing_displayed()


@then('the results are filtered and only listings priced between "{min_price}" and "{max_price}" are shown')
def step_then_results_filtered_by_price_range(context, min_price, max_price):
    """Assert that the displayed listings are all priced within the specified range."""
    facade = _facade(context)
    facade.assert_listings_within_price_range(min_price, max_price)


@then('the listing detail page loads with the title, price, address, and agent information all visible')
def step_then_listing_detail_page_loads_with_full_info(context):
    """Assert that the listing detail page shows title, price, address, and agent information."""
    facade = _facade(context)
    facade.assert_listing_detail_has_title()
    facade.assert_listing_detail_has_price()
    facade.assert_listing_detail_has_address()
    facade.assert_listing_detail_has_agent_info()


@then('only listings located in the "{suburb}" suburb are displayed')
def step_then_only_suburb_listings_displayed(context, suburb):
    """Assert that all displayed listings belong to the specified suburb."""
    facade = _facade(context)
    facade.assert_listings_in_suburb(suburb)


@then('only "{bedrooms}"-bedroom properties are shown in the results')
def step_then_only_bedroom_count_properties_shown(context, bedrooms):
    """Assert that all displayed listings match the specified bedroom count."""
    facade = _facade(context)
    facade.assert_listings_have_bedrooms(bedrooms)


@then('the property price is displayed and is not empty')
def step_then_property_price_displayed_and_not_empty(context):
    """Assert that the property price on the detail page is visible and has non-empty content."""
    facade = _facade(context)
    facade.assert_price_element_not_empty(context.tc.price_element)


@then('the listing detail page loads correctly showing the title, price, and agent details')
def step_then_listing_detail_loads_with_title_price_agent(context):
    """Assert that the listing detail page correctly displays title, price, and agent details."""
    facade = _facade(context)
    facade.assert_listing_detail_has_title()
    facade.assert_listing_detail_has_price()
    facade.assert_listing_detail_has_agent_info()


@then('the API returns a "{expected_status}" response with listing data and the UI displays matching property listings')
def step_then_api_returns_status_and_ui_shows_listings(context, expected_status):
    """Assert that the API returned the expected HTTP status with listing data, and the UI shows listings."""
    facade = _facade(context)
    facade.assert_api_response_status(context.tc.api_response, int(expected_status))
    facade.assert_api_returns_listings(context.tc.api_response)
    facade.assert_at_least_one_listing_displayed()