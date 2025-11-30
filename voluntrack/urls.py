"""
URL Structure:
    /admin/     → Django admin interface
    /accounts/  → Django auth URLs (login, logout, password reset)
    /          → Hub app URLs (all main functionality)

Custom Error Handlers:
    The handler404, handler500, and handler403 variables tell Django
    which views to use for error pages.
"""

from django.contrib import admin
from django.urls import include, path

# URL patterns for the project
urlpatterns = [
    # Django admin interface
    # Access at /admin/ - only users with is_staff=True can log in
    path("admin/", admin.site.urls),
    
    # Django's built-in authentication URLs
    # Provides: login, logout, password_change, password_reset
    # Templates should be in registration/ directory
    path("accounts/", include("django.contrib.auth.urls")),
    
    # Hub app URLs (main application)
    # The namespace "hub" allows {% url 'hub:view_name' %} in templates
    path("", include(("hub.urls", "hub"), namespace="hub")),
]

# CUSTOM ERROR HANDLERS

# These handlers override Django's default error pages
# with custom, user-friendly pages defined in hub/views.py

# 404 - Page Not Found
handler404 = "hub.views.page_not_found"


# 500 - Server Error
handler500 = "hub.views.server_error"

# 403 - Permission Denied
handler403 = "hub.views.permission_denied"
