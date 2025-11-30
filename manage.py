"""



VolunTrack - Volunteer Management System

Project Structure:
    voluntrack/
    ├── manage.py               
    ├── requirements.txt         Python dependencies
    │
    ├── hub/                     Main application
    │   ├── models.py            Database models (Department, Profile, Event, Signup, Contribution)
    │   ├── views.py             Request handlers and business logic
    │   ├── forms.py             Form classes for user input validation
    │   ├── urls.py              URL routing
    │   ├── admin.py             Admin panel configuration
    │   ├── decorators.py        Custom @coordinator_required decorator
    │   ├── signals.py           Auto-create Profile on User creation
    │   ├── static/hub/          CSS styles
    │   └── templates/           HTML templates (dashboard, events, reports, etc.)
    │
    └── voluntrack/              Project configuration
        ├── settings.py          Django settings
        └── urls.py              Root URL config + error handlers



"""

import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voluntrack.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
