Feature: Trade Me Property Search
  As a property buyer
  I want to search and filter residential properties on Trade Me
  So that I can find properties that match my criteria

  Background:
    Given the Trade Me property search page is open at "https://www.trademe.co.nz/a/property/residential/sale"

  @smoke @ui @search @e2e
  Scenario: Search for residential property in Wellington
    When I search for "Wellington homes"
    Then search results appear showing residential properties matching the "Wellington homes" query

  @regression @ui @filter @e2e
  Scenario: Filter search results by price range 500k to 800k
    Given I am on the Trade Me property search page with results visible for "Wellington homes"
    When I apply a price filter with a minimum of "$500k" and a maximum of "$800k"
    Then only properties priced between "$500k" and "$800k" are displayed in the results