"""
hub/__init__.py - Hub App Package Initialization

This file marks the 'hub' directory as a Python package.

The hub app is the main application for VolunTrack, containing:
    - models.py: Database models (Department, Profile, Event, Signup, Contribution)
    - views.py: View functions for handling HTTP requests
    - forms.py: Form classes for user input
    - urls.py: URL patterns for the app
    - admin.py: Django admin configuration
    - signals.py: Django signals (auto-create Profile)
    - decorators.py: Custom decorators (coordinator_required)
    - templates/: HTML templates
    - static/: CSS and JavaScript files
    - management/commands/: Custom management commands
"""

