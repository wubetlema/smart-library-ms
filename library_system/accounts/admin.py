from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_approved', 'date_joined']
    list_filter = ['role', 'is_active', 'is_approved']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_editable = ['role', 'is_active', 'is_approved']
    fieldsets = UserAdmin.fieldsets + (
        ('Library Info', {'fields': ('role', 'phone', 'address', 'date_of_birth', 'profile_picture', 'is_approved')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Library Info', {'fields': ('role', 'email', 'first_name', 'last_name', 'is_approved')}),
    )
