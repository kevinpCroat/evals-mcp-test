"""
Comprehensive tests for shopping_cart module.
Covers Item, ShoppingCart, exceptions; normal, edge, and error cases.
"""

import pytest
from decimal import Decimal
from shopping_cart import (
    Item,
    ShoppingCart,
    InvalidQuantityError,
    InvalidPriceError,
    InvalidDiscountError,
)


# =============================================================================
# Item class tests
# =============================================================================

class TestItemInitialization:
    def test_create_item_valid(self):
        item = Item("item1", "Test Product", 10.99, 2)
        assert item.item_id == "item1"
        assert item.name == "Test Product"
        assert item.price == Decimal("10.99")
        assert item.quantity == 2

    def test_create_item_default_quantity(self):
        item = Item("item1", "Product", 10.99)
        assert item.quantity == 1

    def test_create_item_zero_price(self):
        item = Item("item1", "Free Item", 0.0, 1)
        assert item.price == Decimal("0.0")

    @pytest.mark.parametrize("item_id", ["", None])
    def test_create_item_invalid_id(self, item_id):
        with pytest.raises(ValueError, match="Item ID must be a non-empty string"):
            Item(item_id, "Product", 10.0)

    @pytest.mark.parametrize("name", ["", None])
    def test_create_item_invalid_name(self, name):
        with pytest.raises(ValueError, match="Item name must be a non-empty string"):
            Item("item1", name, 10.0)

    def test_create_item_negative_price(self):
        with pytest.raises(InvalidPriceError, match="Price cannot be negative"):
            Item("item1", "Product", -5.0)

    @pytest.mark.parametrize("quantity", [0, -1, -10])
    def test_create_item_invalid_quantity(self, quantity):
        with pytest.raises(InvalidQuantityError, match="Quantity must be positive"):
            Item("item1", "Product", 10.0, quantity)


class TestItemMethods:
    def test_get_total_single(self):
        item = Item("item1", "Product", 10.50, 1)
        assert item.get_total() == Decimal("10.50")

    def test_get_total_multiple(self):
        item = Item("item1", "Product", 10.50, 3)
        assert item.get_total() == Decimal("31.50")

    def test_get_total_decimal_precision(self):
        item = Item("item1", "Product", 10.99, 7)
        assert item.get_total() == Decimal("76.93")


# =============================================================================
# ShoppingCart initialization
# =============================================================================

class TestShoppingCartInitialization:
    def test_create_cart_default_tax(self):
        cart = ShoppingCart()
        assert cart.tax_rate == Decimal("0.0")
        assert len(cart.items) == 0
        assert cart.loyalty_points == 0

    def test_create_cart_with_tax_rate(self):
        cart = ShoppingCart(tax_rate=0.08)
        assert cart.tax_rate == Decimal("0.08")

    @pytest.mark.parametrize("tax_rate", [-0.1, 1.1, 2.0])
    def test_create_cart_invalid_tax_rate(self, tax_rate):
        with pytest.raises(ValueError, match="Tax rate must be between 0 and 1"):
            ShoppingCart(tax_rate=tax_rate)


# =============================================================================
# ShoppingCart item management
# =============================================================================

class TestShoppingCartItemManagement:
    @pytest.fixture
    def cart(self):
        return ShoppingCart()

    @pytest.fixture
    def sample_item(self):
        return Item("item1", "Product 1", 10.0, 1)

    def test_add_item_to_empty_cart(self, cart, sample_item):
        cart.add_item(sample_item)
        assert len(cart.items) == 1
        assert cart.items["item1"] == sample_item

    def test_add_duplicate_increases_quantity(self, cart):
        cart.add_item(Item("item1", "Product", 10.0, 2))
        cart.add_item(Item("item1", "Product", 10.0, 3))
        assert len(cart.items) == 1
        assert cart.items["item1"].quantity == 5

    def test_add_multiple_different_items(self, cart):
        cart.add_item(Item("item1", "Product 1", 10.0))
        cart.add_item(Item("item2", "Product 2", 20.0))
        assert len(cart.items) == 2

    def test_add_non_item_raises(self, cart):
        with pytest.raises(TypeError, match="Must provide an Item instance"):
            cart.add_item("not an item")

    def test_remove_existing_item(self, cart, sample_item):
        cart.add_item(sample_item)
        cart.remove_item("item1")
        assert len(cart.items) == 0

    def test_remove_nonexistent_raises(self, cart):
        with pytest.raises(KeyError, match="Item item1 not found"):
            cart.remove_item("item1")

    def test_update_quantity_existing(self, cart, sample_item):
        cart.add_item(sample_item)
        cart.update_quantity("item1", 5)
        assert cart.items["item1"].quantity == 5

    def test_update_quantity_zero_raises(self, cart, sample_item):
        cart.add_item(sample_item)
        with pytest.raises(InvalidQuantityError, match="Quantity must be positive"):
            cart.update_quantity("item1", 0)

    def test_update_quantity_negative_raises(self, cart, sample_item):
        cart.add_item(sample_item)
        with pytest.raises(InvalidQuantityError, match="Quantity must be positive"):
            cart.update_quantity("item1", -5)

    def test_update_quantity_nonexistent_raises(self, cart):
        with pytest.raises(KeyError, match="Item item1 not found"):
            cart.update_quantity("item1", 5)


