from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import json

from .decorators import coordinator_required
from .forms import ContributionForm, EventForm, UserRegistrationForm
from .models import Contribution, Event, Signup, Department

def home(request):
    return render(request, "hub/home.html")

def register(request):
    if request.user.is_authenticated:
        return redirect("hub:dashboard")
    
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data.get("email")
            user.first_name = form.cleaned_data.get("first_name")
            user.last_name = form.cleaned_data.get("last_name")
            user.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created successfully.")
            return redirect("hub:dashboard")
    else:
        form = UserRegistrationForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def dashboard(request):
    is_coordinator = hasattr(request.user, "profile") and request.user.profile.is_coordinator
    
    if is_coordinator:
        dept = getattr(request.user.profile, "department", None)
        
        # Pending approvals count
        pending_qs = Contribution.objects.filter(status="PENDING")
        pending_count = pending_qs.count()
        
        # Total approved hours (all users)
        total_hours = (Contribution.objects
                      .filter(status="APPROVED")
                      .aggregate(total=Sum("hours"))["total"] or 0)
        
        # My upcoming events: only future, pending events created by this coordinator
        my_events_qs = (Event.objects
                        .filter(created_by=request.user,
                                date__gte=timezone.now())
                        .filter(Q(status="SCHEDULED") | Q(status__isnull=True) | Q(status="")))
        my_events = my_events_qs.order_by("date")[:5]
        
        # Upcoming events (future & pending, optionally filtered by department)
        upcoming_qs = (Event.objects
                       .filter(date__gte=timezone.now())
                       .filter(Q(status="SCHEDULED") | Q(status__isnull=True) | Q(status="")))
        if dept:
            upcoming_qs = upcoming_qs.filter(department=dept)
        upcoming = upcoming_qs.order_by("date")[:5]
        
        # Recent contributions (for approval)
        recent_pending = pending_qs.select_related("user", "event", "department").order_by("-created_at")[:5]
        
        # Total events created
        total_events = Event.objects.filter(created_by=request.user).count()
        
        return render(request, "hub/coordinator_dashboard.html", {
            "pending_count": pending_count,
            "total_hours": total_hours,
            "my_events": my_events,
            "upcoming": upcoming,
            "recent_pending": recent_pending,
            "total_events": total_events,
            "department": dept,
        })
    else:
        # Volunteer dashboard
        my_hours = (Contribution.objects
                    .filter(user=request.user, status="APPROVED")
                    .aggregate(total=Sum("hours"))["total"] or 0)
        pending = Contribution.objects.filter(user=request.user, status="PENDING")[:5]

        # Events I'm signed up for (both pending and completed)
        signed_events = (Event.objects
                         .filter(signups__user=request.user, signups__status="CONFIRMED")
                         .distinct()
                         .order_by("date"))

        # Other available events: pending events I'm not signed up for
        available_events = (Event.objects
                            .filter(Q(status="SCHEDULED") | Q(status__isnull=True) | Q(status=""))
                            .exclude(signups__user=request.user, signups__status="CONFIRMED")
                            .order_by("date"))

        return render(request, "hub/dashboard.html", {
            "my_hours": my_hours,
            "pending": pending,
            "signed_events": signed_events,
            "available_events": available_events,
        })

@login_required
def events_list(request):
    # Events listing with optional status/owner filters
    status = request.GET.get("status") or "SCHEDULED"
    mine = request.GET.get("mine") == "1"

    qs = Event.objects.all()
    if mine:
        qs = qs.filter(created_by=request.user)

    if status == "SCHEDULED":
        qs = qs.filter(status="SCHEDULED")
    elif status == "COMPLETED":
        qs = qs.filter(status="COMPLETED")
    elif status == "ALL":
        pass
    events = qs.order_by("-date")
    return render(request, "hub/events_list.html", {
        "events": events,
        "status_filter": status,
        "mine": mine,
    })

