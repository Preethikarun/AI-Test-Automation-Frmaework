Feature: Todo application
  As a user
  I want to manage my daily tasks
  So that I can stay organised

  @smoke @ui
  Scenario: Add a single todo item
    Given the todo app is open
    When I add a todo item "Build AI test framework"
    Then the todo count shows 1
    And the item "Build AI test framework" is visible

  @regression @ui
  Scenario: Add multiple todo items
    Given the todo app is open
    When I add a todo item "Day 1 foundation"
        And I add a todo item "Day 2 AI agents"
    And I add a todo item "Day 3 CI/CD"
    Then the todo count shows 3

  @regression @ui
  Scenario: Complete a todo item
    Given the todo app is open
    And I add a todo item "Complete me"
    When I complete todo item 1
    Then the todo count shows 0

  @regression @ui
  Scenario: Delete a todo item
    Given the todo app is open
    And I add a todo item "Delete me"
    And I add a todo item "Keep me"
        When I delete todo item 1
    Then the item "Delete me" is not visible
    And the item "Keep me" is visible