# =============================================================================
# ShoppingCart counts and state
# =============================================================================

class TestShoppingCartCounts:
    @pytest.fixture
    def cart(self):
        return ShoppingCart()

    def test_empty_cart_counts(self, cart):
        assert cart.get_item_count() == 0
        assert cart.get_unique_item_count() == 0
        assert cart.is_empty() is True

    def test_cart_single_item_counts(self, cart):
        cart.add_item(Item("item1", "Product", 10.0, 3))
        assert cart.get_item_count() == 3
        assert cart.get_unique_item_count() == 1
        assert cart.is_empty() is False

    def test_cart_multiple_items_counts(self, cart):
        cart.add_item(Item("item1", "P1", 10.0, 2))
        cart.add_item(Item("item2", "P2", 20.0, 3))
        cart.add_item(Item("item3", "P3", 30.0, 1))
        assert cart.get_item_count() == 6
        assert cart.get_unique_item_count() == 3

    def test_clear_cart(self, cart):
        cart.add_item(Item("item1", "Product", 10.0))
        cart.apply_discount("SAVE10", 10)
        cart.clear()
        assert cart.is_empty() is True
        assert len(cart.discounts) == 0


# =============================================================================
# ShoppingCart price calculations
# =============================================================================

class TestShoppingCartPriceCalculations:
    @pytest.fixture
    def cart(self):
        return ShoppingCart()

    def test_empty_cart_subtotal(self, cart):
        assert cart.get_subtotal() == Decimal("0")

    def test_single_item_subtotal(self, cart):
        cart.add_item(Item("item1", "Product", 10.50, 2))
        assert cart.get_subtotal() == Decimal("21.00")

    def test_multiple_items_subtotal(self, cart):
        cart.add_item(Item("item1", "P1", 10.00, 2))
        cart.add_item(Item("item2", "P2", 15.50, 1))
        assert cart.get_subtotal() == Decimal("35.50")


# =============================================================================
# ShoppingCart discounts
# =============================================================================

class TestShoppingCartDiscounts:
    @pytest.fixture
    def cart(self):
        c = ShoppingCart()
        c.add_item(Item("item1", "Product", 100.0, 1))
        return c

    def test_no_discount(self, cart):
        assert cart.get_discount_amount() == Decimal("0")

    def test_single_discount(self, cart):
        cart.apply_discount("SAVE10", 10)
        assert cart.get_discount_amount() == Decimal("10.00")

    def test_multiple_discounts(self, cart):
        cart.apply_discount("SAVE10", 10)
        cart.apply_discount("EXTRA5", 5)
        assert cart.get_discount_amount() == Decimal("15.00")

    def test_discount_cannot_exceed_subtotal(self):
        cart = ShoppingCart()
        cart.add_item(Item("item1", "Product", 50.0, 1))
        cart.apply_discount("HUGE", 80)
        cart.apply_discount("MORE", 40)
        assert cart.get_discount_amount() == Decimal("50.00")

    def test_negative_discount_raises(self, cart):
        with pytest.raises(InvalidDiscountError, match="between 0 and 100"):
            cart.apply_discount("BAD", -10)

    def test_over_100_discount_raises(self, cart):
        with pytest.raises(InvalidDiscountError, match="between 0 and 100"):
            cart.apply_discount("BAD", 101)


# =============================================================================
# ShoppingCart tax
# =============================================================================

class TestShoppingCartTax:
    def test_no_tax_rate(self):
        cart = ShoppingCart(tax_rate=0.0)
        cart.add_item(Item("item1", "Product", 100.0))
        assert cart.get_tax_amount() == Decimal("0")

    def test_tax_on_subtotal(self):
        cart = ShoppingCart(tax_rate=0.08)
        cart.add_item(Item("item1", "Product", 100.0))
        assert cart.get_tax_amount() == Decimal("8.00")

    def test_tax_after_discount(self):
        cart = ShoppingCart(tax_rate=0.10)
        cart.add_item(Item("item1", "Product", 100.0))
        cart.apply_discount("SAVE20", 20)
        assert cart.get_tax_amount() == Decimal("8.00")


