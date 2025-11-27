from django.contrib import admin
from .models import Department, Profile, Event, Signup, Contribution

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_coordinator", "department")

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "date", "location", "capacity")
    list_filter = ("department",)

@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status", "created_at")

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "hours", "status", "approved_by", "approved_at", "created_at")
    list_filter = ("status", "department")
