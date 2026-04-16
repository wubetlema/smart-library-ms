"""
Unit tests for the borrowing app.
Run with: python manage.py test borrowing
"""
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from books.models import Book, Category
from .models import BorrowRecord


def make_user(username, role='student', password='Test1234!'):
    return CustomUser.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com', role=role, is_approved=True
    )


def make_book(title='Test Book', copies=2):
    cat, _ = Category.objects.get_or_create(name='Test Category')
    return Book.objects.create(
        title=title, author='Test Author',
        category=cat, total_copies=copies,
        available_copies=copies, status='available'
    )


class FineCalculationTest(TestCase):
    """Test BorrowRecord.calculate_fine() business logic."""

    def setUp(self):
        self.student = make_user('student1')
        self.book = make_book()

    def test_no_fine_when_returned_on_time(self):
        today = timezone.now().date()
        rec = BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=today + timedelta(days=1),
            status='returned',
            returned_date=today,
        )
        self.assertEqual(rec.calculate_fine(), Decimal('0.00'))

    def test_fine_calculated_correctly_for_overdue(self):
        today = timezone.now().date()
        rec = BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=today - timedelta(days=3),
            status='overdue',
        )
        self.assertEqual(rec.calculate_fine(), Decimal('15.00'))  # 3 days * ETB 5

    def test_fine_on_late_return(self):
        due = date(2026, 1, 1)
        returned = date(2026, 1, 6)  # 5 days late
        rec = BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=due, status='returned',
            returned_date=returned,
        )
        self.assertEqual(rec.calculate_fine(), Decimal('25.00'))  # 5 * 5

    def test_no_fine_when_not_overdue(self):
        today = timezone.now().date()
        rec = BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=today + timedelta(days=5),
            status='borrowed',
        )
        self.assertEqual(rec.calculate_fine(), Decimal('0.00'))


class BorrowLimitTest(TestCase):
    """Test student borrow limit enforcement."""

    def setUp(self):
        self.client = Client()
        self.student = make_user('student2')
        self.client.login(username='student2', password='Test1234!')

    def test_student_cannot_exceed_borrow_limit(self):
        from django.conf import settings
        limit = getattr(settings, 'MAX_BORROW_LIMIT', 3)
        today = timezone.now().date()
        # Create books up to the limit
        for i in range(limit):
            book = make_book(f'Book {i}')
            BorrowRecord.objects.create(
                member=self.student, book=book,
                due_date=today + timedelta(days=14),
                status='borrowed',
            )
        # Try to borrow one more
        extra_book = make_book('Extra Book')
        url = reverse('student_borrow', kwargs={'book_id': extra_book.pk})
        response = self.client.post(url)
        # Should redirect back with error, not create a new record
        active = BorrowRecord.objects.filter(
            member=self.student, status__in=['borrowed', 'overdue']
        ).count()
        self.assertEqual(active, limit)


class RoleAccessTest(TestCase):
    """Test role-based access control."""

    def setUp(self):
        self.client = Client()
        self.student = make_user('stu', role='student')
        self.librarian = make_user('lib', role='librarian')
        self.admin = make_user('adm', role='admin')

    def test_student_cannot_access_borrow_list(self):
        self.client.login(username='stu', password='Test1234!')
        response = self.client.get(reverse('borrow_list'))
        self.assertNotEqual(response.status_code, 200)

    def test_librarian_can_access_borrow_list(self):
        self.client.login(username='lib', password='Test1234!')
        response = self.client.get(reverse('borrow_list'))
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_admin_dashboard(self):
        self.client.login(username='stu', password='Test1234!')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_unauthenticated_redirects_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/accounts/login/?next=/accounts/dashboard/')


class IsDueSoonTest(TestCase):
    """Test BorrowRecord.is_due_soon property."""

    def setUp(self):
        self.student = make_user('student3')
        self.book = make_book()

    def test_due_soon_within_3_days(self):
        today = timezone.now().date()
        rec = BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=today + timedelta(days=2),
            status='borrowed',
        )
        self.assertTrue(rec.is_due_soon)

    def test_not_due_soon_when_4_days_away(self):
        today = timezone.now().date()
        rec = BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=today + timedelta(days=4),
            status='borrowed',
        )
        self.assertFalse(rec.is_due_soon)

    def test_not_due_soon_when_overdue(self):
        today = timezone.now().date()
        rec = BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=today - timedelta(days=1),
            status='overdue',
        )
        self.assertFalse(rec.is_due_soon)
