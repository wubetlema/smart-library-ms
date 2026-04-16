from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.http import HttpResponse
from decimal import Decimal
import csv
import io

from accounts.decorators import role_required
from accounts.models import CustomUser
from books.models import Book
from .models import BorrowRecord, Reservation
from .forms import BorrowForm, ReturnForm
from activity.utils import log_action


# ── Borrow ────────────────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def borrow_book_view(request, book_id=None, member_id=None):
    initial = {}
    if book_id:
        book = get_object_or_404(Book, pk=book_id)
        initial['book'] = book
    if member_id:
        member = get_object_or_404(CustomUser, pk=member_id)
        initial['member'] = member

    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.issued_by = request.user
            record.status = 'borrowed'
            record.save()
            book = record.book
            book.available_copies = max(0, book.available_copies - 1)
            if book.available_copies == 0:
                book.status = 'borrowed'
            book.save()
            log_action(request.user, 'BORROW',
                       f'Issued "{book.title}" to {record.member.username}', request)
            messages.success(request, f'"{book.title}" borrowed by {record.member.get_full_name() or record.member.username}.')
            # Notify the student
            from activity.utils import notify
            notify(record.member, 'Book Issued',
                   f'"{book.title}" has been issued to you. Due: {record.due_date}',
                   type='success', link=f'/books/{book.pk}/')
            return redirect('borrow_list')
    else:
        form = BorrowForm(initial=initial)
    return render(request, 'borrowing/borrow_form.html', {'form': form, 'title': 'Borrow Book'})


@login_required
def student_borrow_view(request, book_id):
    """Allow a student to borrow a book directly."""
    from django.conf import settings as django_settings
    book = get_object_or_404(Book, pk=book_id)

    if request.user.role not in ('student',):
        return redirect('borrow_book_for', book_id=book_id)

    # Check borrow limit
    max_limit = getattr(django_settings, 'MAX_BORROW_LIMIT', 3)
    active_count = BorrowRecord.objects.filter(
        member=request.user, status__in=['borrowed', 'overdue']
    ).count()
    if active_count >= max_limit:
        messages.error(request, f'You have reached the maximum borrow limit of {max_limit} books. Please return a book before borrowing another.')
        return redirect('book_detail', pk=book_id)

    # Check already borrowed this book
    already = BorrowRecord.objects.filter(
        member=request.user, book=book, status__in=['borrowed', 'overdue']
    ).exists()
    if already:
        messages.warning(request, f'You already have "{book.title}" borrowed.')
        return redirect('book_detail', pk=book_id)

    if not book.is_available:
        messages.error(request, f'"{book.title}" is not available right now.')
        return redirect('book_detail', pk=book_id)

    if request.method == 'POST':
        from datetime import timedelta
        due_date = timezone.now().date() + timedelta(days=7)  # 7-day due date
        record = BorrowRecord.objects.create(
            member=request.user,
            book=book,
            due_date=due_date,
            status='borrowed',
            issued_by=None,
        )
        book.available_copies = max(0, book.available_copies - 1)
        if book.available_copies == 0:
            book.status = 'borrowed'
        book.save()
        log_action(request.user, 'BORROW', f'Borrowed "{book.title}"', request)
        messages.success(request, f'You borrowed "{book.title}". Due: {due_date}')
        return redirect('book_detail', pk=book_id)

    return render(request, 'borrowing/student_borrow_confirm.html', {'book': book})


