from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg
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
            messages.success(request, f"Welcome, {user.username}!")
            return redirect("hub:dashboard")
    else:
        form = UserRegistrationForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def dashboard(request):
    user = request.user
    if user.profile.is_coordinator:
        dept = user.profile.department
        pending_qs = Contribution.objects.filter(status="PENDING")
        total_hours = Contribution.objects.filter(status="APPROVED").aggregate(t=Sum("hours"))["t"] or 0
        my_events = Event.objects.filter(created_by=user, date__gte=timezone.now(), status="SCHEDULED").order_by("date")[:5]
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
        my_hours = Contribution.objects.filter(user=user, status="APPROVED").aggregate(t=Sum("hours"))["t"] or 0
        signed_events = Event.objects.filter(signups__user=user, signups__status="CONFIRMED").distinct().order_by("date")
        available_events = Event.objects.filter(status="SCHEDULED").exclude(signups__user=user, signups__status="CONFIRMED").order_by("date")
        return render(request, "hub/dashboard.html", {
            "my_hours": my_hours,
            "pending": Contribution.objects.filter(user=user, status="PENDING")[:5],
            "signed_events": signed_events,
            "available_events": available_events,
        })

@login_required
def events_list(request):
    status = request.GET.get("status") or "SCHEDULED"
    mine = request.GET.get("mine") == "1"
    qs = Event.objects.all()
    if mine:
        qs = qs.filter(created_by=request.user)
    if status == "SCHEDULED":
        qs = qs.filter(status="SCHEDULED")
    elif status == "COMPLETED":
        qs = qs.filter(status="COMPLETED")
    return render(request, "hub/events_list.html", {"events": qs.order_by("-date"), "status_filter": status, "mine": mine})

@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    signed = Signup.objects.filter(user=request.user, event=event, status="CONFIRMED").exists()
    current_count = event.signups.filter(status="CONFIRMED").count()
    contribs = Contribution.objects.filter(event=event, status="APPROVED").values("user__username").annotate(hours=Sum("hours")).order_by("-hours")
    return render(request, "hub/event_detail.html", {
        "event": event, "signed": signed,
        "remaining": max(0, event.capacity - current_count),
        "participants": event.signups.filter(status="CONFIRMED").select_related("user"),
        "hours_labels_json": json.dumps([c["user__username"] for c in contribs]),
        "hours_data_json": json.dumps([float(c["hours"]) for c in contribs]),
        "has_hours_data": contribs.exists(),
    })

@login_required
@coordinator_required
def event_update_status(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Event.STATUS):
            event.status = new_status
            event.save()
            messages.success(request, "Event status updated.")
    return redirect("hub:event_detail", pk=pk)

