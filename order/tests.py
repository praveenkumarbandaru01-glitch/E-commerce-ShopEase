from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from carts.models import CartItem
from product.models import Category, Product
from .models import Order, OrderItem


class CheckoutAndOrderTrackingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="buyer",
            password="test-password-123",
        )
        cls.other_user = get_user_model().objects.create_user(
            username="other-buyer",
            password="test-password-123",
        )
        category = Category.objects.create(name="Home")
        cls.product = Product.objects.create(
            name="Desk lamp",
            category=category,
            price="45.00",
            stock=5,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def add_item_to_cart(self, quantity=2):
        CartItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=quantity,
        )

    def test_checkout_get_displays_cash_on_delivery(self):
        self.add_item_to_cart()

        response = self.client.get(reverse("checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cash on delivery")
        self.assertContains(response, "Pay in cash when your order arrives")

    def test_checkout_creates_order_and_reserves_stock(self):
        self.add_item_to_cart(quantity=2)

        response = self.client.post(
            reverse("checkout"),
            {
                "shipping_address": "12 Market Street, Springfield",
                "payment_method": Order.PaymentMethod.CASH_ON_DELIVERY,
            },
        )

        order = Order.objects.get(user=self.user)
        self.assertRedirects(
            response,
            reverse("order_detail", args=[order.pk]),
        )
        self.assertEqual(order.status, Order.Status.PLACED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.DUE)
        self.assertEqual(order.payment_method, Order.PaymentMethod.CASH_ON_DELIVERY)
        self.assertEqual(order.total, self.product.price * 2)
        self.assertEqual(order.items.get().product_name, "Desk lamp")
        self.assertEqual(order.items.get().unit_price, self.product.price)
        self.assertFalse(CartItem.objects.filter(user=self.user).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_checkout_rejects_non_cod_payment_and_missing_address(self):
        self.add_item_to_cart()

        response = self.client.post(
            reverse("checkout"),
            {"shipping_address": "Somewhere", "payment_method": "card"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())

        response = self.client.post(
            reverse("checkout"),
            {
                "shipping_address": "",
                "payment_method": Order.PaymentMethod.CASH_ON_DELIVERY,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())

    def test_checkout_rejects_stock_changes_without_partial_order(self):
        self.add_item_to_cart(quantity=6)

        response = self.client.post(
            reverse("checkout"),
            {
                "shipping_address": "12 Market Street",
                "payment_method": Order.PaymentMethod.CASH_ON_DELIVERY,
            },
        )

        self.assertRedirects(response, reverse("cart"))
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertTrue(CartItem.objects.filter(user=self.user).exists())

    def test_order_tracking_shows_status_and_items(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address="12 Market Street",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=1,
            unit_price=self.product.price,
        )

        response = self.client.get(reverse("order_detail", args=[order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order placed")
        self.assertContains(response, "Desk lamp")
        self.assertContains(response, "Cash on delivery")

    def test_customers_cannot_view_another_users_order(self):
        order = Order.objects.create(
            user=self.other_user,
            shipping_address="Private address",
        )

        response = self.client.get(reverse("order_detail", args=[order.pk]))

        self.assertEqual(response.status_code, 404)

    def test_cancelling_eligible_order_restocks_products(self):
        order = Order.objects.create(
            user=self.user,
            shipping_address="12 Market Street",
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=2,
            unit_price=self.product.price,
        )
        self.product.stock = 3
        self.product.save(update_fields=["stock"])

        response = self.client.post(reverse("cancel_order", args=[order.pk]))

        self.assertRedirects(response, reverse("order_detail", args=[order.pk]))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.stock, 5)