@login_required
@role_required('admin', 'librarian')
def return_book_view(request, pk):
    from django.shortcuts import get_object_or_404
    # Try to get the record regardless of status first
    try:
        record = BorrowRecord.objects.get(pk=pk)
    except BorrowRecord.DoesNotExist:
        messages.error(request, 'Borrow record not found.')
        return redirect('borrow_list')

    if record.status == 'returned':
        messages.warning(request, f'"{record.book.title}" has already been returned.')
        return redirect('borrow_list')

    fine = record.calculate_fine()

    if request.method == 'POST':
        form = ReturnForm(request.POST, instance=record)
        if form.is_valid():
            ret = form.save(commit=False)
            ret.status = 'returned'
            ret.fine_amount = fine
            ret.save()
            # Restore available copies
            book = record.book
            book.available_copies += 1
            if book.status == 'borrowed' and book.available_copies > 0:
                book.status = 'available'
            book.save()

            # Notify students with pending reservations
            from .models import Reservation
            pending_res = Reservation.objects.filter(
                book=book, status='pending'
            ).select_related('member').first()
            if pending_res:
                pending_res.status = 'ready'
                pending_res.save()
                # Send email notification
                from django.core.mail import send_mail
                from django.conf import settings as django_settings
                if pending_res.member.email:
                    try:
                        send_mail(
                            f'[Smart Library] "{book.title}" is now available!',
                            f'Dear {pending_res.member.get_full_name() or pending_res.member.username},\n\n'
                            f'Good news! The book "{book.title}" you reserved is now available for pickup.\n\n'
                            f'Please visit the library within 3 days to borrow it.\n\n'
                            f'Smart Library',
                            django_settings.DEFAULT_FROM_EMAIL,
                            [pending_res.member.email],
                            fail_silently=True,
                        )
                    except Exception:
                        pass
            log_action(request.user, 'RETURN',
                       f'Returned "{record.book.title}" from {record.member.username}. Fine: ETB {fine}', request)
            messages.success(request, f'"{record.book.title}" returned. Fine: ETB {fine}')
            # Notify the student
            from activity.utils import notify
            if fine > 0:
                notify(record.member, 'Book Returned – Fine Applied',
                       f'"{record.book.title}" returned. Fine: ETB {fine}',
                       type='warning', link='/borrow/my/')
            else:
                notify(record.member, 'Book Returned',
                       f'"{record.book.title}" returned on time. No fine.',
                       type='success', link='/borrow/my/')
            return redirect('borrow_list')
    else:
        form = ReturnForm(instance=record)
    return render(request, 'borrowing/return_form.html', {
        'form': form, 'record': record, 'fine': fine
    })


# ── Lists ─────────────────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def borrow_list_view(request):
    records = BorrowRecord.objects.select_related('member', 'book').all()

    status_filter = request.GET.get('status', '')
    q = request.GET.get('q', '')
    if status_filter:
        records = records.filter(status=status_filter)
    if q:
        records = records.filter(
            Q(member__username__icontains=q) |
            Q(member__first_name__icontains=q) |
            Q(member__last_name__icontains=q) |
            Q(book__title__icontains=q)
        )

    # Auto-mark overdue
    today = timezone.now().date()
    records.filter(status='borrowed', due_date__lt=today).update(status='overdue')

    paginator = Paginator(records, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'borrowing/borrow_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'q': q,
    })


@login_required
def my_borrowings_view(request):
    """Student's own borrowing history."""
    today = timezone.now().date()
    records = BorrowRecord.objects.filter(member=request.user).select_related('book')
    # auto-mark overdue
    records.filter(status='borrowed', due_date__lt=today).update(status='overdue')
    # refresh queryset after update
    records = BorrowRecord.objects.filter(member=request.user).select_related('book')

    total_count    = records.count()
    active_count   = records.filter(status__in=['borrowed', 'overdue']).count()
    overdue_count  = records.filter(status='overdue').count()
    returned_count = records.filter(status='returned').count()
    # due within 3 days (not overdue)
    from datetime import timedelta
    due_soon_count = records.filter(
        status='borrowed',
        due_date__gte=today,
        due_date__lte=today + timedelta(days=3)
    ).count()

    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'borrowing/my_borrowings.html', {
        'page_obj': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'overdue_count': overdue_count,
        'returned_count': returned_count,
        'due_soon_count': due_soon_count,
    })


