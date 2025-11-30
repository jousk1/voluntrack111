"""Database models for VolunTrack."""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Department(models.Model):
    # Organizational unit for categorizing events and volunteers
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Profile(models.Model):
    # Extended user profile with coordinator status and department
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_coordinator = models.BooleanField(default=False)
    department = models.ForeignKey(
        Department, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        role = "Coordinator" if self.is_coordinator else "Volunteer"
        return f"{self.user.username} ({role})"

    class Meta:
        ordering = ['user__username']


class Event(models.Model):
    # Volunteer event with signup tracking
    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        Department, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    capacity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="SCHEDULED")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="events_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.date:%Y-%m-%d})"

    def get_confirmed_count(self):
        # Returns the number of confirmed signups
        return self.signups.filter(status="CONFIRMED").count()

    def get_remaining_capacity(self):
        # Returns remaining spots, or None if unlimited
        if self.capacity == 0:
            return None
        return max(0, self.capacity - self.get_confirmed_count())

    def is_full(self):
        # Returns True if event has reached capacity
        if self.capacity == 0:
            return False
        return self.get_confirmed_count() >= self.capacity

    class Meta:
        ordering = ["date"]


class Signup(models.Model):
    # User registration for an event
    STATUS_CHOICES = [
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="signups")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="CONFIRMED")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.event.title} ({self.status})"

    class Meta:
        unique_together = ("user", "event")
        ordering = ["-created_at"]


class Contribution(models.Model):
    # Volunteer hours log with approval workflow
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, null=True, blank=True, on_delete=models.SET_NULL)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default="PENDING")
    approved_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name="contributions_approved"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.hours}h ({self.status})"

    def approve(self, coordinator):
        # Approve this contribution
        self.status = "APPROVED"
        self.approved_by = coordinator
        self.approved_at = timezone.now()
        self.save()

    def reject(self, coordinator, reason=""):
        # Reject this contribution with an optional reason
        self.status = "REJECTED"
        self.approved_by = coordinator
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()

    class Meta:
        ordering = ["-created_at"]
