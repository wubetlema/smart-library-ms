from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import CustomUser
from .forms import RegisterForm, LoginForm, ProfileUpdateForm, AdminUserEditForm
from .decorators import role_required
from activity.utils import log_action
from books.models import Book
from borrowing.models import BorrowRecord


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            log_action(user, 'REGISTER', f'New account registered: {user.username}', request)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    import time
    now = time.time()
    lockout_until = request.session.get('login_lockout_until', 0)
    attempts = request.session.get('login_attempts', 0)

    # Check if lockout has expired
    if lockout_until and now > lockout_until:
        request.session['login_attempts'] = 0
        request.session['login_lockout_until'] = 0
        attempts = 0

    if attempts >= 5 and now < lockout_until:
        remaining_mins = int((lockout_until - now) / 60) + 1
        messages.error(request, f'Too many failed attempts. Try again in {remaining_mins} minute(s).')
        return render(request, 'accounts/login.html', {'form': LoginForm(), 'locked': True})

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_approved:
                messages.error(request, 'Your account is pending approval by an administrator.')
                return redirect('login')
            request.session['login_attempts'] = 0
            request.session['login_lockout_until'] = 0
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            log_action(user, 'LOGIN', f'{user.username} logged in', request)
            return redirect('dashboard')
        else:
            new_attempts = attempts + 1
            request.session['login_attempts'] = new_attempts
            if new_attempts >= 5:
                request.session['login_lockout_until'] = now + 900  # 15 minutes
                messages.error(request, 'Account locked for 15 minutes due to too many failed attempts.')
            else:
                remaining = 5 - new_attempts
                messages.error(request, f'Invalid username or password. {remaining} attempt(s) remaining.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    log_action(request.user, 'LOGOUT', f'{request.user.username} logged out', request)
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard_view(request):
    today = timezone.now().date()
    BorrowRecord.objects.filter(status='borrowed', due_date__lt=today).update(status='overdue')

    total_books = Book.objects.count()
    available_books = Book.objects.filter(status='available', available_copies__gt=0).count()
    borrowed_books = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count()
    registered_members = CustomUser.objects.filter(role='student').count()
    overdue_count = BorrowRecord.objects.filter(status='overdue').count()

    # student-specific
    my_active = 0
    my_overdue = 0
    if request.user.role == 'student':
        my_active = BorrowRecord.objects.filter(
            member=request.user, status__in=['borrowed', 'overdue']).count()
        my_overdue = BorrowRecord.objects.filter(
            member=request.user, status='overdue').count()

    return render(request, 'accounts/dashboard.html', {
        'user': request.user,
        'total_books': total_books,
        'available_books': available_books,
        'borrowed_books': borrowed_books,
        'registered_members': registered_members,
        'overdue_count': overdue_count,
        'my_active': my_active,
        'my_overdue': my_overdue,
    })


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    total_borrowed = BorrowRecord.objects.filter(member=request.user).count()
    total_returned = BorrowRecord.objects.filter(member=request.user, status='returned').count()
    active_borrows = BorrowRecord.objects.filter(member=request.user, status__in=['borrowed', 'overdue']).count()

    return render(request, 'accounts/profile.html', {
        'form': form,
        'total_borrowed': total_borrowed,
        'total_returned': total_returned,
        'active_borrows': active_borrows,
    })


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


# ── Admin / Librarian views ──────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def user_list_view(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    users = CustomUser.objects.all().order_by('role', 'username')
    q = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) |
            Q(last_name__icontains=q) | Q(email__icontains=q)
        )
    if role_filter:
        users = users.filter(role=role_filter)
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'pending':
        users = users.filter(is_approved=False)

    paginator = Paginator(users, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts/user_list.html', {
        'page_obj': page_obj,
        'q': q,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'admin_count': CustomUser.objects.filter(role='admin').count(),
        'librarian_count': CustomUser.objects.filter(role='librarian').count(),
        'student_count': CustomUser.objects.filter(role='student').count(),
        'pending_count': CustomUser.objects.filter(is_approved=False).count(),
    })


@login_required
@role_required('admin')
def user_edit_view(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            new_role = form.cleaned_data.get('role')
            # Enforce max 5 admins
            if new_role == 'admin' and user_obj.role != 'admin':
                admin_count = CustomUser.objects.filter(role='admin').count()
                if admin_count >= 5:
                    messages.error(request, 'Maximum of 5 admin accounts allowed. Cannot assign admin role.')
                    return render(request, 'accounts/user_edit.html', {'form': form, 'edited_user': user_obj})
            form.save()
            messages.success(request, f'User {user_obj.username} updated.')
            return redirect('user_list')
    else:
        form = AdminUserEditForm(instance=user_obj)
    return render(request, 'accounts/user_edit.html', {'form': form, 'edited_user': user_obj})


@login_required
@role_required('admin')
def user_delete_view(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        username = user.username
        user.delete()
        log_action(request.user, 'DELETE_USER', f'Deleted user: {username}', request)
        messages.success(request, f'User {username} deleted.')
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'edited_user': user})


@login_required
@role_required('admin')
def create_librarian_view(request):
    """Admin creates a librarian account directly."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'librarian'
            user.is_approved = True
            user.save()
            log_action(request.user, 'ADD_USER',
                       f'Created librarian account: {user.username}', request)
            messages.success(request, f'Librarian account "{user.username}" created.')
            return redirect('user_list')
    else:
        form = RegisterForm()
    return render(request, 'accounts/create_librarian.html', {'form': form})


@login_required
@role_required('admin')
def toggle_user_active_view(request, pk):
    """Admin activates or deactivates a user account."""
    target = get_object_or_404(CustomUser, pk=pk)
    if target.pk == request.user.pk:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect('user_list')
    target.is_active = not target.is_active
    target.save()
    action = 'activated' if target.is_active else 'deactivated'
    log_action(request.user, 'EDIT_USER',
               f'Account {action}: {target.username}', request)
    messages.success(request, f'Account "{target.username}" {action}.')
    return redirect('user_list')


@login_required
@role_required('admin', 'librarian')
def library_card_view(request, pk):
    """Generate printable library ID card for a student."""
    member = get_object_or_404(CustomUser, pk=pk)
    total_borrowed = BorrowRecord.objects.filter(member=member).count()
    return render(request, 'accounts/library_card.html', {
        'member': member,
        'total_borrowed': total_borrowed,
    })


@login_required
@role_required('admin')
def toggle_approval_view(request, pk):
    """Admin approves or revokes approval for a user account."""
    target = get_object_or_404(CustomUser, pk=pk)
    if target.pk == request.user.pk:
        messages.error(request, "You cannot change your own approval status.")
        return redirect('user_list')
    target.is_approved = not target.is_approved
    target.save()
    action = 'approved' if target.is_approved else 'unapproved'
    log_action(request.user, 'EDIT_USER', f'Account {action}: {target.username}', request)
    messages.success(request, f'Account "{target.username}" {action}.')
    return redirect('user_list')


@login_required
def member_qr_view(request, pk):
    """QR code linking to member profile (for library card)."""
    import qrcode, io
    from django.http import HttpResponse
    member = get_object_or_404(CustomUser, pk=pk)
    url = request.build_absolute_uri(f'/borrow/member/{pk}/history/')
    qr = qrcode.QRCode(version=1, box_size=6, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1e293b', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf, content_type='image/png')
