"""
hub/admin.py - Django Admin Configuration

This module configures the Django admin interface for managing
VolunTrack data through a web-based GUI at /admin/.

Admin Features:
    - CRUD operations for all models
    - Filtering and searching
    - Bulk actions
    - Inline editing

Custom Configurations:
    - ProfileInline: Edit Profile directly on User admin page
    - List display columns for quick overview
    - List filters for narrowing results
    - Search fields for finding records
    - List editable for quick changes

Access:
    Admin interface is available at /admin/
    Only users with is_staff=True can access it.
    Superusers have full access to all models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Contribution, Department, Event, Profile, Signup


# =============================================================================
# USER ADMIN WITH PROFILE INLINE
# =============================================================================

class ProfileInline(admin.StackedInline):
    """
    Inline admin for Profile model.
    
    Allows editing a user's Profile directly on the User admin page,
    instead of having to navigate to a separate Profile page.
    
    Displays:
        - is_coordinator checkbox
        - department dropdown
        - phone field
    """
    model = Profile
    can_delete = False  # Prevent accidental Profile deletion
    verbose_name_plural = 'Profile'
    fields = ('is_coordinator', 'department', 'phone')


class UserAdmin(BaseUserAdmin):
    """
    Extended User admin with Profile inline.
    
    Inherits all default User admin functionality and adds
    the ProfileInline for editing profiles on the same page.
    """
    inlines = (ProfileInline,)


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# =============================================================================
# DEPARTMENT ADMIN
# =============================================================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Department model.
    
    Simple admin with just the name field.
    Used to create/edit volunteer departments.
    """
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


# =============================================================================
# PROFILE ADMIN
# =============================================================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for Profile model.
    
    Provides quick access to manage user profiles, especially
    useful for promoting users to coordinator status.
    
    Features:
        - list_editable: Toggle is_coordinator directly in list view
        - list_filter: Filter by coordinator status or department
        - search_fields: Find users by name or email
    """
    list_display = ("user", "is_coordinator", "department", "phone")
    list_filter = ("is_coordinator", "department")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    list_editable = ("is_coordinator",)  # Quick toggle in list view
    raw_id_fields = ("user",)  # Better UX for large user lists
    ordering = ("user__username",)


# =============================================================================
# EVENT ADMIN
# =============================================================================

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Admin configuration for Event model.
    
    Allows administrators to manage volunteer events,
    view signup counts, and update event status.
    """
    list_display = ("title", "department", "date", "location", "capacity", "status", "created_by")
    list_filter = ("status", "department", "date")
    search_fields = ("title", "description", "location")
    date_hierarchy = "date"  # Date-based navigation
    ordering = ("-date",)
    raw_id_fields = ("created_by",)


# =============================================================================
# SIGNUP ADMIN
# =============================================================================

@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    """
    Admin configuration for Signup model.
    
    Provides visibility into event registrations.
    Useful for troubleshooting signup issues.
    """
    list_display = ("user", "event", "status", "created_at")
    list_filter = ("status", "created_at", "event")
    search_fields = ("user__username", "event__title")
    raw_id_fields = ("user", "event")
    ordering = ("-created_at",)


# =============================================================================
# CONTRIBUTION ADMIN
# =============================================================================

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Contribution model.
    
    Primary admin for managing volunteer hour logs.
    Coordinators can use this to review, approve, or reject contributions.
    
    Features:
        - Filter by status for quick access to pending items
        - Date hierarchy for finding contributions by date
        - Search by user or description
    """
    list_display = ("user", "event", "department", "hours", "status", "date", "approved_by")
    list_filter = ("status", "department", "date")
    search_fields = ("user__username", "description", "rejection_reason")
    date_hierarchy = "date"
    ordering = ("-created_at",)
    raw_id_fields = ("user", "approved_by", "event")
    
    # Read-only fields that shouldn't be manually edited
    readonly_fields = ("created_at", "approved_at")
