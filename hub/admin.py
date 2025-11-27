from django.contrib import admin
from .models import Department, Profile, Event, Signup, Contribution

@admin.register(Department, Profile)
class SimpleAdmin(admin.ModelAdmin):
    pass

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "date", "status")

@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status")

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "hours", "status", "approved_by")
    list_filter = ("status", "department")
