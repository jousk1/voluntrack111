"""
Models:
    - Department: Organizational units for categorizing events and volunteers
    - Profile: Extended user data (coordinator status, department assignment)
    - Event: Volunteer events with signup tracking
    - Signup: User-event relationship tracking
    - Contribution: Volunteer hours logging with approval workflow

Database Relationships:
    User (Django built-in)
      └── Profile (OneToOne) - Every user has exactly one profile
           └── Department (ForeignKey, optional)
    
    Event
      ├── Department (ForeignKey, optional)
      ├── User/created_by (ForeignKey)
      └── Signup (reverse relationship via related_name="signups")
    
    Signup
      ├── User (ForeignKey)
      └── Event (ForeignKey)
    
    Contribution
      ├── User (ForeignKey) - Who logged the hours
      ├── Event (ForeignKey, optional) - Associated event
      ├── Department (ForeignKey, required)
      └── User/approved_by (ForeignKey, optional) - Who approved it
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Profile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        help_text="The Django user this profile belongs to"
    )
    is_coordinator = models.BooleanField(
        default=False,
        help_text="Coordinators have elevated permissions (create events, approve logs)"
    )
    department = models.ForeignKey(
        Department, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        help_text="Optional department assignment for this user"
    )
    phone = models.CharField(
        max_length=30, 
        blank=True,
        help_text="Optional contact phone number"
    )

    def __str__(self):
        role = "Coordinator" if self.is_coordinator else "Volunteer"
        return f"{self.user.username} ({role})"

    class Meta:
        ordering = ['user__username']


class Event(models.Model):
    # Status choices for event lifecycle
    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    title = models.CharField(
        max_length=200,
        help_text="Name of the volunteer event"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the event"
    )
    department = models.ForeignKey(
        Department, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        help_text="Optional department this event belongs to"
    )
    date = models.DateTimeField(
        help_text="When the event takes place"
    )
    location = models.CharField(
        max_length=200,
        help_text="Where the event takes place"
    )
    capacity = models.PositiveIntegerField(
        default=0,
        help_text="Maximum number of signups (0 = unlimited)"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default="SCHEDULED",
        help_text="Current status in event lifecycle"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="events_created",
        help_text="Coordinator who created this event"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this event was created"
    )

    def __str__(self):
        return f"{self.title} ({self.date:%Y-%m-%d})"

    def get_confirmed_count(self):
        """Returns the number of confirmed signups for this event."""
        return self.signups.filter(status="CONFIRMED").count()

    def get_remaining_capacity(self):
        """Returns remaining spots, or None if unlimited."""
        if self.capacity == 0:
            return None  # Unlimited
        return max(0, self.capacity - self.get_confirmed_count())

    def is_full(self):
        """Returns True if event has reached capacity."""
        if self.capacity == 0:
            return False  # Unlimited capacity
        return self.get_confirmed_count() >= self.capacity

    class Meta:
        ordering = ["date"]


class Signup(models.Model):
    STATUS_CHOICES = [
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="The volunteer who signed up"
    )
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name="signups",
        help_text="The event being signed up for"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default="CONFIRMED",
        help_text="Current signup status"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this signup was created"
    )

    def __str__(self):
        return f"{self.user.username} → {self.event.title} ({self.status})"

    class Meta:
        # Prevent duplicate signups - one user can only sign up once per event
        unique_together = ("user", "event")
        ordering = ["-created_at"]


class Contribution(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="The volunteer who logged this contribution"
    )
    event = models.ForeignKey(
        Event, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        help_text="Optional associated event (null for non-event work)"
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE,
        help_text="Department this work was performed for"
    )
    date = models.DateField(
        default=timezone.now,
        help_text="Date when the volunteer work was performed"
    )
    hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Number of hours worked (e.g., 2.5 for 2 hours 30 minutes)"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of work performed"
    )
    status = models.CharField(
        max_length=8, 
        choices=STATUS_CHOICES, 
        default="PENDING",
        help_text="Current approval status"
    )
    approved_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name="contributions_approved",
        help_text="Coordinator who reviewed this contribution"
    )
    approved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this contribution was reviewed"
    )
    rejection_reason = models.TextField(
        blank=True, 
        help_text="Reason for rejection (if applicable)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this contribution was submitted"
    )

    def __str__(self):
        return f"{self.user.username}: {self.hours}h ({self.status})"

    def approve(self, coordinator):
        """
        Approve this contribution.
        
        Args:
            coordinator: The User object of the coordinator approving
        """
        self.status = "APPROVED"
        self.approved_by = coordinator
        self.approved_at = timezone.now()
        self.save()

    def reject(self, coordinator, reason=""):
        """
        Reject this contribution with an optional reason.
        
        Args:
            coordinator: The User object of the coordinator rejecting
            reason: Explanation for the rejection
        """
        self.status = "REJECTED"
        self.approved_by = coordinator
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()

    class Meta:
        ordering = ["-created_at"]
