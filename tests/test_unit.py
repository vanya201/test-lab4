import unittest
from unittest.mock import MagicMock
from eshop import Product, ShoppingCart


class TestProduct(unittest.TestCase):
    def setUp(self):
        self.product = Product(name='Test', price=123.45, available_amount=21)
        self.cart = ShoppingCart()

    def tearDown(self):
        self.cart.remove_product(self.product)

    def test_mock_add_product(self):
        self.product.is_available = MagicMock()
        self.cart.add_product(self.product, 12345)
        self.product.is_available.assert_called_with(12345)
        self.product.is_available.reset_mock()

    def test_add_available_amount(self):
        self.cart.add_product(self.product, 11)
        self.assertEqual(self.cart.contains_product(self.product), True, 'Продукт успішно доданий до корзини')

    def test_add_non_available_amount(self):
        with self.assertRaises(ValueError):
            self.cart.add_product(self.product, 22)
        self.assertEqual(self.cart.contains_product(self.product), False, 'Продукт не доданий до корзини')


if __name__ == '__main__':
    unittest.main()
