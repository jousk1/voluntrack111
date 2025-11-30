"""
hub/views.py - View Functions for VolunTrack

This module contains all view functions that handle HTTP requests.
Views process data and return HTTP responses (usually rendered templates).

View Categories:
    1. Public Views - Accessible without login (home, register, error pages)
    2. Authenticated Views - Require login (dashboard, events, contributions)
    3. Coordinator Views - Require coordinator role (approvals, management)

Key Patterns Used:
    - @login_required: Django decorator ensuring user is authenticated
    - @coordinator_required: Custom decorator checking Profile.is_coordinator
    - Paginator: Django's pagination for large querysets
    - messages: Django's flash message framework for user feedback

Request/Response Flow:
    1. URL pattern matches (urls.py)
    2. View function called with request object
    3. View processes data (queries, form validation)
    4. View returns HttpResponse (usually render() with template)
"""

import csv
import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Avg, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import coordinator_required
from .forms import ContributionForm, EventForm, UserRegistrationForm
from .models import Contribution, Department, Event, Signup


# =============================================================================
# PUBLIC VIEWS - No authentication required
# =============================================================================

def home(request):
    return render(request, "hub/home.html")


def page_not_found(request, exception):
    # Custom 404 error page.
    return render(request, "hub/404.html", status=404)


def permission_denied(request, exception):

    # Custom 403 error page.
    return render(request, "hub/403.html", status=403)


def register(request):
    # The Profile is created automatically via signal (see signals.py).
    # New users are volunteers by default
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect("hub:dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Create the user account
            user = form.save()
            
            # Set additional fields from form
            user.email = form.cleaned_data.get("email")
            user.first_name = form.cleaned_data.get("first_name")
            user.last_name = form.cleaned_data.get("last_name")
            user.save()
            
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect("hub:dashboard")
    else:
        form = UserRegistrationForm()

    return render(request, "registration/register.html", {"form": form})


# =============================================================================
# AUTHENTICATED VIEWS - Login required
# =============================================================================

@login_required
def dashboard(request):
    """
    Role-based dashboard view.
    
    Displays different dashboards based on user role:
    - Coordinators: See pending approvals, all hours, created events
    - Volunteers: See personal stats, signed events, available events
    
    This is the main landing page after login.
    """
    user = request.user

    if user.profile.is_coordinator:
        # ----- COORDINATOR DASHBOARD -----
        dept = user.profile.department
        
        # Get pending contributions for review
        pending_qs = Contribution.objects.filter(status="PENDING")
        
        # Calculate total approved hours across all users
        total_hours = (
            Contribution.objects
            .filter(status="APPROVED")
            .aggregate(total=Sum("hours"))["total"] or 0
        )
        
        # Get upcoming events created by this coordinator
        my_events = (
            Event.objects
            .filter(created_by=user, date__gte=timezone.now(), status="SCHEDULED")
            .order_by("date")[:5]
        )
        
        # Get upcoming events (optionally filtered by department)
        upcoming_qs = Event.objects.filter(date__gte=timezone.now(), status="SCHEDULED")
        if dept:
            upcoming_qs = upcoming_qs.filter(department=dept)

        return render(request, "hub/coordinator_dashboard.html", {
            "pending_count": pending_qs.count(),
            "total_hours": total_hours,
            "my_events": my_events,
            "upcoming": upcoming_qs.order_by("date")[:5],
            "recent_pending": pending_qs.select_related("user", "event", "department").order_by("-created_at")[:5],
            "total_events": Event.objects.filter(created_by=user).count(),
            "department": dept,
        })
    else:
        # ----- VOLUNTEER DASHBOARD -----
        
        # Calculate this user's total approved hours
        my_hours = (
            Contribution.objects
            .filter(user=user, status="APPROVED")
            .aggregate(total=Sum("hours"))["total"] or 0
        )
        
        # Get events user is signed up for (only scheduled events)
        signed_events = (
            Event.objects
            .filter(signups__user=user, signups__status="CONFIRMED", status="SCHEDULED")
            .distinct()
            .order_by("date")
        )
        
        # Get available events (scheduled, not already signed up)
        available_events = (
            Event.objects
            .filter(status="SCHEDULED")
            .exclude(signups__user=user, signups__status="CONFIRMED")
            .order_by("date")
        )

        return render(request, "hub/dashboard.html", {
            "my_hours": my_hours,
            "pending": Contribution.objects.filter(user=user, status="PENDING")[:5],
            "signed_events": signed_events,
            "available_events": available_events,
        })


@login_required
def events_list(request):
    """
    List all events with filtering, search, and pagination.
    
    Query Parameters:
        status: Filter by event status (SCHEDULED/COMPLETED/ALL)
        mine: If "1", show only events created by current user
        search: Search term for title, description, location
        page: Page number for pagination
    
    Features:
        - Search across title, description, and location
        - Filter by status (defaults to SCHEDULED)
        - Filter by creator (for coordinators to see their events)
        - Paginated results (12 per page)
    """
    # Get filter parameters from query string
    status_filter = request.GET.get("status") or "SCHEDULED"
    show_mine = request.GET.get("mine") == "1"
    search_query = request.GET.get("search", "").strip()

    # Start with all events, prefetch signups for efficiency
    queryset = Event.objects.prefetch_related("signups")

    # Apply filters
    if show_mine:
        queryset = queryset.filter(created_by=request.user)

    if status_filter == "SCHEDULED":
        queryset = queryset.filter(status="SCHEDULED")
    elif status_filter == "COMPLETED":
        queryset = queryset.filter(status="COMPLETED")
    # If status is empty or "ALL", don't filter by status

    # Apply search filter (case-insensitive across multiple fields)
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    # Order by date (newest first) and paginate
    events = queryset.order_by("-date")
    paginator = Paginator(events, 12)  # 12 events per page
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "hub/events_list.html", {
        "events": page_obj,
        "status_filter": status_filter,
        "mine": show_mine,
        "search": search_query,
    })


