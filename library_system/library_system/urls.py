from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import HttpResponse


def views_about(request):
    from django.shortcuts import render
    features = [
        'Browse & search books by title, author, category',
        'Borrow and return books with fine calculation',
        'Book reservation for unavailable titles',
        'Student borrow limit enforcement',
        'Overdue notifications and due-date alerts',
        'Admin dashboard with charts and statistics',
        'Export reports as PDF and CSV',
        'Activity log for full audit trail',
        'Role-based access (Admin / Librarian / Student)',
        'Responsive design — works on mobile and desktop',
        'Secure authentication with password reset',
        'Online reading links for borrowed books',
    ]
    return render(request, 'about.html', {'features': features})


def views_contact(request):
    from django.shortcuts import render
    from django.core.mail import send_mail
    from django.conf import settings as s
    sent = False
    error = None
    form_data = {}
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        form_data = {'name': name, 'email': email, 'subject': subject, 'message': message}
        if name and email and subject and message:
            try:
                send_mail(
                    f'[Smart Library Contact] {subject}',
                    f'From: {name} <{email}>\n\n{message}',
                    s.DEFAULT_FROM_EMAIL,
                    [s.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                sent = True
                form_data = {}
            except Exception as e:
                error = f'Failed to send message: {e}'
        else:
            error = 'All fields are required.'
    return render(request, 'contact.html', {'sent': sent, 'error': error, 'form_data': form_data})

urlpatterns = [
    path('admin/', admin.site.urls),
    # Password reset (built-in Django views)
    path('accounts/password-reset/',
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('accounts/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('accounts/password-reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('accounts/password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
    # About page
    path('about/', views_about, name='about'),
    path('contact/', views_contact, name='contact'),
    path('accounts/', include('accounts.urls')),
    path('', include('accounts.urls')),
    path('', include('books.urls')),
    path('', include('borrowing.urls')),
    path('', include('activity.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