@login_required
@role_required('admin', 'librarian')
def member_history_view(request, member_id):
    from django.db.models import Sum
    member = get_object_or_404(CustomUser, pk=member_id)
    today = timezone.now().date()
    records = BorrowRecord.objects.filter(member=member).select_related('book')
    # auto-mark overdue
    records.filter(status='borrowed', due_date__lt=today).update(status='overdue')
    records = BorrowRecord.objects.filter(member=member).select_related('book')

    total_borrows  = records.count()
    active_borrows = records.filter(status__in=['borrowed', 'overdue']).count()
    overdue_borrows = records.filter(status='overdue').count()
    total_fines    = records.aggregate(t=Sum('fine_amount'))['t'] or 0

    return render(request, 'borrowing/member_history.html', {
        'member': member,
        'records': records,
        'total_borrows': total_borrows,
        'active_borrows': active_borrows,
        'overdue_borrows': overdue_borrows,
        'total_fines': total_fines,
    })


# ── Member Management ─────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def member_list_view(request):
    members = CustomUser.objects.filter(role='student').order_by('first_name')
    q = request.GET.get('q', '')
    if q:
        members = members.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) |
            Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    members = members.annotate(
        active_borrows=Count('borrow_records', filter=Q(borrow_records__status__in=['borrowed', 'overdue']))
    )
    paginator = Paginator(members, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'borrowing/member_list.html', {'page_obj': page_obj, 'q': q})


@login_required
@role_required('admin', 'librarian')
def member_edit_view(request, member_id):
    """Librarian/admin can update a student member's basic info."""
    member = get_object_or_404(CustomUser, pk=member_id, role='student')
    from accounts.forms import ProfileUpdateForm
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Member {member.username} updated.')
            return redirect('member_list')
    else:
        form = ProfileUpdateForm(instance=member)
    return render(request, 'borrowing/member_edit.html', {'form': form, 'member': member})
    return render(request, 'borrowing/member_list.html', {'page_obj': page_obj, 'q': q})


# ── Admin Dashboard & Reports ─────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def admin_dashboard_view(request):
    today = timezone.now().date()

    # Auto-mark overdue
    BorrowRecord.objects.filter(status='borrowed', due_date__lt=today).update(status='overdue')

    total_books = Book.objects.count()
    available_books = Book.objects.filter(status='available', available_copies__gt=0).count()
    total_borrowed = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count()
    overdue_count = BorrowRecord.objects.filter(status='overdue').count()
    total_members = CustomUser.objects.filter(role='student').count()
    total_fines = BorrowRecord.objects.filter(fine_amount__gt=0).aggregate(
        total=Sum('fine_amount'))['total'] or Decimal('0.00')
    unpaid_fines = BorrowRecord.objects.filter(fine_amount__gt=0, fine_paid=False).aggregate(
        total=Sum('fine_amount'))['total'] or Decimal('0.00')

    recent_borrows = BorrowRecord.objects.select_related('member', 'book').order_by('-borrowed_date')[:8]
    overdue_records = BorrowRecord.objects.filter(status='overdue').select_related('member', 'book')[:8]

    # Books by category for chart
    from books.models import Category
    categories = Category.objects.annotate(book_count=Count('books')).order_by('-book_count')[:8]

    # Advanced analytics
    from django.db.models.functions import TruncMonth
    from datetime import timedelta
    import json

    # Monthly borrow trend (last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_data = (BorrowRecord.objects
        .filter(borrowed_date__gte=six_months_ago)
        .annotate(month=TruncMonth('borrowed_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month'))
    monthly_labels = [d['month'].strftime('%b %Y') for d in monthly_data]
    monthly_counts = [d['count'] for d in monthly_data]

    # Most popular authors
    from books.models import Book as BookModel
    top_authors = (BookModel.objects
        .values('author')
        .annotate(borrow_count=Count('borrow_records'))
        .order_by('-borrow_count')[:5])

    # Books never borrowed
    rarely_borrowed = BookModel.objects.annotate(
        borrow_count=Count('borrow_records')
    ).filter(borrow_count=0)[:5]

    return render(request, 'borrowing/admin_dashboard.html', {
        'total_books': total_books,
        'available_books': available_books,
        'total_borrowed': total_borrowed,
        'overdue_count': overdue_count,
        'total_members': total_members,
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
        'recent_borrows': recent_borrows,
        'overdue_records': overdue_records,
        'categories': categories,
        'monthly_labels': monthly_labels,
        'monthly_counts': monthly_counts,
        'top_authors': top_authors,
        'rarely_borrowed': rarely_borrowed,
    })