@login_required
def event_detail(request, pk):
    """
    Display detailed information about a single event.
    
    Shows:
        - Event details (title, description, date, location)
        - Current signup status for the user
        - Remaining capacity
        - List of confirmed participants
        - Hours chart for contributions (if any)
    
    Args:
        pk: Primary key of the Event
    """
    event = get_object_or_404(Event, pk=pk)
    
    # Check if current user is signed up
    is_signed_up = Signup.objects.filter(
        user=request.user, 
        event=event, 
        status="CONFIRMED"
    ).exists()
    
    # Calculate capacity
    current_count = event.signups.filter(status="CONFIRMED").count()
    remaining = max(0, event.capacity - current_count) if event.capacity > 0 else None
    
    # Get approved contribution hours by user for this event (for chart)
    contributions = (
        Contribution.objects
        .filter(event=event, status="APPROVED")
        .values("user__username")
        .annotate(hours=Sum("hours"))
        .order_by("-hours")
    )
    
    # Prepare chart data as JSON
    chart_labels = [c["user__username"] for c in contributions]
    chart_data = [float(c["hours"]) for c in contributions]

    return render(request, "hub/event_detail.html", {
        "event": event,
        "signed": is_signed_up,
        "remaining": remaining,
        "participants": event.signups.filter(status="CONFIRMED").select_related("user"),
        "hours_labels_json": json.dumps(chart_labels),
        "hours_data_json": json.dumps(chart_data),
        "has_hours_data": len(chart_labels) > 0,
    })


@login_required
def event_signup(request, pk):
    """
    Handle event signup for the current user.
    
    Validation:
        - User must not already be signed up
        - Event must not be at capacity (if capacity > 0)
    
    Creates a Signup record with status="CONFIRMED".
    """
    event = get_object_or_404(Event, pk=pk)

    # Check if already signed up
    if event.signups.filter(user=request.user, status="CONFIRMED").exists():
        messages.info(request, "You are already signed up.")
    # Check capacity
    elif event.capacity and event.signups.filter(status="CONFIRMED").count() >= event.capacity:
        messages.error(request, "This event is full.")
    else:
        # Create the signup
        Signup.objects.create(user=request.user, event=event, status="CONFIRMED")
        messages.success(request, "Signed up successfully!")

    return redirect("hub:event_detail", pk=pk)


