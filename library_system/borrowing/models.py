from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

FINE_PER_DAY = Decimal('2.00')  # ETB 2 per overdue day (requirement: days × 2 birr)


class BorrowRecord(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrow_records'
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='borrow_records'
    )
    borrowed_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    fine_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='issued_records'
    )

    class Meta:
        ordering = ['-borrowed_date']

    def __str__(self):
        return f"{self.member.username} – {self.book.title} ({self.status})"

    def calculate_fine(self):
        """Calculate fine based on overdue days."""
        if self.status == 'returned' and self.returned_date:
            if self.returned_date > self.due_date:
                days = (self.returned_date - self.due_date).days
                return FINE_PER_DAY * days
        elif self.status in ('borrowed', 'overdue'):
            today = timezone.now().date()
            if today > self.due_date:
                days = (today - self.due_date).days
                return FINE_PER_DAY * days
        return Decimal('0.00')

    @property
    def is_overdue(self):
        if self.status == 'returned':
            return False
        return timezone.now().date() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    @property
    def days_until_due(self):
        if self.status != 'borrowed':
            return 0
        delta = self.due_date - timezone.now().date()
        return delta.days

    @property
    def is_due_soon(self):
        """True if borrowed and due within 3 days (but not overdue)."""
        return self.status == 'borrowed' and 0 <= self.days_until_due <= 3


class Reservation(models.Model):
    """Student reserves a book that is currently unavailable."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ready', 'Ready for Pickup'),
        ('cancelled', 'Cancelled'),
        ('fulfilled', 'Fulfilled'),
    ]
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    reserved_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-reserved_at']
        unique_together = [('member', 'book', 'status')]

    def __str__(self):
        return f"{self.member.username} reserved {self.book.title} ({self.status})"
