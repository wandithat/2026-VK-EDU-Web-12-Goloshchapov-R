from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class ProfileTests(TestCase):
    def test_profile_is_one_to_one_with_user(self):
        user = get_user_model().objects.create_user(username='profile-user', password='test-password')
        profile = Profile.objects.create(user=user)
        self.assertEqual(user.profile, profile)


class AuthenticationViewsTests(TestCase):
    def test_signup_creates_user_and_logs_them_in(self):
        response = self.client.post(reverse('signup'), {
            'login': 'new-user',
            'email': 'new@example.com',
            'password': 'Strong-password-123',
            'password_repeat': 'Strong-password-123',
        })
        user = get_user_model().objects.get(username='new-user')
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_authenticated_user_can_open_signup_to_create_another_account(self):
        existing = get_user_model().objects.create_user(username='existing', password='test-password')
        self.client.force_login(existing)
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_login_authenticates_user(self):
        get_user_model().objects.create_user(username='login-user', password='Strong-password-123')
        response = self.client.post(reverse('login'), {'login': 'login-user', 'password': 'Strong-password-123'})
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
