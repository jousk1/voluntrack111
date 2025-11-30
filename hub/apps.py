"""
App Configuration:
    - name: The Python path to the app ('hub')
    - default_auto_field: The default primary key field type
    - ready(): Hook called when Django is ready (used to load signals)

Why ready() is Important:
    Signals (like our Profile auto-creation signal) need to be
    imported when Django starts. The ready() method is the
    recommended place to do this import.
"""

from django.apps import AppConfig


class HubConfig(AppConfig):
    """
    Configuration class for the Hub application.
    
    This class is referenced in INSTALLED_APPS via the app's __init__.py
    or by the full path 'hub.apps.HubConfig'.
    """
    
    # Default primary key field type for models in this app
    default_auto_field = "django.db.models.BigAutoField"
    
    # Python path to the application
    name = "hub"
    
    # Human-readable name for the app
    verbose_name = "Volunteer Hub"

    def ready(self):
        """
        Called when Django has finished loading the app.
        
        This method imports the signals module to register signal handlers.
        The import has a side effect: it connects the signal receivers
        defined in signals.py.
        
        Note: The 'noqa' comment tells linters to ignore the "unused import"
        warning, since the import is intentionally for its side effect.
        """
        # Import signals to register the signal handlers
        from . import signals  # noqa: F401