@login_required
def event_signup(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if event.signups.filter(user=request.user, status="CONFIRMED").exists():
        messages.info(request, "You are already signed up.")
    elif event.capacity and event.signups.filter(status="CONFIRMED").count() >= event.capacity:
        messages.error(request, "This event is full.")
    else:
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
    signups = Signup.objects.filter(user=request.user, status="CONFIRMED").select_related("event").order_by("event__date")
    return render(request, "hub/signup_list.html", {"signups": signups})

@login_required
def contribution_create(request):
    initial_event = None
    if eid := request.GET.get("event"):
        initial_event = Event.objects.filter(pk=eid).first()
    
    if request.method == "POST":
        form = ContributionForm(request.POST, user=request.user)
        if form.is_valid():
            contrib = form.save(commit=False)
            is_coord = request.user.profile.is_coordinator
            if contrib.event:
                if contrib.event.status != "SCHEDULED":
                    form.add_error("event", "You can only log work for scheduled events.")
                elif not is_coord and not Signup.objects.filter(user=request.user, event=contrib.event, status="CONFIRMED").exists():
                    form.add_error("event", "You must be signed up for this event.")
                else:
                    contrib.user = request.user
                    contrib.save()
                    messages.success(request, "Contribution submitted for approval.")
                    return redirect("hub:dashboard")
            else:
                contrib.user = request.user
                contrib.save()
                messages.success(request, "Contribution submitted for approval.")
                return redirect("hub:dashboard")
    else:
        form = ContributionForm(user=request.user, initial_event=initial_event)
    return render(request, "hub/contribution_create.html", {"form": form})

@login_required
@coordinator_required
def approvals_list(request):
    status_filter = request.GET.get("status") or "PENDING"
    dept_param = request.GET.get("department")
    my_dept = request.user.profile.department
    selected_department, dept_filter_value = None, "all"
    
    if dept_param == "mine" and my_dept:
        selected_department, dept_filter_value = my_dept, "mine"
    elif dept_param and dept_param not in ("all", "mine"):
        selected_department = Department.objects.filter(pk=dept_param).first()
        dept_filter_value = str(selected_department.pk) if selected_department else "all"
    
    qs = Contribution.objects.filter(status=status_filter) if status_filter else Contribution.objects.all()
    if selected_department:
        qs = qs.filter(department=selected_department)
    
    def cnt(s): return Contribution.objects.filter(status=s, department=selected_department).count() if selected_department else Contribution.objects.filter(status=s).count()
    
    return render(request, "hub/approvals_list.html", {
        "contributions": qs.select_related("user", "event", "department", "approved_by").order_by("-created_at"),
        "status_filter": status_filter, "dept_filter_value": dept_filter_value,
        "pending_count": cnt("PENDING"), "approved_count": cnt("APPROVED"), "rejected_count": cnt("REJECTED"),
        "departments": Department.objects.all(), "my_department": my_dept, "selected_department": selected_department,
    })

@login_required
@coordinator_required
def approval_detail(request, pk):
    return render(request, "hub/approval_detail.html", {"contrib": get_object_or_404(Contribution, pk=pk)})

@login_required
@coordinator_required
def approval_approve(request, pk):
    contrib = get_object_or_404(Contribution, pk=pk, status="PENDING")
    contrib.status, contrib.approved_by, contrib.approved_at = "APPROVED", request.user, timezone.now()
    contrib.save()
    messages.success(request, "Contribution approved.")
    return redirect("hub:approvals_list")

@login_required
@coordinator_required
def approval_reject(request, pk):
    contrib = get_object_or_404(Contribution, pk=pk, status="PENDING")
    contrib.status, contrib.approved_by, contrib.approved_at = "REJECTED", request.user, timezone.now()
    contrib.save()
    messages.warning(request, "Contribution rejected.")
    return redirect("hub:approvals_list")

@login_required
@coordinator_required
def all_logs(request):
    status_filter, dept_filter = request.GET.get("status", ""), request.GET.get("department", "")
    qs = Contribution.objects.all().select_related("user", "event", "department", "approved_by")
    if status_filter:
        qs = qs.filter(status=status_filter)
    if dept_filter.isdigit():
        qs = qs.filter(department_id=int(dept_filter))
    return render(request, "hub/all_logs.html", {
        "contributions": qs.order_by("-created_at"),
        "status_filter": status_filter, "dept_filter": dept_filter,
        "pending_count": Contribution.objects.filter(status="PENDING").count(),
        "approved_count": Contribution.objects.filter(status="APPROVED").count(),
        "rejected_count": Contribution.objects.filter(status="REJECTED").count(),
        "departments": Department.objects.all(),
    })

@login_required
@coordinator_required
def log_update_status(request, pk):
    contrib = get_object_or_404(Contribution, pk=pk)
    if request.method == "POST" and (new_status := request.POST.get("status")) in dict(Contribution.STATUS):
        old_status = contrib.status
        contrib.status = new_status
        if new_status in ("APPROVED", "REJECTED") and old_status == "PENDING":
            contrib.approved_by, contrib.approved_at = request.user, timezone.now()
        elif new_status == "PENDING":
            contrib.approved_by, contrib.approved_at = None, None
        contrib.save()
        messages.success(request, f"Log status updated to {new_status}.")
    return redirect("hub:all_logs")

@login_required
def reports(request):
    totals = Contribution.objects.filter(status="APPROVED").values("user__username").annotate(hours=Sum("hours")).order_by("-hours")[:10]
    dept_totals = Contribution.objects.filter(status="APPROVED").values("department__name").annotate(hours=Sum("hours")).order_by("-hours")
    dept_avgs = Contribution.objects.filter(status="APPROVED").values("department__name").annotate(avg=Avg("hours")).order_by("-avg")
    rank_labels, rank_data = [t["user__username"] for t in totals], [float(t["hours"]) for t in totals]
    return render(request, "hub/reports.html", {
        "rank_labels_json": json.dumps(rank_labels), "rank_data_json": json.dumps(rank_data),
        "dept_labels_json": json.dumps([d["department__name"] for d in dept_totals]),
        "dept_data_json": json.dumps([float(d["hours"]) for d in dept_totals]),
        "avg_labels_json": json.dumps([a["department__name"] for a in dept_avgs]),
        "avg_data_json": json.dumps([float(a["avg"]) for a in dept_avgs]),
        "has_rank_data": bool(rank_labels), "has_dept_data": dept_totals.exists(), "has_avg_data": dept_avgs.exists(),
        "total_hours": sum(rank_data), "pending_total": Contribution.objects.filter(status="PENDING").count(),
        "total_contributions": Contribution.objects.count(),
    })
