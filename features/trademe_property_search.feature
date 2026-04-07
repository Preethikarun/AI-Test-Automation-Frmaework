Feature: Property Search on Trade Me

  Background:
    Given the Trade Me property search page is open

  @smoke @search @ui
  Scenario: Search returns property listings for Wellington
    When I enter "Wellington homes" in the search box and click the Search button
    Then at least one property listing is displayed in the results

  @regression @filter @ui
  Scenario: Filter by price range narrows results
    Given search results are displayed for "Wellington homes"
    When I enter "500000" in the minimum price field, enter "800000" in the maximum price field, and click Apply Filter
    Then the results are filtered and only listings priced between "$500,000" and "$800,000" are shown

  @regression @detail @ui
  Scenario: Open first listing shows detail page
    Given filtered search results are visible
    When I click on the first listing card in the results
    Then the listing detail page loads with the title, price, address, and agent information all visible

  @regression @filter @ui
  Scenario: Filter by suburb narrows results to that area
    Given search results are displayed for "New Zealand homes"
    When I enter "Thorndon" in the suburb filter field and click Apply Filter
    Then only listings located in the "Thorndon" suburb are displayed

  @regression @filter @ui
  Scenario: Filter by bedrooms shows matching properties
    Given price-filtered search results are displayed
    When I select "3" from the bedrooms dropdown and click Apply Filter
    Then only "3"-bedroom properties are shown in the results

  @regression @detail @ui
  Scenario: Listing detail shows price
    Given a listing detail page is open
    When I verify the price element is visible on the page
    Then the property price is displayed and is not empty

  @regression @e2e @ui
  Scenario: Search, filter and view detail - full end-to-end flow
    When I enter "Wellington homes" in the search box, click Search, apply a price filter of "$500k" to "$800k", and click the first listing
    Then the listing detail page loads correctly showing the title, price, and agent details

  @regression @e2e @api
  Scenario: API confirms listings exist and UI displays them
    Given the Trade Me property search API is available and the property search page is open
    When I call the property search API for "Wellington", verify the API returns listings, search the UI for "Wellington homes", and verify the displayed results
    Then the API returns a "200" response with listing data and the UI displays matching property listings