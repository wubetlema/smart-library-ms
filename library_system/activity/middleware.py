from django.utils.deprecation import MiddlewareMixin


# URL patterns to skip logging (static, media, admin ajax)
SKIP_PATHS = ['/static/', '/media/', '/admin/jsi18n/', '/favicon']


class ActivityLogMiddleware(MiddlewareMixin):
    """Auto-log page visits for authenticated users (POST only to reduce noise)."""

    def process_response(self, request, response):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return response
        if request.method != 'POST':
            return response
        path = request.path
        if any(path.startswith(s) for s in SKIP_PATHS):
            return response
        if response.status_code in (301, 302):
            # Only log successful form submissions
            from .utils import log_action
            log_action(
                user=request.user,
                action='OTHER',
                description=f"POST {path}",
                request=request,
            )
        return response


class NoCacheMiddleware(MiddlewareMixin):
    """
    Prevent browser from caching authenticated pages and form pages.
    This stops the back button from showing stale login/register/form pages
    after the user has already completed the action.
    """
    NO_CACHE_PATHS = [
        '/accounts/register/',
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/dashboard/',
        '/accounts/profile/',
        '/accounts/change-password/',
        '/borrow/',
        '/members/',
    ]

    def process_response(self, request, response):
        # Always no-cache for auth pages and form submissions
        path = request.path
        is_auth_page = any(path.startswith(p) for p in self.NO_CACHE_PATHS)
        is_post = request.method == 'POST'
        is_authenticated = hasattr(request, 'user') and request.user.is_authenticated

        if is_auth_page or is_post or is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
