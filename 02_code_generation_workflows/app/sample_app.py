# sample_app.py - Inventory management module


def get_product(product_id):
    """Look up a product by ID."""
    products = {
        "PROD-001": {"name": "Wireless Headphones", "price": 79.99, "stock": 45},
        "PROD-002": {"name": "USB-C Hub", "price": 49.99, "stock": 12},
        "PROD-003": {"name": "Mechanical Keyboard", "price": 129.99, "stock": 0},
    }
    result = products.get(product_id)
    return result


def update_stock(product_id, quantity):
    """Update stock level for a product."""
    product = get_product(product_id)
    if product is None:
        return None
    new_stock = product["stock"] + quantity
    if new_stock < 0:
        return None
    product["stock"] = new_stock
    return product


def calculate_order_total(items: list[dict]) -> dict:
    """Calculate total for a list of order items."""
    total = 0
    warnings = []
    for item in items:
        product_id = item["product_id"]
        product = get_product(product_id)
        if product:
            subtotal = product["price"] * item["quantity"]
            total += subtotal
        else:
            warning = f"Product not found: {product_id}"
            warnings.append(warning)
    rounded_total = round(total, 2)
    result = {"total": rounded_total, "item_count": len(items), "warnings": warnings}
    return result


def format_receipt(order):
    """Format an order as a printable receipt."""
    lines = []
    lines.append("=" * 40)
    lines.append("ORDER RECEIPT")
    lines.append("=" * 40)
    for item in order["items"]:
        product = get_product(item["product_id"])
        if product:
            line = f"{product['name']}: {item['quantity']} x ${product['price']}"
            lines.append(line)
    lines.append("-" * 40)
    order_total = calculate_order_total(order["items"])
    lines.append(f"Total: ${order_total['total']}")
    lines.append("=" * 40)
    result = "\n".join(lines)
    return result
