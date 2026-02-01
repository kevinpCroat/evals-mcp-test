"""
Order Processing System - Refactored for clarity and reduced duplication.
Public API preserved for test compatibility.
"""

from datetime import datetime
from typing import Dict, List, Any


def _round2(value: float) -> float:
    return round(value, 2)


class OrderProcessingSystemManager:
    """
    Coordinates order processing, inventory, customers, and reporting.
    Delegates to internal helpers to reduce complexity.
    """

    DISCOUNT_RULES = {'SAVE10': 0.10, 'SAVE20': 0.20, 'VIP': 0.25, 'FIRSTORDER': 0.15}
    SHIPPING_RATES = {'standard': 5.99, 'express': 15.99, 'overnight': 29.99}
    TAX_RATE = 0.085
    VIP_THRESHOLD = 1000
    FREE_SHIPPING_THRESHOLD = 100

    def __init__(self):
        self.orders: List[Dict] = []
        self.inventory: Dict[str, Dict] = {}
        self.customers: Dict[str, Dict] = {}

    @property
    def discount_rules(self):
        return self.DISCOUNT_RULES

    @property
    def shipping_rates(self):
        return self.SHIPPING_RATES

    def _find_order(self, order_id: int) -> Dict:
        for order in self.orders:
            if order['order_id'] == order_id:
                return order
        raise ValueError(f"Order {order_id} not found")

    def _get_customer(self, customer_id: str) -> Dict:
        if customer_id not in self.customers:
            raise ValueError(f"Customer {customer_id} not found")
        return self.customers[customer_id]

    def _get_product(self, product_id: str) -> Dict:
        if product_id not in self.inventory:
            raise ValueError(f"Product {product_id} not found")
        return self.inventory[product_id]

    def _ensure_customer(self, order_data: Dict) -> str:
        customer_id = order_data['customer_id']
        if customer_id not in self.customers:
            self.customers[customer_id] = {
                'id': customer_id,
                'name': order_data.get('customer_name', 'Unknown'),
                'email': order_data.get('customer_email', ''),
                'orders': [],
                'total_spent': 0,
                'is_vip': False
            }
        return customer_id

    def _validate_order_items(self, items: List[Dict]) -> None:
        if not items:
            raise ValueError("Order must contain at least one item")
        for item in items:
            if 'product_id' not in item:
                raise ValueError("Product ID is required for all items")
            if 'quantity' not in item:
                raise ValueError("Quantity is required for all items")
            quantity = item['quantity']
            product_id = item['product_id']
            if quantity <= 0:
                raise ValueError(f"Invalid quantity for product {product_id}")
            if product_id not in self.inventory:
                raise ValueError(f"Product {product_id} not found in inventory")
            product = self.inventory[product_id]
            if product['stock'] < quantity:
                raise ValueError(f"Insufficient stock for product {product_id}")

    def _calculate_subtotal(self, items: List[Dict]) -> float:
        return sum(
            self._get_product(it['product_id'])['price'] * it['quantity']
            for it in items
        )

    def _calculate_discount(self, subtotal: float, discount_code: str) -> float:
        if not discount_code:
            return 0
        if discount_code not in self.DISCOUNT_RULES:
            raise ValueError(f"Invalid discount code: {discount_code}")
        return subtotal * self.DISCOUNT_RULES[discount_code]

    def _calculate_shipping(self, order_total_after_discount: float, shipping_method: str) -> float:
        if shipping_method not in self.SHIPPING_RATES:
            raise ValueError(f"Invalid shipping method: {shipping_method}")
        if order_total_after_discount >= self.FREE_SHIPPING_THRESHOLD:
            return 0
        return self.SHIPPING_RATES[shipping_method]

    def _apply_order_to_inventory(self, items: List[Dict]) -> None:
        for item in items:
            product_id = item['product_id']
            self.inventory[product_id]['stock'] -= item['quantity']

    def _update_customer_after_order(self, customer_id: str, order_id: int, total: float) -> None:
        self.customers[customer_id]['orders'].append(order_id)
        self.customers[customer_id]['total_spent'] += total
        if self.customers[customer_id]['total_spent'] >= self.VIP_THRESHOLD:
            self.customers[customer_id]['is_vip'] = True

    def processOrderAndCalculateEverything(self, order_data: Dict) -> Dict:
        if not order_data:
            raise ValueError("Order data cannot be empty")
        if 'customer_id' not in order_data:
            raise ValueError("Customer ID is required")
        if 'items' not in order_data:
            raise ValueError("Items list is required")

        customer_id = self._ensure_customer(order_data)
        items = order_data['items']
        self._validate_order_items(items)

        subtotal = self._calculate_subtotal(items)
        discount_code = order_data.get('discount_code', '')
        discount_amount = self._calculate_discount(subtotal, discount_code)
        shipping_method = order_data.get('shipping_method', 'standard')
        shipping_cost = self._calculate_shipping(subtotal - discount_amount, shipping_method)
        taxable = subtotal - discount_amount
        tax_amount = taxable * self.TAX_RATE
        total = _round2(subtotal - discount_amount + shipping_cost + tax_amount)

        order = {
            'order_id': len(self.orders) + 1,
            'customer_id': customer_id,
            'items': items,
            'subtotal': _round2(subtotal),
            'discount_code': discount_code,
            'discount_amount': _round2(discount_amount),
            'shipping_method': shipping_method,
            'shipping_cost': _round2(shipping_cost),
            'tax_amount': _round2(tax_amount),
            'total': total,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }

        self._apply_order_to_inventory(items)
        self._update_customer_after_order(customer_id, order['order_id'], total)
        self.orders.append(order)
        return order

    def getOrderSummaryWithAllDetails(self, order_id: int) -> Dict:
        found_order = self._find_order(order_id)
        customer = self._get_customer(found_order['customer_id'])
        item_details = []
        for item in found_order['items']:
            product = self._get_product(item['product_id'])
            item_details.append({
                'product_id': item['product_id'],
                'name': product['name'],
                'quantity': item['quantity'],
                'price': product['price'],
                'total': product['price'] * item['quantity']
            })
        return {
            'order_id': found_order['order_id'],
            'customer': {
                'id': customer['id'], 'name': customer['name'],
                'email': customer['email'], 'is_vip': customer['is_vip']
            },
            'items': item_details,
            'subtotal': found_order['subtotal'],
            'discount_code': found_order['discount_code'],
            'discount_amount': found_order['discount_amount'],
            'shipping_method': found_order['shipping_method'],
            'shipping_cost': found_order['shipping_cost'],
            'tax_amount': found_order['tax_amount'],
            'total': found_order['total'],
            'status': found_order['status'],
            'created_at': found_order['created_at']
        }

    def cancelOrderAndRestoreInventory(self, order_id: int) -> Dict:
        found_order = self._find_order(order_id)
        if found_order['status'] == 'cancelled':
            raise ValueError("Order is already cancelled")
        for item in found_order['items']:
            product_id = item['product_id']
            if product_id in self.inventory:
                self.inventory[product_id]['stock'] += item['quantity']
        customer_id = found_order['customer_id']
        if customer_id in self.customers:
            self.customers[customer_id]['total_spent'] -= found_order['total']
            if self.customers[customer_id]['total_spent'] < self.VIP_THRESHOLD:
                self.customers[customer_id]['is_vip'] = False
        found_order['status'] = 'cancelled'
        return found_order

    def addProductToInventory(self, product_id: str, name: str, price: float, stock: int) -> Dict:
        if not product_id:
            raise ValueError("Product ID cannot be empty")
        if product_id in self.inventory:
            raise ValueError(f"Product {product_id} already exists")
        if not name:
            raise ValueError("Product name cannot be empty")
        if price <= 0:
            raise ValueError("Price must be positive")
        if stock < 0:
            raise ValueError("Stock cannot be negative")
        self.inventory[product_id] = {
            'product_id': product_id,
            'name': name,
            'price': price,
            'stock': stock
        }
        return self.inventory[product_id]

    def updateProductStock(self, product_id: str, new_stock: int) -> Dict:
        self._get_product(product_id)
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
        self.inventory[product_id]['stock'] = new_stock
        return self.inventory[product_id]

    def getCustomerOrderHistory(self, customer_id: str) -> Dict:
        customer = self._get_customer(customer_id)
        customer_orders = [o for o in self.orders if o['customer_id'] == customer_id]
        return {
            'customer_id': customer['id'],
            'customer_name': customer['name'],
            'is_vip': customer['is_vip'],
            'total_spent': customer['total_spent'],
            'order_count': len(customer_orders),
            'orders': customer_orders
        }

    def getInventoryReport(self) -> Dict:
        products = [
            {
                'product_id': p['product_id'],
                'name': p['name'],
                'price': p['price'],
                'stock': p['stock'],
                'status': 'in_stock' if p['stock'] > 0 else 'out_of_stock'
            }
            for p in self.inventory.values()
        ]
        return {'total_products': len(self.inventory), 'products': products}

    def calculateRevenueReport(self) -> Dict:
        completed = [o for o in self.orders if o['status'] != 'cancelled']
        total_revenue = sum(o['total'] for o in completed)
        total_discounts = sum(o['discount_amount'] for o in completed)
        total_shipping = sum(o['shipping_cost'] for o in completed)
        total_tax = sum(o['tax_amount'] for o in completed)
        return {
            'order_count': len(completed),
            'total_revenue': _round2(total_revenue),
            'total_discounts': _round2(total_discounts),
            'total_shipping': _round2(total_shipping),
            'total_tax': _round2(total_tax)
        }
