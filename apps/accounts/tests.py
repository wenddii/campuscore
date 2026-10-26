from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class OwnerAuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner",
            password="correct-password",
            is_staff=True,
        )

    def test_invalid_login_is_rejected(self):
        response = self.client.post(
            reverse("login"),
            {"username": "owner", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password")

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("login"),
            {"username": "owner", "password": "correct-password"},
        )
        self.assertRedirects(response, reverse("students:dashboard"))

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("students:dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('students:dashboard')}",
        )

    def test_logout_requires_post_and_redirects_to_login(self):
        self.client.force_login(self.user)
        get_response = self.client.get(reverse("logout"))
        self.assertEqual(get_response.status_code, 405)
        post_response = self.client.post(reverse("logout"))
        self.assertRedirects(post_response, reverse("login"))
