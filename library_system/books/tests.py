"""
Unit tests for the books app.
Run with: python manage.py test books
"""
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from .models import Book, Category, BookReview


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


class BookModelTest(TestCase):

    def test_is_available_true_when_copies_exist(self):
        book = make_book(copies=2)
        self.assertTrue(book.is_available)

    def test_is_available_false_when_no_copies(self):
        book = make_book(copies=0)
        self.assertFalse(book.is_available)

    def test_is_available_false_when_status_not_available(self):
        book = make_book(copies=2)
        book.status = 'borrowed'
        book.save()
        self.assertFalse(book.is_available)

    def test_avg_rating_none_when_no_reviews(self):
        book = make_book()
        self.assertIsNone(book.avg_rating)

    def test_avg_rating_calculated_correctly(self):
        book = make_book()
        u1 = make_user('rater1')
        u2 = make_user('rater2')
        BookReview.objects.create(book=book, user=u1, rating=4)
        BookReview.objects.create(book=book, user=u2, rating=2)
        self.assertEqual(book.avg_rating, 3.0)

    def test_review_count(self):
        book = make_book()
        u1 = make_user('rev1')
        BookReview.objects.create(book=book, user=u1, rating=5)
        self.assertEqual(book.review_count, 1)


class BookReviewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = make_user('reviewer')
        self.book = make_book()

    def test_student_cannot_review_without_borrowing(self):
        self.client.login(username='reviewer', password='Test1234!')
        response = self.client.post(
            reverse('submit_review', kwargs={'pk': self.book.pk}),
            {'rating': '5', 'comment': 'Great book'}
        )
        # Should redirect but NOT create a review
        self.assertEqual(BookReview.objects.count(), 0)

    def test_student_can_review_after_borrowing(self):
        from borrowing.models import BorrowRecord
        from django.utils import timezone
        from datetime import timedelta
        BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=timezone.now().date() + timedelta(days=14),
            status='returned',
            returned_date=timezone.now().date(),
        )
        self.client.login(username='reviewer', password='Test1234!')
        self.client.post(
            reverse('submit_review', kwargs={'pk': self.book.pk}),
            {'rating': '4', 'comment': 'Good read'}
        )
        self.assertEqual(BookReview.objects.count(), 1)
        review = BookReview.objects.first()
        self.assertEqual(review.rating, 4)

    def test_duplicate_review_updates_existing(self):
        from borrowing.models import BorrowRecord
        from django.utils import timezone
        from datetime import timedelta
        BorrowRecord.objects.create(
            member=self.student, book=self.book,
            due_date=timezone.now().date() + timedelta(days=14),
            status='returned',
            returned_date=timezone.now().date(),
        )
        self.client.login(username='reviewer', password='Test1234!')
        self.client.post(reverse('submit_review', kwargs={'pk': self.book.pk}), {'rating': '3'})
        self.client.post(reverse('submit_review', kwargs={'pk': self.book.pk}), {'rating': '5'})
        # Should still be only 1 review (updated)
        self.assertEqual(BookReview.objects.count(), 1)
        self.assertEqual(BookReview.objects.first().rating, 5)


class BookSearchTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user('searcher')
        self.client.login(username='searcher', password='Test1234!')
        cat, _ = Category.objects.get_or_create(name='Fiction')
        Book.objects.create(title='Django Basics', author='Alice', category=cat,
                            total_copies=1, available_copies=1, status='available')
        Book.objects.create(title='Python Advanced', author='Bob', category=cat,
                            total_copies=1, available_copies=0, status='borrowed')

    def test_search_by_title(self):
        response = self.client.get(reverse('book_list'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Basics')
        self.assertNotContains(response, 'Python Advanced')

    def test_search_by_author(self):
        response = self.client.get(reverse('book_list'), {'author': 'Bob'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python Advanced')
        self.assertNotContains(response, 'Django Basics')

    def test_filter_available_only(self):
        response = self.client.get(reverse('book_list'), {'availability': 'available'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Basics')
        self.assertNotContains(response, 'Python Advanced')