@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    signed = Signup.objects.filter(user=request.user, event=event, status="CONFIRMED").exists()
    current_count = event.signups.filter(status="CONFIRMED").count()
    remaining = max(0, event.capacity - current_count)
    participants = event.signups.filter(status="CONFIRMED").select_related("user")
    # Hours per volunteer for this event (approved only)
    contribs = (Contribution.objects
                .filter(event=event, status="APPROVED")
                .values("user__username")
                .annotate(hours=Sum("hours"))
                .order_by("-hours"))
    hours_labels = [c["user__username"] for c in contribs]
    hours_data = [float(c["hours"]) for c in contribs]
    return render(request, "hub/event_detail.html", {
        "event": event,
        "signed": signed,
        "remaining": remaining,
        "participants": participants,
        "hours_labels_json": json.dumps(hours_labels),
        "hours_data_json": json.dumps(hours_data),
        "has_hours_data": bool(hours_labels),
    })


@login_required
@coordinator_required
def event_update_status(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        valid_statuses = {choice[0] for choice in Event.STATUS}
        if new_status in valid_statuses:
            event.status = new_status
            event.save()
            messages.success(request, "Event status updated.")
    return redirect("hub:event_detail", pk=pk)

@login_required
def event_signup(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.signups.filter(user=request.user, status="CONFIRMED").exists():
        messages.info(request, "You are already signed up.")
        return redirect("hub:event_detail", pk=pk)
    if event.capacity and event.signups.filter(status="CONFIRMED").count() >= event.capacity:
        messages.error(request, "This event is full.")
        return redirect("hub:event_detail", pk=pk)
    Signup.objects.create(user=request.user, event=event, status="CONFIRMED")
    messages.success(request, "Signed up successfully!")
    return redirect("hub:event_detail", pk=pk)

@login_required
@coordinator_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.created_by = request.user
            ev.save()
            messages.success(request, "Event created.")
            return redirect("hub:event_detail", pk=ev.pk)
    else:
        form = EventForm()
    return render(request, "hub/event_create.html", {"form": form})

@login_required
def signup_list(request):
    # Your signups
    signups = Signup.objects.filter(user=request.user, status="CONFIRMED").select_related("event").order_by("event__date")
    return render(request, "hub/signup_list.html", {"signups": signups})

@login_required
def contribution_create(request):
    if request.method == "POST":
        form = ContributionForm(request.POST, user=request.user)
        if form.is_valid():
            contrib = form.save(commit=False)
            is_coordinator = hasattr(request.user, "profile") and request.user.profile.is_coordinator

            if contrib.event:
                # Only pending events
                if contrib.event.status != "SCHEDULED":
                    form.add_error("event", "You can only log work for pending events.")
                # Volunteers must be signed up for the event
                elif (not is_coordinator and
                      not Signup.objects.filter(user=request.user, event=contrib.event, status="CONFIRMED").exists()):
                    form.add_error("event", "You must be signed up for this event to log work.")
                else:
                    contrib.user = request.user
                    contrib.status = "PENDING"
                    contrib.save()
                    messages.success(request, "Contribution submitted for approval.")
                    return redirect("hub:dashboard")
            else:
                # Logging work not tied to a specific event is allowed for pending department work
                contrib.user = request.user
                contrib.status = "PENDING"
                contrib.save()
                messages.success(request, "Contribution submitted for approval.")
                return redirect("hub:dashboard")
    else:
        form = ContributionForm(user=request.user)
    return render(request, "hub/contribution_create.html", {"form": form})

@login_required
@coordinator_required
def approvals_list(request):

    status_filter = request.GET.get("status") or "PENDING"
    dept_param = request.GET.get("department")

    dept = getattr(request.user.profile, "department", None)
    selected_department = None
    dept_filter_value = "all"

    if dept_param == "mine" and dept:
        selected_department = dept
        dept_filter_value = "mine"
    elif dept_param and dept_param not in ("all", "mine"):
        try:
            selected_department = Department.objects.get(pk=dept_param)
            dept_filter_value = str(selected_department.pk)
        except Department.DoesNotExist:
            selected_department = None
            dept_filter_value = "all"
    elif dept_param == "mine" and not dept:
        selected_department = None
        dept_filter_value = "all"
    else:
        selected_department = None
        dept_filter_value = "all"

    qs = Contribution.objects.all()

    if status_filter:
        qs = qs.filter(status=status_filter)

    if selected_department:
        qs = qs.filter(department=selected_department)

    contributions = qs.select_related("user", "event", "department", "approved_by").order_by("-created_at")

    def count_for(status):
        count_qs = Contribution.objects.filter(status=status)
        if selected_department:
            count_qs = count_qs.filter(department=selected_department)
        return count_qs.count()

    pending_count = count_for("PENDING")
    approved_count = count_for("APPROVED")
    rejected_count = count_for("REJECTED")

    all_departments = Department.objects.all()

    return render(request, "hub/approvals_list.html", {
        "contributions": contributions,
        "status_filter": status_filter,
        "dept_filter_value": dept_filter_value,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "departments": all_departments,
        "my_department": dept,
        "selected_department": selected_department,
    })

@login_required
@coordinator_required
def approval_detail(request, pk):
    contrib = get_object_or_404(Contribution, pk=pk)
    return render(request, "hub/approval_detail.html", {"contrib": contrib})

@login_required
@coordinator_required
def approval_approve(request, pk):
    contrib = get_object_or_404(Contribution, pk=pk, status="PENDING")
    contrib.status = "APPROVED"
    contrib.approved_by = request.user
    contrib.approved_at = timezone.now()
    contrib.save()
    messages.success(request, "Contribution approved.")
    return redirect("hub:approvals_list")

@login_required
@coordinator_required
def approval_reject(request, pk):
    contrib = get_object_or_404(Contribution, pk=pk, status="PENDING")
    contrib.status = "REJECTED"
    contrib.approved_by = request.user
    contrib.approved_at = timezone.now()
    contrib.save()
    messages.warning(request, "Contribution rejected.")
    return redirect("hub:approvals_list")

@login_required
def reports(request):
    # Totals per user (approved)
    totals = (Contribution.objects.filter(status="APPROVED")
              .values("user__username").annotate(hours=Sum("hours")).order_by("-hours")[:10])

    # Average hours across departments
    dept_avgs = (Contribution.objects.filter(status="APPROVED")
                 .values("department__name").annotate(avg=Avg("hours")).order_by("-avg"))

    # Department totals
    dept_totals = (Contribution.objects.filter(status="APPROVED")
                   .values("department__name").annotate(hours=Sum("hours")).order_by("-hours"))

    # Prepare series for Chart.js
    rank_labels = [t["user__username"] for t in totals]
    rank_data = [float(t["hours"]) for t in totals]

    dept_labels = [d["department__name"] for d in dept_totals]
    dept_data = [float(d["hours"]) for d in dept_totals]

    avg_labels = [a["department__name"] for a in dept_avgs]
    avg_data = [float(a["avg"]) for a in dept_avgs]

    total_hours = sum(rank_data)
    pending_total = Contribution.objects.filter(status="PENDING").count()
    total_contributions = Contribution.objects.count()

    context = {
        "rank_labels_json": json.dumps(rank_labels),
        "rank_data_json": json.dumps(rank_data),
        "dept_labels_json": json.dumps(dept_labels),
        "dept_data_json": json.dumps(dept_data),
        "avg_labels_json": json.dumps(avg_labels),
        "avg_data_json": json.dumps(avg_data),
        "has_rank_data": bool(rank_labels),
        "has_dept_data": bool(dept_labels),
        "has_avg_data": bool(avg_labels),
        "total_hours": total_hours,
        "pending_total": pending_total,
        "total_contributions": total_contributions,
    }

    return render(request, "hub/reports.html", context)
