from behave import given, when, then
from eshop import Product


@given("A product with available amount of {amount}")
def create_product(context, amount):
    context.product = Product(name="test", price=10.0, available_amount=int(amount))
    context.error = None
    context.result = None


@when("I check availability for amount {amount}")
def check_availability(context, amount):
    try:
        value = None if amount == "None" else int(amount)
        context.result = context.product.is_available(value)
    except TypeError as e:
        context.error = e


@then("The product should be available")
def product_available(context):
    assert context.result == True


@then("The product should not be available")
def product_not_available(context):
    assert context.result == False


@when("I buy amount {amount}")
def buy_product(context, amount):
    context.product.buy(int(amount))


@then("The product available amount should be {amount}")
def check_available_amount(context, amount):
    assert context.product.available_amount == int(amount)


@then("An error is raised")
def error_raised(context):
    assert context.error is not None
