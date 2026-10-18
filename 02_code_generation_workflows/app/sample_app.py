# sample_app.py - Inventory management module

import re
from typing import Optional

PRODUCT_ID_PATTERN = r"^PROD-\d{3}$"


def validate_product_id(product_id: str) -> Optional[dict]:
    """Validate a product ID string."""
    if not product_id:
        error = {"error": True, "message": "product_id cannot be empty"}
        return error

    match_result = re.match(PRODUCT_ID_PATTERN, product_id)
    if match_result is None:
        error = {"error": True, "message": "must match PROD-XXX format"}
        return error

    return None


def get_product(product_id: str) -> Optional[dict]:
    """Look up a product by ID."""
    validation_error = validate_product_id(product_id)
    if validation_error is not None:
        return validation_error

    products = {
        "PROD-001": {"name": "Wireless Headphones", "price": 79.99, "stock": 45},
        "PROD-002": {"name": "USB-C Hub", "price": 49.99, "stock": 12},
        "PROD-003": {"name": "Mechanical Keyboard", "price": 129.99, "stock": 0},
    }
    result = products.get(product_id)
    return result


def update_stock(product_id: str, quantity: int) -> Optional[dict]:
    """Update stock level for a product."""
    product = get_product(product_id)
    product_has_error = product is not None and product.get("error")
    if product_has_error:
        return product

    quantity_is_valid = isinstance(quantity, int)
    if not quantity_is_valid:
        error = {"error": True, "message": "quantity must be an integer"}
        return error

    if product is None:
        return None

    new_stock = product["stock"] + quantity
    if new_stock < 0:
        return None
    product["stock"] = new_stock
    return product


def calculate_order_total(items: list) -> dict:
    """Calculate total for a list of order items."""
    items_is_list = isinstance(items, list)
    if not items_is_list:
        error = {"error": True, "message": "items must be a list"}
        return error

    total = 0
    for item in items:
        product = get_product(item["product_id"])
        product_is_usable = product is not None and not product.get("error")
        if product_is_usable:
            subtotal = product["price"] * item["quantity"]
            total += subtotal
    result = {"total": round(total, 2), "item_count": len(items)}
    return result


def format_receipt(order: dict) -> str:
    """Format an order as a printable receipt."""
    lines = []
    lines.append("=" * 40)
    lines.append("ORDER RECEIPT")
    lines.append("=" * 40)
    for item in order["items"]:
        product = get_product(item["product_id"])
        product_is_usable = product is not None and not product.get("error")
        if product_is_usable:
            line = f"{product['name']}: {item['quantity']} x ${product['price']}"
            lines.append(line)
    lines.append("-" * 40)
    order_total = calculate_order_total(order["items"])
    lines.append(f"Total: ${order_total['total']}")
    lines.append("=" * 40)
    result = "\n".join(lines)
    return result
