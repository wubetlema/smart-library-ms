from django.contrib import admin
from .models import BorrowRecord, Reservation


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ['member', 'book', 'borrowed_date', 'due_date', 'status', 'fine_amount', 'fine_paid']
    list_filter = ['status', 'fine_paid']
    search_fields = ['member__username', 'book__title']
    list_editable = ['fine_paid']
    readonly_fields = ['borrowed_date']
    date_hierarchy = 'borrowed_date'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['member', 'book', 'status', 'reserved_at']
    list_filter = ['status']
    search_fields = ['member__username', 'book__title']
    readonly_fields = ['reserved_at']
