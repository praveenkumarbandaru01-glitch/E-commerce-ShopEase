from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from product.models import Category, Product
from .models import CartItem, WishlistItem


class CartAndWishlistTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="shopper",
            password="test-password-123",
        )
        category = Category.objects.create(name="Accessories")
        cls.product = Product.objects.create(
            name="Canvas bag",
            category=category,
            price="25.00",
            stock=2,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_add_to_cart_and_update_quantity(self):
        response = self.client.post(
            reverse("add_to_cart", args=[self.product.pk])
        )

        self.assertRedirects(response, reverse("cart"))
        item = CartItem.objects.get(user=self.user, product=self.product)
        self.assertEqual(item.quantity, 1)

        response = self.client.post(
            reverse("update_cart_item", args=[item.pk]),
            {"quantity": "2"},
        )

        self.assertRedirects(response, reverse("cart"))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        self.assertContains(self.client.get(reverse("cart")), "₹50.00")

    def test_cart_quantity_cannot_exceed_stock(self):
        item = CartItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=1,
        )

        self.client.post(
            reverse("update_cart_item", args=[item.pk]),
            {"quantity": "3"},
        )

        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_wishlist_add_is_idempotent_and_remove_works(self):
        url = reverse("add_to_wishlist", args=[self.product.pk])
        self.client.post(url)
        self.client.post(url)

        self.assertEqual(
            WishlistItem.objects.filter(
                user=self.user,
                product=self.product,
            ).count(),
            1,
        )

        item = WishlistItem.objects.get(user=self.user, product=self.product)
        response = self.client.post(
            reverse("remove_wishlist_item", args=[item.pk])
        )

        self.assertRedirects(response, reverse("wishlist"))
        self.assertFalse(WishlistItem.objects.filter(pk=item.pk).exists())

    def test_cart_and_wishlist_require_login(self):
        self.client.logout()

        self.assertEqual(self.client.get(reverse("cart")).status_code, 302)
        self.assertEqual(self.client.get(reverse("wishlist")).status_code, 302)
