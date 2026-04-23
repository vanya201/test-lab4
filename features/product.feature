Feature: Product
  We want to test that Product functionality works correctly

  Scenario: Product is available when requested amount equals stock
    Given A product with available amount of 5
    When I check availability for amount 5
    Then The product should be available

  Scenario: Product is unavailable when requested amount exceeds stock by 1
    Given A product with available amount of 5
    When I check availability for amount 6
    Then The product should not be available

  Scenario: Product is unavailable when stock is 0
    Given A product with available amount of 0
    When I check availability for amount 1
    Then The product should not be available

  Scenario: Buying product reduces available amount correctly
    Given A product with available amount of 10
    When I buy amount 3
    Then The product available amount should be 7

  Scenario: Checking availability with None raises an error
    Given A product with available amount of 5
    When I check availability for amount None
    Then An error is raised
