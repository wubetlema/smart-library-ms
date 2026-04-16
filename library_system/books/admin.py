from django.contrib import admin
from .models import Book, Category, BookReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'available_copies', 'total_copies', 'date_added']
    list_filter = ['status', 'category']
    search_fields = ['title', 'author', 'isbn']
    list_editable = ['status', 'available_copies']
    readonly_fields = ['date_added', 'updated_at']
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'author', 'isbn', 'category', 'description')}),
        ('Publication', {'fields': ('publisher', 'publication_year')}),
        ('Copies & Status', {'fields': ('total_copies', 'available_copies', 'status')}),
        ('Media', {'fields': ('cover_image', 'cover_url', 'read_url')}),
        ('Timestamps', {'fields': ('date_added', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ['book', 'user', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['book__title', 'user__username']
    readonly_fields = ['created_at']
