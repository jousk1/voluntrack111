from functools import wraps

from django.core.exceptions import PermissionDenied

"""
This module contains custom decorators for access control.

Decorators:
    - coordinator_required: Restricts view access to coordinator users only

Usage:
    @login_required
    @coordinator_required
    def my_coordinator_view(request):
        # Only coordinators can access this pass
"""

def coordinator_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, "profile") and request.user.profile.is_coordinator:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    
    return wrapper
