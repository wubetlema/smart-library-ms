"""
Management command: send email reminders for books due in 1-3 days.
Run daily via cron or Windows Task Scheduler:
    python manage.py send_due_reminders
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from borrowing.models import BorrowRecord
from activity.utils import log_action


class Command(BaseCommand):
    help = 'Send email reminders for books due within 3 days'

    def handle(self, *args, **options):
        today = timezone.now().date()
        soon = today + timedelta(days=3)

        # Due soon (not yet overdue)
        due_soon = BorrowRecord.objects.filter(
            status='borrowed',
            due_date__gte=today,
            due_date__lte=soon,
        ).select_related('member', 'book')

        sent = 0
        for record in due_soon:
            if not record.member.email:
                continue
            days_left = (record.due_date - today).days
            subject = f'[LibraryMS] Reminder: "{record.book.title}" due in {days_left} day(s)'
            message = (
                f'Dear {record.member.get_full_name() or record.member.username},\n\n'
                f'This is a reminder that the book "{record.book.title}" '
                f'is due on {record.due_date} ({days_left} day(s) from today).\n\n'
                f'Please return it on time to avoid a fine of ETB {settings.FINE_PER_DAY}/day.\n\n'
                f'Thank you,\nLibrary Management System'
            )
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [record.member.email])
                sent += 1
            except Exception as e:
                self.stderr.write(f'Failed to send to {record.member.email}: {e}')

        # Overdue reminders
        overdue = BorrowRecord.objects.filter(status='overdue').select_related('member', 'book')
        for record in overdue:
            if not record.member.email:
                continue
            fine = record.calculate_fine()
            subject = f'[LibraryMS] OVERDUE: "{record.book.title}" – Fine: ETB {fine}'
            message = (
                f'Dear {record.member.get_full_name() or record.member.username},\n\n'
                f'The book "{record.book.title}" was due on {record.due_date} '
                f'and is now {record.days_overdue} day(s) overdue.\n\n'
                f'Current fine: ETB {fine}\n\n'
                f'Please return the book immediately.\n\n'
                f'Library Management System'
            )
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [record.member.email])
                sent += 1
            except Exception as e:
                self.stderr.write(f'Failed to send to {record.member.email}: {e}')

        self.stdout.write(self.style.SUCCESS(f'Sent {sent} reminder email(s).'))
