from functools import wraps
from django.shortcuts import redirect


def admin_required(view_func):
    """Decorator to protect admin views. Redirects to login if not authenticated."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('platform_admin_id'):
            return redirect('platformadmin:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def superadmin_required(view_func):
    """Decorator to restrict view to superadmins only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('platform_admin_id'):
            return redirect('platformadmin:login')
        if request.session.get('platform_admin_role') != 'superadmin':
            return redirect('platformadmin:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
