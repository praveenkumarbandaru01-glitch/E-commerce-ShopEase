from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="shopper",
            password="test-password-123",
            email="shopper@example.com",
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('profile')}",
        )

    def test_profile_can_update_account_details(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("profile"),
            {
                "username": "shopper",
                "first_name": "Alex",
                "last_name": "Shopper",
                "email": "alex@example.com",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alex")
        self.assertEqual(self.user.last_name, "Shopper")
        self.assertEqual(self.user.email, "alex@example.com")
