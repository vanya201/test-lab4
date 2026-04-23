Feature:Shopping cart
  We want to test that shopping cart functionality works correctly
  Scenario: Successful add product to cart
    Given The product has availability of 123
    And An empty shopping cart
    When I add product to the cart in amount 123
    Then Product is added to the cart successfully
  Scenario: Failed add product to cart
    Given The product has availability of 123
    And An empty shopping cart
    When I add product to the cart in amount 124
    Then Product is not added to cart successfully

  Scenario: Empty cart total is zero
    Given An empty shopping cart
    Then The cart total should be 0

  Scenario: Adding product with amount 0 succeeds
    Given The product has availability of 5
    And An empty shopping cart
    When I add product to the cart in amount 0
    Then Product is added to the cart successfully

  Scenario: Removing non-existent product does not raise error
    Given An empty shopping cart
    When I remove a product not in cart
    Then No error occurs
