from django.urls import path
from . import views

urlpatterns = [
    path('activity/', views.activity_log_view, name='activity_log'),
    path('notifications/json/', views.notifications_json, name='notifications_json'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/', views.notifications_page, name='notifications'),
]