@login_required
@role_required('admin', 'librarian')
def reports_view(request):
    today = timezone.now().date()
    BorrowRecord.objects.filter(status='borrowed', due_date__lt=today).update(status='overdue')

    # Overdue report
    overdue = BorrowRecord.objects.filter(status='overdue').select_related('member', 'book')

    # Fines report
    fines = BorrowRecord.objects.filter(fine_amount__gt=0).select_related('member', 'book').order_by('-fine_amount')

    # Most borrowed books
    top_books = Book.objects.annotate(
        borrow_count=Count('borrow_records')
    ).order_by('-borrow_count')[:10]

    # Most active members
    top_members = CustomUser.objects.filter(role='student').annotate(
        borrow_count=Count('borrow_records')
    ).order_by('-borrow_count')[:10]

    total_fines = fines.aggregate(total=Sum('fine_amount'))['total'] or Decimal('0.00')
    unpaid_fines = fines.filter(fine_paid=False).aggregate(total=Sum('fine_amount'))['total'] or Decimal('0.00')

    return render(request, 'borrowing/reports.html', {
        'overdue': overdue,
        'fines': fines,
        'top_books': top_books,
        'top_members': top_members,
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
    })

# ── CSV Export ────────────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def export_borrows_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="borrow_records.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Member', 'Book', 'ISBN', 'Borrowed Date', 'Due Date',
                     'Returned Date', 'Status', 'Fine (ETB)', 'Fine Paid'])
    records = BorrowRecord.objects.select_related('member', 'book').all()
    for i, r in enumerate(records, 1):
        writer.writerow([
            i, r.member.get_full_name() or r.member.username,
            r.book.title, r.book.isbn or '',
            r.borrowed_date, r.due_date,
            r.returned_date or '', r.get_status_display(),
            r.fine_amount, 'Yes' if r.fine_paid else 'No',
        ])
    log_action(request.user, 'EXPORT', 'Exported borrow records CSV', request)
    return response


@login_required
@role_required('admin', 'librarian')
def export_overdue_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="overdue_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Member', 'Email', 'Book', 'Due Date', 'Days Overdue', 'Fine (ETB)'])
    records = BorrowRecord.objects.filter(status='overdue').select_related('member', 'book')
    for i, r in enumerate(records, 1):
        writer.writerow([
            i, r.member.get_full_name() or r.member.username,
            r.member.email, r.book.title,
            r.due_date, r.days_overdue, r.calculate_fine(),
        ])
    log_action(request.user, 'EXPORT', 'Exported overdue report CSV', request)
    return response


@login_required
@role_required('admin', 'librarian')
def export_books_csv(request):
    from books.models import Book as BookModel
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books_catalog.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Title', 'Author', 'ISBN', 'Category', 'Publisher',
                     'Year', 'Total Copies', 'Available', 'Status'])
    for i, b in enumerate(BookModel.objects.select_related('category').all(), 1):
        writer.writerow([
            i, b.title, b.author, b.isbn or '',
            b.category.name if b.category else '',
            b.publisher, b.publication_year or '',
            b.total_copies, b.available_copies, b.get_status_display(),
        ])
    log_action(request.user, 'EXPORT', 'Exported books catalog CSV', request)
    return response


# ── Borrow Slip ───────────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def borrow_slip_view(request, pk):
    record = get_object_or_404(BorrowRecord, pk=pk)
    return render(request, 'borrowing/borrow_slip.html', {'record': record})


