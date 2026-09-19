from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            profile = getattr(request.user, 'profile', None)
            user_role = profile.role if profile else 'public_viewer'
            
            if user_role in allowed_roles or user_role == 'admin':
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f"Access Denied: Your role ({user_role}) is not authorized for this action.")
            raise PermissionDenied
        return _wrapped_view
    return decorator
