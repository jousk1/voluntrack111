from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("events/", views.events_list, name="events_list"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/<int:pk>/status/", views.event_update_status, name="event_update_status"),
    path("events/<int:pk>/signup/", views.event_signup, name="event_signup"),
    path("signups/", views.signup_list, name="signup_list"),
    path("contributions/new/", views.contribution_create, name="contribution_create"),
    path("approvals/", views.approvals_list, name="approvals_list"),
    path("approvals/<int:pk>/", views.approval_detail, name="approval_detail"),
    path("approvals/<int:pk>/approve/", views.approval_approve, name="approval_approve"),
    path("approvals/<int:pk>/reject/", views.approval_reject, name="approval_reject"),
    path("logs/", views.all_logs, name="all_logs"),
    path("logs/<int:pk>/status/", views.log_update_status, name="log_update_status"),
    path("reports/", views.reports, name="reports"),
]
