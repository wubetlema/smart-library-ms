from django.urls import path
from . import views

urlpatterns = [
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/dashboard/', views.dashboard_view, name='dashboard'),
    path('accounts/profile/', views.profile_view, name='profile'),
    path('accounts/change-password/', views.change_password_view, name='change_password'),
    path('accounts/users/', views.user_list_view, name='user_list'),
    path('accounts/users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('accounts/users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
    path('accounts/users/<int:pk>/toggle-active/', views.toggle_user_active_view, name='toggle_user_active'),
    path('accounts/users/<int:pk>/toggle-approval/', views.toggle_approval_view, name='toggle_approval'),
    path('accounts/librarian/create/', views.create_librarian_view, name='create_librarian'),
    path('accounts/members/<int:pk>/card/', views.library_card_view, name='library_card'),
    path('accounts/members/<int:pk>/qr/', views.member_qr_view, name='member_qr'),
]
