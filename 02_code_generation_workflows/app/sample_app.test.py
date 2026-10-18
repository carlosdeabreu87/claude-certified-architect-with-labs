# sample_app.test.py - Tests for inventory management module
import unittest

from sample_app import get_product, update_stock, calculate_order_total


class TestGetProduct(unittest.TestCase):
    def test_existing_product(self):
        result = get_product("PROD-001")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Wireless Headphones")

    def test_missing_product(self):
        result = get_product("PROD-999")
        self.assertIsNone(result)

    def test_empty_product_id(self):
        result = get_product("")
        self.assertEqual(result["message"], "product_id cannot be empty")

    def test_invalid_product_id_format(self):
        result = get_product("INVALID")
        self.assertEqual(result["message"], "must match PROD-XXX format")


class TestUpdateStock(unittest.TestCase):
    def test_add_stock(self):
        result = update_stock("PROD-001", 10)
        self.assertIsNotNone(result)

    def test_invalid_product(self):
        result = update_stock("PROD-999", 5)
        self.assertIsNone(result)

    def test_negative_result(self):
        result = update_stock("PROD-003", -5)
        self.assertIsNone(result)

    def test_non_integer_quantity(self):
        result = update_stock("PROD-001", "abc")
        self.assertEqual(result["message"], "quantity must be an integer")


class TestCalculateOrderTotal(unittest.TestCase):
    def test_single_item(self):
        items = [{"product_id": "PROD-001", "quantity": 2}]
        result = calculate_order_total(items)
        self.assertEqual(result["total"], 159.98)

    def test_multiple_items(self):
        items = [
            {"product_id": "PROD-001", "quantity": 1},
            {"product_id": "PROD-002", "quantity": 1},
        ]
        result = calculate_order_total(items)
        self.assertEqual(result["total"], 129.98)

    def test_empty_order(self):
        result = calculate_order_total([])
        self.assertEqual(result["total"], 0)

    def test_non_list_items(self):
        result = calculate_order_total("not a list")
        self.assertEqual(result["message"], "items must be a list")


if __name__ == "__main__":
    unittest.main()