@login_required
def signup_list(request):
    """
    Display list of events the current user is signed up for.
    
    Only shows:
        - Confirmed signups (not cancelled)
        - Scheduled events (not completed/cancelled)
    """
    signups = (
        Signup.objects
        .filter(user=request.user, status="CONFIRMED", event__status="SCHEDULED")
        .select_related("event")
        .order_by("event__date")
    )
    return render(request, "hub/signup_list.html", {"signups": signups})


@login_required
def signup_cancel(request, pk):
    """
    Cancel a signup for an event.
    
    GET: Show confirmation page
    POST: Cancel the signup (set status to CANCELLED)
    
    Note: We update status rather than delete to preserve history.
    """
    signup = get_object_or_404(
        Signup, 
        pk=pk, 
        user=request.user, 
        status="CONFIRMED"
    )

    if request.method == "POST":
        signup.status = "CANCELLED"
        signup.save()
        messages.success(request, f"Signup cancelled for {signup.event.title}.")
        return redirect("hub:signup_list")

    return render(request, "hub/signup_cancel_confirm.html", {"signup": signup})


@login_required
def contribution_create(request):
    """
    Handle volunteer contribution (hours) logging.
    
    GET: Display empty contribution form
    POST: Validate and save contribution
    
    Validation Rules:
        - If event is selected, it must be SCHEDULED
        - Non-coordinators must be signed up for the event
        - Department is required
        - Hours must be positive
    
    All contributions start with status="PENDING" for coordinator review.
    """
    # Check for pre-selected event (from event detail page link)
    initial_event = None
    event_id = request.GET.get("event")
    if event_id:
        initial_event = Event.objects.filter(pk=event_id).first()

    if request.method == "POST":
        form = ContributionForm(request.POST, user=request.user)
        
        if form.is_valid():
            contribution = form.save(commit=False)  # Don't save yet
            is_coordinator = request.user.profile.is_coordinator

            # Validate event-related rules
            if contribution.event:
                # Event must be scheduled
                if contribution.event.status != "SCHEDULED":
                    form.add_error("event", "You can only log work for scheduled events.")
                # Non-coordinators must be signed up
                elif not is_coordinator and not Signup.objects.filter(
                    user=request.user, 
                    event=contribution.event, 
                    status="CONFIRMED"
                ).exists():
                    form.add_error("event", "You must be signed up for this event.")
                else:
                    # Valid - save the contribution
                    contribution.user = request.user
                    contribution.save()
                    messages.success(request, "Contribution submitted for approval.")
                    return redirect("hub:dashboard")
            else:
                # No event - just save (for non-event volunteer work)
                contribution.user = request.user
                contribution.save()
                messages.success(request, "Contribution submitted for approval.")
                return redirect("hub:dashboard")
    else:
        form = ContributionForm(user=request.user, initial_event=initial_event)

    return render(request, "hub/contribution_create.html", {"form": form})


