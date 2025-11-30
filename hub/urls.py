"""URL Configuration for the Hub App."""

from django.urls import path
from . import views

urlpatterns = [
    # Public
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),

    # Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),

    # Events
    path("events/", views.events_list, name="events_list"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),
    path("events/<int:pk>/status/", views.event_update_status, name="event_update_status"),
    path("events/<int:pk>/signup/", views.event_signup, name="event_signup"),

    # Signups
    path("signups/", views.signup_list, name="signup_list"),
    path("signups/<int:pk>/cancel/", views.signup_cancel, name="signup_cancel"),

    # Contributions
    path("contributions/new/", views.contribution_create, name="contribution_create"),

    # Approvals
    path("approvals/", views.approvals_list, name="approvals_list"),
    path("approvals/<int:pk>/", views.approval_detail, name="approval_detail"),
    path("approvals/<int:pk>/approve/", views.approval_approve, name="approval_approve"),
    path("approvals/<int:pk>/reject/", views.approval_reject, name="approval_reject"),

    # Logs & Reports
    path("logs/", views.all_logs, name="all_logs"),
    path("logs/export/", views.export_logs_csv, name="export_logs_csv"),
    path("logs/<int:pk>/status/", views.log_update_status, name="log_update_status"),
    path("reports/", views.reports, name="reports"),

    # Coordinator Management
    path("coordinators/", views.coordinator_management, name="coordinator_management"),
]
