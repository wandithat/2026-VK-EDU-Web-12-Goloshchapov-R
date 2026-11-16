from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import Profile


class ProfileTests(TestCase):
    def test_profile_is_one_to_one_with_user(self):
        user = get_user_model().objects.create_user(username='profile-user', password='test-password')
        self.assertEqual(user.profile.user, user)

    def test_profile_form_updates_user_and_nickname(self):
        user = get_user_model().objects.create_user(username='profile-user', password='test-password')
        self.client.force_login(user)
        response = self.client.post(reverse('profile'), {
            'login': 'new-login',
            'email': 'new@example.com',
            'name': 'New Name',
            'nickname': 'New Nick',
        })
        self.assertRedirects(response, reverse('profile'))
        user.refresh_from_db()
        self.assertEqual(user.username, 'new-login')
        self.assertEqual(user.email, 'new@example.com')
        self.assertEqual(user.profile.nickname, 'New Nick')

    def test_profile_requires_authentication(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_avatar_is_saved_with_unpredictable_name(self):
        user = get_user_model().objects.create_user(username='avatar-user', password='test-password')
        self.client.force_login(user)
        image = Image.new('RGB', (2, 2), color='white')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        avatar = SimpleUploadedFile('avatar.png', buffer.getvalue(), content_type='image/png')
        response = self.client.post(reverse('profile'), {
            'login': user.username,
            'email': 'avatar@example.com',
            'name': '',
            'nickname': 'Avatar User',
            'avatar': avatar,
        })
        self.assertRedirects(response, reverse('profile'))
        user.refresh_from_db()
        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile.avatar)
        self.assertTrue(profile.avatar.name.startswith('avatars/'))
        self.assertNotEqual(profile.avatar.name, 'avatars/avatar.png')


class AuthenticationViewsTests(TestCase):
    def test_signup_creates_user_profile_and_logs_them_in(self):
        response = self.client.post(reverse('signup'), {
            'login': 'new-user',
            'email': 'new@example.com',
            'name': 'New User',
            'password': 'Strong-password-123',
            'password_repeat': 'Strong-password-123',
        })
        user = get_user_model().objects.get(username='new-user')
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(user.first_name, 'New User')

    def test_signup_shows_password_validator_errors(self):
        response = self.client.post(reverse('signup'), {
            'login': 'weak-user',
            'email': 'weak@example.com',
            'name': 'Weak User',
            'password': '123',
            'password_repeat': '123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors['password'])
        self.assertFalse(get_user_model().objects.filter(username='weak-user').exists())

    def test_authenticated_user_can_open_signup(self):
        existing = get_user_model().objects.create_user(username='existing', password='test-password')
        self.client.force_login(existing)
        self.assertEqual(self.client.get(reverse('signup')).status_code, 200)

    def test_login_authenticates_user(self):
        get_user_model().objects.create_user(username='login-user', password='Strong-password-123')
        response = self.client.post(reverse('login'), {'login': 'login-user', 'password': 'Strong-password-123'})
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_redirects_to_safe_next(self):
        get_user_model().objects.create_user(username='login-user', password='Strong-password-123')
        response = self.client.post(
            f"{reverse('login')}?next=/hot/",
            {'login': 'login-user', 'password': 'Strong-password-123', 'next': '/hot/'},
        )
        self.assertRedirects(response, '/hot/')

    def test_login_rejects_external_next(self):
        get_user_model().objects.create_user(username='login-user', password='Strong-password-123')
        response = self.client.post(
            reverse('login'),
            {'login': 'login-user', 'password': 'Strong-password-123', 'next': 'https://evil.example/'},
        )
        self.assertRedirects(response, reverse('index'))

    def test_logout_returns_to_referer(self):
        user = get_user_model().objects.create_user(username='logout-user', password='test-password')
        self.client.force_login(user)
        response = self.client.post(reverse('logout'), HTTP_REFERER='/hot/')
        self.assertRedirects(response, '/hot/')
        self.assertNotIn('_auth_user_id', self.client.session)
