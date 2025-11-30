from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile
"""
Used Django's signal system to automatically create a Profile whenever
a new User is created.

Signal Flow:
    1. User.objects.create_user(...) is called
    2. Django saves the User to database
    3. post_save signal fires
    4. create_user_profile() receiver is called
    5. Profile is created and linked to the User

Registration:
    This module is imported in hub/apps.py → ready() method
    to ensure signals are connected when Django starts.
"""

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Profile when a new User is created.
    Behavior:
        - New user created → Profile created with defaults (is_coordinator=False)
        - Existing user updated → No action taken
    """
    if created:
        Profile.objects.create(user=instance)








