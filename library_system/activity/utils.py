from .models import ActivityLog, Notification


def log_action(user, action, description, request=None):
    """Helper to create an activity log entry."""
    ip = None
    if request:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
    ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip,
    )


def notify(user, title, message, type='info', link=''):
    """Create an in-system notification for a user."""
    Notification.objects.create(
        user=user, title=title, message=message, type=type, link=link
    )
