from django.test import TestCase
from django.urls import reverse
from .models import Category, Product


class StorefrontTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.electronics = Category.objects.create(name="Electronics")
        cls.books = Category.objects.create(name="Books")
        Product.objects.create(
            name="Headphones",
            category=cls.electronics,
            description="Wireless audio",
            price="49.99",
            stock=8,
        )
        Product.objects.create(
            name="Novel",
            category=cls.books,
            description="A mystery story",
            price="12.50",
            stock=3,
        )
        Product.objects.create(
            name="Unavailable tablet",
            category=cls.electronics,
            price="99.00",
            stock=0,
        )

    def test_dashboard_shows_catalog_and_stock_counts(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Headphones")
        self.assertContains(response, "Electronics")
        self.assertEqual(response.context["total_products"], 3)
        self.assertEqual(response.context["available_products"], 2)
        self.assertEqual(response.context["low_stock"], 1)

    def test_category_and_search_filters_can_be_combined(self):
        response = self.client.get(
            reverse("dashboard"),
            {"category": "Electronics", "q": "wireless"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Headphones")
        self.assertNotContains(response, "Unavailable tablet")
        self.assertNotContains(response, "Novel")

    def test_product_detail_lists_other_products_in_its_category(self):
        response = self.client.get(
            reverse("product_detail", args=[self.electronics.products.first().pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "More from Electronics")
        self.assertContains(response, "Unavailable tablet")
        self.assertContains(response, "Add to cart")
