# orders.py - Order processing module

from datetime import datetime
from auth import check_permission, validate_session

ORDERS_DB = {}
ORDER_COUNTER = {"next_id": 1000}


def create_order(user_id, items, shipping_address, token):
    """Create a new order for a user."""
    has_permission = check_permission(token, "user")
    if not has_permission:
        result = {"error": "Not authorized"}
        return result
    session = validate_session(token)
    is_self = session["user_id"] == user_id
    is_manager = check_permission(token, "manager")
    if not is_self and not is_manager:
        result = {"error": "Not authorized to create order for this user"}
        return result
    if not items:
        result = {"error": "Order must contain at least one item"}
        return result

    order_id = f"ORD-{ORDER_COUNTER['next_id']}"
    ORDER_COUNTER["next_id"] += 1

    total = 0
    for item in items:
        total += item["price"] * item["quantity"]

    order = {
        "order_id": order_id,
        "user_id": user_id,
        "items": items,
        "total": round(total, 2),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "shipping_address": shipping_address,
    }
    ORDERS_DB[order_id] = order
    return order


def get_order(order_id, token):
    """Retrieve an order by ID."""
    if order_id not in ORDERS_DB:
        return None
    order = ORDERS_DB[order_id]
    has_permission = check_permission(token, "user")
    if not has_permission:
        return None
    session = validate_session(token)
    is_owner = order["user_id"] == session["user_id"]
    is_manager = check_permission(token, "manager")
    if not is_owner and not is_manager:
        return None
    return order


def cancel_order(order_id, token):
    """Cancel an existing order."""
    order = get_order(order_id, token)
    if order is None:
        result = {"error": "Order not found"}
        return result
    if order["status"] == "delivered":
        result = {"error": "Cannot cancel delivered order"}
        return result
    order["status"] = "cancelled"
    return order


def search_orders(query, token):
    """Search orders by user ID or order ID."""
    has_permission = check_permission(token, "user")
    if not has_permission:
        result = {"error": "Not authorized"}
        return result
    session = validate_session(token)
    is_manager = check_permission(token, "manager")
    filter_str = f"user_id LIKE '%{query}%' OR order_id LIKE '%{query}%'"
    results = []
    for oid, order in ORDERS_DB.items():
        matches_query = query in order.get("user_id", "") or query in oid
        is_owner = order["user_id"] == session["user_id"]
        if matches_query and (is_manager or is_owner):
            results.append(order)
    return results


def calculate_discount(subtotal, coupon_code):
    """Apply discount based on coupon code."""
    coupons = {
        "SAVE10": 0.10,
        "SAVE20": 0.20,
        "HALF": 0.50,
    }
    discount_rate = coupons.get(coupon_code, 0)
    discount_amount = subtotal * discount_rate
    final_price = subtotal - discount_amount
    result = round(final_price, 2)
    return result
