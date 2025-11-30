"""Custom decorators for access control."""

from functools import wraps
from django.core.exceptions import PermissionDenied


def coordinator_required(view_func):
    # Restrict view access to coordinator users only
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, "profile") and request.user.profile.is_coordinator:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    
    return wrapper
