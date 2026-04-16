from django.urls import path
from . import views
from .home_view import home_view
from . import export_views

urlpatterns = [
    # Home
    path('', home_view, name='home'),
    # Borrowing
    path('borrow/', views.borrow_book_view, name='borrow_book'),
    path('borrow/<int:book_id>/', views.borrow_book_view, name='borrow_book_for'),
    path('borrow/member/<int:member_id>/issue/', views.borrow_book_view, name='borrow_for_member'),
    path('borrow/<int:book_id>/request/', views.student_borrow_view, name='student_borrow'),
    path('borrow/<int:book_id>/reserve/', views.reserve_book_view, name='reserve_book'),
    path('reservations/', views.my_reservations_view, name='my_reservations'),
    path('reservations/<int:pk>/cancel/', views.cancel_reservation_view, name='cancel_reservation'),
    path('borrow/list/', views.borrow_list_view, name='borrow_list'),
    path('borrow/return/<int:pk>/', views.return_book_view, name='return_book'),
    path('borrow/<int:pk>/slip/', views.borrow_slip_view, name='borrow_slip'),
    path('borrow/my/', views.my_borrowings_view, name='my_borrowings'),
    path('borrow/member/<int:member_id>/history/', views.member_history_view, name='member_history'),
    path('borrow/<int:pk>/mark-paid/', views.mark_fine_paid_view, name='mark_fine_paid'),
    # Members
    path('members/', views.member_list_view, name='member_list'),
    path('members/<int:member_id>/edit/', views.member_edit_view, name='member_edit'),
    # Dashboard & Reports
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('reports/', views.reports_view, name='reports'),
    path('backup/', views.trigger_backup_view, name='trigger_backup'),
    path('send-reminders/', views.trigger_reminders_view, name='send_reminders'),
    # Exports
    path('export/borrows/csv/', export_views.export_borrows_csv, name='export_borrows_csv'),
    path('export/overdue/csv/', export_views.export_overdue_csv, name='export_overdue_csv'),
    path('export/books/csv/', export_views.export_books_csv, name='export_books_csv'),
    path('export/report/pdf/', export_views.export_report_pdf, name='export_report_pdf'),
]