@login_required
def reports(request):
    """
    Display reports and analytics for volunteer activity.
    
    Shows:
        - Total approved hours
        - Pending contributions count
        - Total contributions
        - Top 10 volunteers chart (bar chart)
        - Hours by department chart (pie chart)
        - Average hours per contribution by department (line chart)
    
    Query Parameters:
        date_from: Filter contributions from this date
        date_to: Filter contributions until this date
    
    Uses Django ORM aggregations (Sum, Avg) and Chart.js for visualization.
    """
    # Get date filter parameters
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    # Base queryset: only approved contributions
    queryset = Contribution.objects.filter(status="APPROVED")

    # Apply date filters if provided
    if date_from:
        queryset = queryset.filter(date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__lte=date_to)

    # ----- AGGREGATIONS -----
    
    # Top 10 volunteers by total hours
    top_volunteers = (
        queryset
        .values("user__username")
        .annotate(hours=Sum("hours"))
        .order_by("-hours")[:10]
    )
    
    # Total hours by department
    dept_totals = (
        queryset
        .values("department__name")
        .annotate(hours=Sum("hours"))
        .order_by("-hours")
    )
    
    # Average hours per contribution by department
    dept_averages = (
        queryset
        .values("department__name")
        .annotate(avg=Avg("hours"))
        .order_by("-avg")
    )

    # Prepare chart data as JSON for Chart.js
    rank_labels = [t["user__username"] for t in top_volunteers]
    rank_data = [float(t["hours"]) for t in top_volunteers]

    return render(request, "hub/reports.html", {
        # Chart data (JSON encoded for JavaScript)
        "rank_labels_json": json.dumps(rank_labels),
        "rank_data_json": json.dumps(rank_data),
        "dept_labels_json": json.dumps([d["department__name"] for d in dept_totals]),
        "dept_data_json": json.dumps([float(d["hours"]) for d in dept_totals]),
        "avg_labels_json": json.dumps([a["department__name"] for a in dept_averages]),
        "avg_data_json": json.dumps([float(a["avg"]) for a in dept_averages]),
        # Flags to conditionally render charts
        "has_rank_data": bool(rank_labels),
        "has_dept_data": dept_totals.exists(),
        "has_avg_data": dept_averages.exists(),
        # Summary statistics
        "total_hours": sum(rank_data),
        "pending_total": Contribution.objects.filter(status="PENDING").count(),
        "total_contributions": Contribution.objects.count(),
        # Filter values (for form persistence)
        "date_from": date_from,
        "date_to": date_to,
    })


# =============================================================================
# COORDINATOR VIEWS - Coordinator role required
# =============================================================================

@login_required
@coordinator_required
def event_create(request):
    """
    Create a new volunteer event.
    
    Only coordinators can create events.
    The event's created_by field is automatically set to the current user.
    """
    if request.method == "POST":
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, "Event created.")
            return redirect("hub:event_detail", pk=event.pk)
    else:
        form = EventForm(user=request.user)

    return render(request, "hub/event_create.html", {"form": form})


