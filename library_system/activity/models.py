from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('REGISTER', 'User Registered'),
        ('BORROW', 'Book Borrowed'),
        ('RETURN', 'Book Returned'),
        ('ADD_BOOK', 'Book Added'),
        ('EDIT_BOOK', 'Book Edited'),
        ('DELETE_BOOK', 'Book Deleted'),
        ('ADD_USER', 'User Added'),
        ('EDIT_USER', 'User Edited'),
        ('DELETE_USER', 'User Deleted'),
        ('EXPORT', 'Report Exported'),
        ('BACKUP', 'Data Backup'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='OTHER')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.get_action_display()} – {self.user}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
        ('success', 'Success'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"
