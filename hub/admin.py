"""Django Admin Configuration for VolunTrack."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Contribution, Department, Event, Profile, Signup


# USER ADMIN WITH PROFILE INLINE

class ProfileInline(admin.StackedInline):
    # Inline admin for Profile - edit profile on User page
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('is_coordinator', 'department', 'phone')


class UserAdmin(BaseUserAdmin):
    # Extended User admin with Profile inline
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# DEPARTMENT ADMIN

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


# PROFILE ADMIN

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_coordinator", "department", "phone")
    list_filter = ("is_coordinator", "department")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    list_editable = ("is_coordinator",)
    raw_id_fields = ("user",)
    ordering = ("user__username",)


# EVENT ADMIN

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "date", "location", "capacity", "status", "created_by")
    list_filter = ("status", "department", "date")
    search_fields = ("title", "description", "location")
    date_hierarchy = "date"
    ordering = ("-date",)
    raw_id_fields = ("created_by",)


# SIGNUP ADMIN

@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status", "created_at")
    list_filter = ("status", "created_at", "event")
    search_fields = ("user__username", "event__title")
    raw_id_fields = ("user", "event")
    ordering = ("-created_at",)


# CONTRIBUTION ADMIN

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "department", "hours", "status", "date", "approved_by")
    list_filter = ("status", "department", "date")
    search_fields = ("user__username", "description", "rejection_reason")
    date_hierarchy = "date"
    ordering = ("-created_at",)
    raw_id_fields = ("user", "approved_by", "event")
    readonly_fields = ("created_at", "approved_at")
