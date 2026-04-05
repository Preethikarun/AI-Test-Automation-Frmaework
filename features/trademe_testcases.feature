Feature: Trade Me Property search and filtering
  As a property buyer
  I want to search and filter residential properties on Trade Me
  So that I can find homes that match my location and budget

  Background:
    Given the Trade Me Property page is open

  @smoke @ui
  Scenario: User sees Wellington homes results after searching by location
    When I search for "Wellington homes"
    Then search results for "Wellington homes" are displayed

  @regression @ui
  Scenario: User sees price-filtered results after setting range 100k to 800k
    Given the search results page for "Wellington homes" is displayed
    When I filter results by price from "100k" to "800k"
    Then refined search results filtered by price range "100k" to "800k" are displayed