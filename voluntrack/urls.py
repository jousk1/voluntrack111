from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include(("hub.urls", "hub"), namespace="hub")),
    path("", RedirectView.as_view(pattern_name="hub:home", permanent=False)),
]