@login_required
@coordinator_required
def event_edit(request, pk):
    """
    Edit an existing event.
    
    Only the coordinator who created the event can edit it.
    """
    event = get_object_or_404(Event, pk=pk, created_by=request.user)

    if request.method == "POST":
        form = EventForm(request.POST, instance=event, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated.")
            return redirect("hub:event_detail", pk=event.pk)
    else:
        form = EventForm(instance=event, user=request.user)

    return render(request, "hub/event_edit.html", {"form": form, "event": event})


@login_required
@coordinator_required
def event_delete(request, pk):
    """
    Delete an event.
    
    GET: Show confirmation page
    POST: Delete the event and redirect to events list
    
    Only the coordinator who created the event can delete it.
    """
    event = get_object_or_404(Event, pk=pk, created_by=request.user)

    if request.method == "POST":
        event_title = event.title
        event.delete()
        messages.success(request, f"Event '{event_title}' deleted.")
        return redirect("hub:events_list")

    return render(request, "hub/event_delete_confirm.html", {"event": event})


@login_required
@coordinator_required
def event_update_status(request, pk):
    """
    Update event status (SCHEDULED/COMPLETED/CANCELLED).
    
    POST only - used by status dropdown on event detail page.
    """
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        new_status = request.POST.get("status")
        # Validate status is a valid choice
        if new_status in dict(Event.STATUS_CHOICES):
            event.status = new_status
            event.save()
            messages.success(request, "Event status updated.")

    return redirect("hub:event_detail", pk=pk)


@login_required
@coordinator_required
def approvals_list(request):
    """
    List contributions pending coordinator approval.
    
    Query Parameters:
        status: Filter by contribution status (PENDING/APPROVED/REJECTED)
        department: Filter by department ("all", "mine", or department ID)
        page: Page number for pagination
    
    Displays counts for each status to help coordinators prioritize.
    """
    # Get filter parameters
    status_filter = request.GET.get("status") or "PENDING"
    dept_param = request.GET.get("department")
    my_department = request.user.profile.department

    # Determine department filter
    selected_department = None
    dept_filter_value = "all"

    if dept_param == "mine" and my_department:
        selected_department = my_department
        dept_filter_value = "mine"
    elif dept_param and dept_param not in ("all", "mine"):
        selected_department = Department.objects.filter(pk=dept_param).first()
        dept_filter_value = str(selected_department.pk) if selected_department else "all"

    # Build queryset
    if status_filter:
        queryset = Contribution.objects.filter(status=status_filter)
    else:
        queryset = Contribution.objects.all()

    if selected_department:
        queryset = queryset.filter(department=selected_department)

    # Helper function to count contributions by status
    def count_by_status(status):
        base = Contribution.objects.filter(status=status)
        if selected_department:
            base = base.filter(department=selected_department)
        return base.count()

    # Get contributions with related data and paginate
    contributions = (
        queryset
        .select_related("user", "event", "department", "approved_by")
        .order_by("-created_at")
    )
    paginator = Paginator(contributions, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "hub/approvals_list.html", {
        "contributions": page_obj,
        "status_filter": status_filter,
        "dept_filter_value": dept_filter_value,
        "pending_count": count_by_status("PENDING"),
        "approved_count": count_by_status("APPROVED"),
        "rejected_count": count_by_status("REJECTED"),
        "departments": Department.objects.all(),
        "my_department": my_department,
        "selected_department": selected_department,
    })


@login_required
@coordinator_required
def approval_detail(request, pk):
    """
    Display detailed view of a contribution for review.
    
    Shows all contribution details to help coordinator make approval decision.
    """
    contribution = get_object_or_404(Contribution, pk=pk)
    return render(request, "hub/approval_detail.html", {"contrib": contribution})


@login_required
@coordinator_required
def approval_approve(request, pk):
    """
    Approve a pending contribution.
    
    Sets status to APPROVED and records who approved it and when.
    """
    contribution = get_object_or_404(Contribution, pk=pk, status="PENDING")
    
    contribution.status = "APPROVED"
    contribution.approved_by = request.user
    contribution.approved_at = timezone.now()
    contribution.save()
    
    messages.success(request, "Contribution approved.")
    return redirect("hub:approvals_list")


@login_required
@coordinator_required
def approval_reject(request, pk):
    """
    Reject a pending contribution with reason.
    
    GET: Show form to enter rejection reason
    POST: Save rejection with reason
    """
    contribution = get_object_or_404(Contribution, pk=pk, status="PENDING")

    if request.method == "POST":
        rejection_reason = request.POST.get("rejection_reason", "").strip()
        
        contribution.status = "REJECTED"
        contribution.approved_by = request.user
        contribution.approved_at = timezone.now()
        contribution.rejection_reason = rejection_reason
        contribution.save()
        
        messages.warning(request, "Contribution rejected.")
        return redirect("hub:approvals_list")

    return render(request, "hub/approval_reject.html", {"contrib": contribution})


@login_required
@coordinator_required
def all_logs(request):
    """
    View all contribution logs with filtering.
    
    Coordinator-only view for managing all contributions.
    Supports filtering by status and department.
    """
    # Get filter parameters
    status_filter = request.GET.get("status", "")
    dept_filter = request.GET.get("department", "")

    # Build queryset with related data
    queryset = Contribution.objects.select_related("user", "event", "department", "approved_by")

    # Apply filters
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if dept_filter.isdigit():
        queryset = queryset.filter(department_id=int(dept_filter))

    # Order and paginate
    contributions = queryset.order_by("-created_at")
    paginator = Paginator(contributions, 25)  # 25 per page for logs
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "hub/all_logs.html", {
        "contributions": page_obj,
        "status_filter": status_filter,
        "dept_filter": dept_filter,
        "pending_count": Contribution.objects.filter(status="PENDING").count(),
        "approved_count": Contribution.objects.filter(status="APPROVED").count(),
        "rejected_count": Contribution.objects.filter(status="REJECTED").count(),
        "departments": Department.objects.all(),
    })


