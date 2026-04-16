from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'description', 'ip_address']
    list_filter = ['action']
    search_fields = ['user__username', 'description', 'ip_address']
    readonly_fields = ['timestamp', 'user', 'action', 'description', 'ip_address']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False  # logs are read-only

    def has_change_permission(self, request, obj=None):
        return False
