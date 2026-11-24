from django.test import TestCase
from django.urls import reverse

from .models import Profile


class AccountFlowTests(TestCase):
    def test_confirm_password_guidance_is_a_placeholder(self):
        response = self.client.get(reverse('register'))

        self.assertContains(
            response,
            'placeholder="Use at least 8 characters with letters and numbers."',
        )

    def test_registration_creates_account_profile_and_session(self):
        response = self.client.post(reverse('register'), {
            'username': 'forest_user',
            'password1': 'ForestTrail246!',
            'password2': 'ForestTrail246!',
            'contact': 'forest@example.com',
        })

        self.assertRedirects(response, reverse('home'))
        self.assertEqual(Profile.objects.get().contact, 'forest@example.com')
        self.assertIn('_auth_user_id', self.client.session)

    def test_duplicate_contact_is_rejected(self):
        self.client.post(reverse('register'), {
            'username': 'first_user',
            'password1': 'ForestTrail246!',
            'password2': 'ForestTrail246!',
            'contact': 'forest@example.com',
        })
        self.client.post(reverse('logout'))

        response = self.client.post(reverse('register'), {
            'username': 'second_user',
            'password1': 'ForestTrail246!',
            'password2': 'ForestTrail246!',
            'contact': 'forest@example.com',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account already uses this contact.')
        self.assertEqual(Profile.objects.count(), 1)

    def test_password_must_include_letters_and_numbers(self):
        response = self.client.post(reverse('register'), {
            'username': 'forest_user',
            'password1': 'onlyletters',
            'password2': 'onlyletters',
            'contact': 'forest@example.com',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password must include both letters and numbers.')
        self.assertEqual(Profile.objects.count(), 0)

    def test_login_and_logout(self):
        self.client.post(reverse('register'), {
            'username': 'forest_user',
            'password1': 'ForestTrail246!',
            'password2': 'ForestTrail246!',
            'contact': '+1 (555) 123-4567',
        })
        self.client.post(reverse('logout'))

        response = self.client.post(reverse('login'), {
            'username': 'forest_user',
            'password': 'ForestTrail246!',
        })

        self.assertRedirects(response, reverse('home'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_home_requires_authentication(self):
        response = self.client.get(reverse('home'))

        self.assertRedirects(response, '/?next=/home/')