@login_required
@coordinator_required
def log_update_status(request, pk):
    """
    Update contribution status (for corrections).
    
    Allows coordinators to change status after initial review.
    Updates approval metadata appropriately.
    """
    contribution = get_object_or_404(Contribution, pk=pk)

    if request.method == "POST":
        new_status = request.POST.get("status")
        
        # Validate status is a valid choice
        if new_status in dict(Contribution.STATUS_CHOICES):
            old_status = contribution.status
            contribution.status = new_status

            # Update approval metadata based on status change
            if new_status in ("APPROVED", "REJECTED") and old_status == "PENDING":
                # New approval/rejection - record who and when
                contribution.approved_by = request.user
                contribution.approved_at = timezone.now()
            elif new_status == "PENDING":
                # Reverting to pending - clear approval data
                contribution.approved_by = None
                contribution.approved_at = None

            contribution.save()
            messages.success(request, f"Log status updated to {new_status}.")

    return redirect("hub:all_logs")


@login_required
@coordinator_required
def export_logs_csv(request):
    """
    Export all contribution logs to CSV file.
    
    Returns a downloadable CSV file containing all contribution data.
    Useful for external reporting and record-keeping.
    """
    # Set up HTTP response as CSV file download
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="voluntrack_logs.csv"'

    # Write CSV data
    writer = csv.writer(response)
    
    # Header row
    writer.writerow([
        "User", "Event", "Department", "Date", "Hours",
        "Status", "Approved By", "Approved At", "Rejection Reason", "Description"
    ])

    # Data rows
    contributions = (
        Contribution.objects
        .select_related("user", "event", "department", "approved_by")
        .order_by("-created_at")
    )
    
    for c in contributions:
        writer.writerow([
            c.user.username,
            c.event.title if c.event else "",
            c.department.name,
            c.date,
            c.hours,
            c.get_status_display(),
            c.approved_by.username if c.approved_by else "",
            c.approved_at or "",
            c.rejection_reason or "",
            c.description[:100] if c.description else "",  # Truncate long descriptions
        ])

    return response


@login_required
@coordinator_required
def coordinator_management(request):
    """
    Manage coordinator users (promote/demote).
    
    Allows coordinators to grant or revoke coordinator status for users.
    Supports filtering by department and searching by name/email.
    
    Security:
        - Only coordinators can access this view
        - Coordinators cannot demote themselves
        - When promoting, optionally assigns the coordinator's department
    """
    # Get all users with their profiles
    users = User.objects.select_related('profile').order_by('username')
    
    # Get filter parameters
    dept_filter = request.GET.get('department', '')
    search_query = request.GET.get('search', '').strip()

    # Apply department filter
    if dept_filter and dept_filter.isdigit():
        users = users.filter(profile__department_id=int(dept_filter))

    # Apply search filter
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Handle promote/demote actions
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')  # 'promote' or 'demote'

        if user_id and action in ['promote', 'demote']:
            target_user = get_object_or_404(User, pk=user_id)

            # Prevent coordinators from demoting themselves
            if action == 'demote' and target_user == request.user:
                messages.error(request, "You cannot remove your own coordinator status.")
            else:
                # Update coordinator status
                target_user.profile.is_coordinator = (action == 'promote')

                # When promoting, optionally assign department
                if action == 'promote' and request.user.profile.department:
                    target_user.profile.department = request.user.profile.department

                target_user.profile.save()
                
                action_text = "promoted to" if action == "promote" else "removed from"
                messages.success(request, f"{target_user.username} {action_text} coordinator.")

            return redirect('hub:coordinator_management')

    # Paginate results
    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "hub/coordinator_management.html", {
        "users": page_obj,
        "departments": Department.objects.all(),
        "dept_filter": dept_filter,
        "search": search_query,
    })
