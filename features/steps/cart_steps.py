from behave import given, when, then
from eshop import Product, ShoppingCart


@given("The product has availability of {availability}")
def create_product_for_cart(context, availability):
    context.product = Product(name="any", price=123, available_amount=int(availability))


@given('An empty shopping cart')
def empty_cart(context):
    context.cart = ShoppingCart()


@when("I add product to the cart in amount {product_amount}")
def add_product(context, product_amount):
    try:
        context.cart.add_product(context.product, int(product_amount))
        context.add_successfully = True
    except ValueError:
        context.add_successfully = False


@then("Product is added to the cart successfully")
def add_successful(context):
    assert context.add_successfully == True


@then("Product is not added to cart successfully")
def add_failed(context):
    assert context.add_successfully == False


@then("The cart total should be {total}")
def check_cart_total(context, total):
    assert context.cart.calculate_total() == int(total)


@when("I remove a product not in cart")
def remove_missing_product(context):
    context.error = None
    try:
        missing = Product(name="ghost", price=1, available_amount=1)
        context.cart.remove_product(missing)
    except Exception as e:
        context.error = e


@then("No error occurs")
def no_error(context):
    assert context.error is None