# =============================================================================
# ShoppingCart total
# =============================================================================

class TestShoppingCartTotal:
    def test_total_without_discount_or_tax(self):
        cart = ShoppingCart()
        cart.add_item(Item("item1", "Product", 50.0, 2))
        assert cart.get_total() == Decimal("100.00")

    def test_total_with_tax_only(self):
        cart = ShoppingCart(tax_rate=0.10)
        cart.add_item(Item("item1", "Product", 100.0))
        assert cart.get_total() == Decimal("110.00")

    def test_total_with_discount_only(self):
        cart = ShoppingCart()
        cart.add_item(Item("item1", "Product", 100.0))
        cart.apply_discount("SAVE20", 20)
        assert cart.get_total() == Decimal("80.00")

    def test_total_with_discount_and_tax(self):
        cart = ShoppingCart(tax_rate=0.10)
        cart.add_item(Item("item1", "Product", 100.0))
        cart.apply_discount("SAVE20", 20)
        assert cart.get_total() == Decimal("88.00")

    def test_total_empty_cart(self):
        cart = ShoppingCart(tax_rate=0.10)
        assert cart.get_total() == Decimal("0")


# =============================================================================
# ShoppingCart loyalty points
# =============================================================================

class TestShoppingCartLoyaltyPoints:
    def test_initial_loyalty_points(self):
        cart = ShoppingCart()
        assert cart.loyalty_points == 0

    def test_apply_loyalty_points(self):
        cart = ShoppingCart()
        cart.apply_loyalty_points(100)
        assert cart.loyalty_points == 100

    def test_apply_negative_loyalty_points_raises(self):
        cart = ShoppingCart()
        with pytest.raises(ValueError, match="cannot be negative"):
            cart.apply_loyalty_points(-10)

    def test_calculate_loyalty_points_from_purchase(self):
        cart = ShoppingCart()
        cart.add_item(Item("item1", "Product", 45.99))
        assert cart.calculate_loyalty_points() == 45


# =============================================================================
# ShoppingCart item retrieval
# =============================================================================

class TestShoppingCartItemRetrieval:
    @pytest.fixture
    def cart(self):
        c = ShoppingCart()
        c.add_item(Item("item1", "Cheap", 10.0))
        c.add_item(Item("item2", "Medium", 50.0))
        c.add_item(Item("item3", "Expensive", 100.0))
        return c

    def test_get_existing_item(self, cart):
        item = cart.get_item("item1")
        assert item is not None
        assert item.item_id == "item1"

    def test_get_nonexistent_item(self, cart):
        assert cart.get_item("item999") is None

    def test_get_items_by_price_range(self, cart):
        items = cart.get_items_by_price_range(20.0, 60.0)
        assert len(items) == 1
        assert items[0].item_id == "item2"

    def test_get_items_by_price_range_inclusive(self, cart):
        items = cart.get_items_by_price_range(10.0, 50.0)
        assert len(items) == 2

    def test_get_items_by_price_range_no_matches(self, cart):
        items = cart.get_items_by_price_range(200.0, 300.0)
        assert len(items) == 0

    def test_get_items_negative_min_raises(self, cart):
        with pytest.raises(ValueError, match="cannot be negative"):
            cart.get_items_by_price_range(-10.0, 50.0)

    def test_get_items_min_greater_than_max_raises(self, cart):
        with pytest.raises(ValueError, match="Min price cannot be greater"):
            cart.get_items_by_price_range(100.0, 50.0)


# =============================================================================
# ShoppingCart summary
# =============================================================================

class TestShoppingCartSummary:
    def test_summary_with_items(self):
        cart = ShoppingCart(tax_rate=0.10)
        cart.add_item(Item("item1", "P1", 50.0, 2))
        cart.add_item(Item("item2", "P2", 30.0, 1))
        cart.apply_discount("SAVE10", 10)
        cart.apply_loyalty_points(25)
        summary = cart.get_summary()
        assert summary['item_count'] == 3
        assert summary['unique_items'] == 2
        assert summary['subtotal'] == 130.0
        assert summary['discount'] == 13.0
        assert summary['tax'] == 11.7
        assert summary['total'] == 128.7
        assert summary['loyalty_points'] == 25

    def test_summary_empty_cart(self):
        cart = ShoppingCart()
        summary = cart.get_summary()
        assert summary['item_count'] == 0
        assert summary['unique_items'] == 0
        assert summary['subtotal'] == 0.0
        assert summary['discount'] == 0.0
        assert summary['tax'] == 0.0
        assert summary['total'] == 0.0
        assert summary['loyalty_points'] == 0
