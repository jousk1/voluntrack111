from django.urls import path
from . import views

"""
URL Categories:
    1. Public: home, register
    2. Dashboard & Profile: dashboard
    3. Events: list, detail, create, edit, delete, status, signup
    4. Signups: list, cancel
    5. Contributions: create
    6. Coordinator: approvals, logs, reports, management
"""
urlpatterns = [
    # PUBLIC URLS
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),

    # DASHBOARD
    path("dashboard/", views.dashboard, name="dashboard"),

    # EVENTS
    # List and detail views
    path("events/", views.events_list, name="events_list"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    
    # Event management (coordinator only)
    path("events/create/", views.event_create, name="event_create"),
    path("events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),
    path("events/<int:pk>/status/", views.event_update_status, name="event_update_status"),
    
    # Event signup
    path("events/<int:pk>/signup/", views.event_signup, name="event_signup"),

    # SIGNUPS (User's event registrations)
    path("signups/", views.signup_list, name="signup_list"),
    path("signups/<int:pk>/cancel/", views.signup_cancel, name="signup_cancel"),

    # CONTRIBUTIONS (Volunteer hours logging)
    path("contributions/new/", views.contribution_create, name="contribution_create"),

    # COORDINATOR: APPROVALS
    path("approvals/", views.approvals_list, name="approvals_list"),
    path("approvals/<int:pk>/", views.approval_detail, name="approval_detail"),
    path("approvals/<int:pk>/approve/", views.approval_approve, name="approval_approve"),
    path("approvals/<int:pk>/reject/", views.approval_reject, name="approval_reject"),

    # COORDINATOR: LOGS & REPORTS
    path("logs/", views.all_logs, name="all_logs"),
    path("logs/export/", views.export_logs_csv, name="export_logs_csv"),
    path("logs/<int:pk>/status/", views.log_update_status, name="log_update_status"),
    path("reports/", views.reports, name="reports"),

    # COORDINATOR: USER MANAGEMENT
    path("coordinators/", views.coordinator_management, name="coordinator_management"),
]