# ── Reservations ─────────────────────────────────────────────────────────────
@login_required
def reserve_book_view(request, book_id):
    """Student reserves an unavailable book."""
    book = get_object_or_404(Book, pk=book_id)

    if request.user.role != 'student':
        messages.error(request, 'Only students can reserve books.')
        return redirect('book_detail', pk=book_id)

    if book.is_available:
        messages.info(request, f'"{book.title}" is available — you can borrow it directly.')
        return redirect('student_borrow', book_id=book_id)

    # Check existing reservation
    existing = Reservation.objects.filter(
        member=request.user, book=book, status__in=['pending', 'ready']
    ).exists()
    if existing:
        messages.warning(request, f'You already have a reservation for "{book.title}".')
        return redirect('book_detail', pk=book_id)

    if request.method == 'POST':
        Reservation.objects.create(member=request.user, book=book)
        log_action(request.user, 'BORROW', f'Reserved "{book.title}"', request)
        messages.success(request, f'"{book.title}" reserved. You will be notified when it becomes available.')
        return redirect('my_reservations')

    return render(request, 'borrowing/reserve_confirm.html', {'book': book})


@login_required
def my_reservations_view(request):
    """Student views their reservations."""
    reservations = Reservation.objects.filter(member=request.user).select_related('book')
    return render(request, 'borrowing/my_reservations.html', {'reservations': reservations})


@login_required
def cancel_reservation_view(request, pk):
    """Student cancels a reservation."""
    res = get_object_or_404(Reservation, pk=pk, member=request.user)
    if request.method == 'POST':
        res.status = 'cancelled'
        res.save()
        messages.success(request, f'Reservation for "{res.book.title}" cancelled.')
        return redirect('my_reservations')
    return render(request, 'borrowing/cancel_reservation.html', {'reservation': res})


# ── Web Backup Trigger ────────────────────────────────────────────────────────

@login_required
@role_required('admin')
def trigger_reminders_view(request):
    """Admin manually triggers due reminder emails."""
    if request.method == 'POST':
        try:
            import subprocess
            from django.conf import settings as django_settings
            result = subprocess.run(
                ['python', 'manage.py', 'send_due_reminders'],
                cwd=django_settings.BASE_DIR,
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                log_action(request.user, 'OTHER', 'Triggered due reminder emails', request)
                messages.success(request, f'Reminders sent. {result.stdout.strip()}')
            else:
                messages.error(request, f'Failed: {result.stderr[:200]}')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_dashboard')
    return render(request, 'borrowing/reminders_confirm.html')


@login_required
@role_required('admin')
def trigger_backup_view(request):
    """Admin can trigger a database backup from the web UI."""
    import subprocess
    from django.conf import settings
    if request.method == 'POST':
        try:
            result = subprocess.run(
                ['python', 'manage.py', 'backup_data'],
                cwd=settings.BASE_DIR,
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                log_action(request.user, 'BACKUP', 'Triggered system backup via web UI', request)
                messages.success(request, 'Backup completed successfully.')
            else:
                messages.error(request, f'Backup failed: {result.stderr[:200]}')
        except Exception as e:
            messages.error(request, f'Backup error: {e}')
        return redirect('admin_dashboard')
    return render(request, 'borrowing/backup_confirm.html')


# ── Fine Management ───────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def mark_fine_paid_view(request, pk):
    """Mark a borrow record's fine as paid."""
    record = get_object_or_404(BorrowRecord, pk=pk)
    if request.method == 'POST':
        record.fine_paid = True
        record.save()
        log_action(request.user, 'EDIT_USER',
                   f'Marked fine paid for {record.member.username} – "{record.book.title}" (ETB {record.fine_amount})', request)
        from activity.utils import notify
        notify(record.member, 'Fine Marked as Paid',
               f'Your fine of ETB {record.fine_amount} for "{record.book.title}" has been marked as paid.',
               type='success', link='/borrow/my/')
        messages.success(request, f'Fine of ETB {record.fine_amount} marked as paid.')
        next_url = request.POST.get('next', 'borrow_list')
        return redirect(next_url)
    return redirect('borrow_list')
