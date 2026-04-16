from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from accounts.decorators import role_required
from .models import ActivityLog, Notification


@login_required
@role_required('admin')
def activity_log_view(request):
    logs = ActivityLog.objects.select_related('user').all()
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    paginator = Paginator(logs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'activity/activity_log.html', {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'action_choices': ActivityLog.ACTION_CHOICES,
    })


@login_required
def notifications_json(request):
    """AJAX: return unread notifications for the bell dropdown."""
    notifs = Notification.objects.filter(user=request.user, is_read=False)[:10]
    data = [{
        'id': n.pk,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'link': n.link,
        'created_at': n.created_at.strftime('%b %d, %H:%M'),
    } for n in notifs]
    return JsonResponse({'notifications': data, 'count': notifs.count()})


@login_required
def mark_notifications_read(request):
    """Mark all notifications as read."""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


@login_required
def notifications_page(request):
    """Full notification history page."""
    notifs = Notification.objects.filter(user=request.user)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'activity/notifications.html', {'notifications': notifs})
