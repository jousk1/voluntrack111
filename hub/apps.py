"""App configuration for the Hub application."""

from django.apps import AppConfig


class HubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hub"
    verbose_name = "Volunteer Hub"

    def ready(self):
        # Import signals to register signal handlers
        from . import signals  # noqa: F401
