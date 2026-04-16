"""
Unit tests for the accounts app.
Run with: python manage.py test accounts
"""
from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser


class RegistrationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('register')

    def test_register_creates_student_account(self):
        response = self.client.post(self.url, {
            'username': 'newstudent',
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'new@test.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(CustomUser.objects.filter(username='newstudent').count(), 1)
        user = CustomUser.objects.get(username='newstudent')
        self.assertEqual(user.role, 'student')

    def test_register_redirects_to_dashboard_on_success(self):
        response = self.client.post(self.url, {
            'username': 'student2',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test2@test.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_register_fails_with_mismatched_passwords(self):
        self.client.post(self.url, {
            'username': 'baduser',
            'email': 'bad@test.com',
            'password1': 'SecurePass123!',
            'password2': 'WrongPass456!',
        })
        self.assertEqual(CustomUser.objects.filter(username='baduser').count(), 0)

    def test_register_fails_with_duplicate_username(self):
        CustomUser.objects.create_user(username='existing', password='Pass123!')
        response = self.client.post(self.url, {
            'username': 'existing',
            'email': 'dup@test.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(CustomUser.objects.filter(username='existing').count(), 1)


class LoginTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('login')
        self.user = CustomUser.objects.create_user(
            username='loginuser', password='Test1234!',
            email='login@test.com', role='student', is_approved=True
        )

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post(self.url, {
            'username': 'loginuser',
            'password': 'Test1234!',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(self.url, {
            'username': 'loginuser',
            'password': 'WrongPass!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_blocked_for_unapproved_user(self):
        self.user.is_approved = False
        self.user.save()
        response = self.client.post(self.url, {
            'username': 'loginuser',
            'password': 'Test1234!',
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_authenticated_user_redirected_away_from_login(self):
        self.client.login(username='loginuser', password='Test1234!')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('dashboard'))


class ProfileTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='profuser', password='Test1234!',
            email='prof@test.com', role='student', is_approved=True
        )
        self.client.login(username='profuser', password='Test1234!')

    def test_profile_page_loads(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_update_saves_correctly(self):
        self.client.post(reverse('profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@test.com',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_unauthenticated_profile_redirects(self):
        self.client.logout()
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)


class RoleModelTest(TestCase):

    def test_admin_property(self):
        u = CustomUser(role='admin')
        self.assertTrue(u.is_admin)
        self.assertFalse(u.is_librarian)
        self.assertFalse(u.is_student)

    def test_librarian_property(self):
        u = CustomUser(role='librarian')
        self.assertTrue(u.is_librarian)

    def test_student_property(self):
        u = CustomUser(role='student')
        self.assertTrue(u.is_student)
