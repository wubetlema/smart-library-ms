from django.shortcuts import render
from books.models import Book, Category
from accounts.models import CustomUser


def home_view(request):
    # Books grouped by category
    categories_with_books = []
    for cat in Category.objects.all():
        books = Book.objects.filter(category=cat).order_by('-date_added')[:5]
        if books:
            categories_with_books.append({'category': cat, 'books': books})

    context = {
        'total_books': Book.objects.count(),
        'available_books': Book.objects.filter(status='available', available_copies__gt=0).count(),
        'total_members': CustomUser.objects.filter(role='student').count(),
        'total_categories': Category.objects.count(),
        'categories_with_books': categories_with_books,
    }
    return render(request, 'borrowing/home.html', context)
