# Portfolio\Education_Villa\edu_core\tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import UserProfile

# Create your tests here.


# Get the custom user model
User = get_user_model()

class UserViewsTest(TestCase):
    def setUp(self):
        # Create a test user using the custom user model
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client = Client()

    def test_signup_view_get(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edu_core/user/signup.html')

    def test_signup_view_post(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_profile_view_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edu_core/user/profile.html')

    def test_profile_view_unauthenticated(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_edit_profile_get_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edu_core/user/edit_profile.html')

    def test_edit_profile_post_authenticated(self):
        self.client.login(username='testuser', password='password123')
        profile = UserProfile.objects.get(user=self.user)
        response = self.client.post(reverse('edit_profile'), {
            'bio': 'Updated bio text',
            'profile_form': 'profile_form'
        })
        self.assertEqual(response.status_code, 302)  # Should redirect to profile
        profile.refresh_from_db()
        self.assertEqual(profile.bio, 'Updated bio text')