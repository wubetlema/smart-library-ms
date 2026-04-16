from django.urls import path
from . import views
urlpatterns = [
    # Books
    path('books/', views.book_list_view, name='book_list'),
    path('books/add/', views.book_add_view, name='book_add'),
    path('books/<int:pk>/', views.book_detail_view, name='book_detail'),
    path('books/<int:pk>/edit/', views.book_edit_view, name='book_edit'),
    path('books/<int:pk>/delete/', views.book_delete_view, name='book_delete'),
    path('books/<int:pk>/remove-copy/', views.book_remove_copy_view, name='book_remove_copy'),
    path('books/<int:pk>/review/', views.submit_review_view, name='submit_review'),
    path('books/search-suggest/', views.book_search_suggest, name='book_search_suggest'),
    path('books/<int:pk>/qr/', views.book_qr_view, name='book_qr'),
    path('books/export/txt/', views.export_books_txt, name='export_books_txt'),
    # Categories
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.category_add_view, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit_view, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),
]
