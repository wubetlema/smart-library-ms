from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Book, Category, BookReview
from .forms import BookForm, CategoryForm, BookSearchForm
from accounts.decorators import role_required


@login_required
def book_list_view(request):
    books = Book.objects.select_related('category').all()
    form = BookSearchForm(request.GET)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        author = form.cleaned_data.get('author')
        category = form.cleaned_data.get('category')
        availability = form.cleaned_data.get('availability')

        if q:
            books = books.filter(
                Q(title__icontains=q) | Q(isbn__icontains=q)
            )
        if author:
            books = books.filter(author__icontains=author)
        if category:
            books = books.filter(category=category)
        if availability == 'available':
            books = books.filter(status='available', available_copies__gt=0)
        elif availability == 'unavailable':
            books = books.filter(Q(status__in=['borrowed', 'reserved', 'lost', 'maintenance']) | Q(available_copies=0))

    # Support ?category=ID from home page "View All" links
    elif request.GET.get('category'):
        try:
            from .models import Category as Cat
            cat = Cat.objects.get(pk=request.GET['category'])
            books = books.filter(category=cat)
            # Pre-populate form with this category
            form = BookSearchForm(initial={'category': cat})
        except Exception:
            pass

    total_count = books.count()
    paginator = Paginator(books, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'books/book_list.html', {
        'page_obj': page_obj,
        'form': form,
        'total_count': total_count,
    })


@login_required
def book_detail_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    from borrowing.models import BorrowRecord
    user_borrow = None
    user_review = None
    can_review = False
    if request.user.role == 'student':
        user_borrow = BorrowRecord.objects.filter(
            member=request.user, book=book, status__in=['borrowed', 'overdue']
        ).first()
        # Can review if they have ever borrowed this book
        has_borrowed = BorrowRecord.objects.filter(member=request.user, book=book).exists()
        user_review = BookReview.objects.filter(user=request.user, book=book).first()
        can_review = has_borrowed and not user_review
    reviews = book.reviews.select_related('user').all()
    return render(request, 'books/book_detail.html', {
        'book': book,
        'user_borrow': user_borrow,
        'reviews': reviews,
        'user_review': user_review,
        'can_review': can_review,
    })


@login_required
def submit_review_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    from borrowing.models import BorrowRecord
    if request.user.role != 'student':
        messages.error(request, 'Only students can submit reviews.')
        return redirect('book_detail', pk=pk)
    has_borrowed = BorrowRecord.objects.filter(member=request.user, book=book).exists()
    if not has_borrowed:
        messages.error(request, 'You must borrow this book before reviewing it.')
        return redirect('book_detail', pk=pk)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        if rating and rating.isdigit() and 1 <= int(rating) <= 5:
            BookReview.objects.update_or_create(
                user=request.user, book=book,
                defaults={'rating': int(rating), 'comment': comment}
            )
            messages.success(request, 'Your review has been submitted.')
        else:
            messages.error(request, 'Please select a valid rating.')
    return redirect('book_detail', pk=pk)


@login_required
def book_search_suggest(request):
    """AJAX endpoint for live search suggestions in navbar."""
    q = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        books = Book.objects.filter(
            Q(title__icontains=q) | Q(author__icontains=q)
        )[:8]
        results = [{'id': b.pk, 'title': b.title, 'author': b.author} for b in books]
    from django.http import JsonResponse
    return JsonResponse({'results': results})


@login_required
def book_qr_view(request, pk):
    """Generate QR code image for a book linking to its detail page."""
    import qrcode
    import io
    from django.http import HttpResponse
    book = get_object_or_404(Book, pk=pk)
    url = request.build_absolute_uri(f'/books/{pk}/')
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#1e293b', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return HttpResponse(buf, content_type='image/png')


@login_required
@role_required('admin', 'librarian')
def book_add_view(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'"{book.title}" added successfully.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()
    return render(request, 'books/book_form.html', {'form': form, 'action': 'Add'})


@login_required
@role_required('admin', 'librarian')
def book_edit_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{book.title}" updated successfully.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {'form': form, 'action': 'Edit', 'book': book})


@login_required
@role_required('admin')
def book_delete_view(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        title = book.title
        book.delete()
        messages.success(request, f'"{title}" deleted.')
        return redirect('book_list')
    return render(request, 'books/book_confirm_delete.html', {'book': book})


@login_required
@role_required('admin', 'librarian')
def book_remove_copy_view(request, pk):
    """Remove one copy from a book's total and available count."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        if book.total_copies <= 1:
            messages.error(request, f'Cannot remove the last copy. Use Delete Book to remove it entirely.')
            return redirect('book_detail', pk=pk)
        book.total_copies -= 1
        if book.available_copies > 0:
            book.available_copies -= 1
        if book.available_copies == 0:
            book.status = 'borrowed'
        book.save()
        messages.success(request, f'One copy of "{book.title}" removed. Remaining: {book.total_copies}')
        return redirect('book_detail', pk=pk)
    return redirect('book_detail', pk=pk)


@login_required
@role_required('admin', 'librarian')
def export_books_txt(request):
    """Export all books to a plain text file (books.txt)."""
    from django.http import HttpResponse
    books = Book.objects.select_related('category').all()
    lines = ['Smart Library – Book Catalog', '=' * 50, '']
    for i, b in enumerate(books, 1):
        lines.append(f'{i}. {b.title}')
        lines.append(f'   Author   : {b.author}')
        lines.append(f'   Category : {b.category.name if b.category else "—"}')
        lines.append(f'   ISBN     : {b.isbn or "—"}')
        lines.append(f'   Copies   : {b.total_copies} total, {b.available_copies} available')
        lines.append(f'   Status   : {b.get_status_display()}')
        lines.append('')
    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="books.txt"'
    return response


# ── Category views ────────────────────────────────────────────────────────────

@login_required
@role_required('admin', 'librarian')
def category_list_view(request):
    categories = Category.objects.all()
    return render(request, 'books/category_list.html', {'categories': categories})


@login_required
@role_required('admin', 'librarian')
def category_add_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'books/category_form.html', {'form': form, 'action': 'Add'})


@login_required
@role_required('admin', 'librarian')
def category_edit_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'books/category_form.html', {'form': form, 'action': 'Edit', 'category': category})


@login_required
@role_required('admin')
def category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
        return redirect('category_list')
    return render(request, 'books/category_confirm_delete.html', {'category': category})
