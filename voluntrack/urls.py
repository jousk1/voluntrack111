"""Root URL Configuration."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include(("hub.urls", "hub"), namespace="hub")),
]

# Custom error handlers
handler404 = "hub.views.page_not_found"
handler500 = "hub.views.server_error"
handler403 = "hub.views.permission_denied"
