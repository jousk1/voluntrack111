"""
hub/management/commands/bootstrap.py - Sample Data Bootstrap Command

This custom management command creates initial data for the application.
Useful for setting up a new installation with sample departments and
an initial coordinator user.

Usage:
    python manage.py bootstrap

What It Creates:
    1. Sample departments (Logistics, Outreach, Fundraising, Cleanup)
    2. A coordinator user (username: coordinator, password: coordinator123)

Note:
    - Departments are created with get_or_create (idempotent)
    - Coordinator user is only created if it doesn't exist
    - Safe to run multiple times
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from hub.models import Department


class Command(BaseCommand):
    """
    Django management command to bootstrap sample data.
    
    This command is safe to run multiple times - it uses
    get_or_create for departments and checks existence for users.
    """
    
    help = "Create sample departments and an initial coordinator user"

    def handle(self, *args, **options):
        """
        Execute the bootstrap command.
        
        Creates sample departments and a coordinator user if they don't exist.
        
        Args:
            *args: Positional arguments (unused)
            **options: Command options (unused)
        """
        # ----- CREATE DEPARTMENTS -----
        department_names = ["Logistics", "Outreach", "Fundraising", "Cleanup"]
        
        for name in department_names:
            department, created = Department.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f"  Created department: {name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"✓ {len(department_names)} departments ensured")
        )

        # ----- CREATE COORDINATOR USER -----
        coordinator_username = "coordinator"
        
        if User.objects.filter(username=coordinator_username).exists():
            self.stdout.write(
                self.style.WARNING(f"  Coordinator user '{coordinator_username}' already exists")
            )
        else:
            # Create the user
            user = User.objects.create_user(
                username=coordinator_username,
                password="coordinator123",
                first_name="Club",
                last_name="Lead"
            )
            
            # Profile is created automatically via signal
            # Update it to make this user a coordinator
            user.refresh_from_db()  # Ensure profile is attached
            user.profile.is_coordinator = True
            user.profile.department = Department.objects.first()
            user.profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ Coordinator user created: {coordinator_username} / coordinator123")
            )

        # Final summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Bootstrap complete!"))
        self.stdout.write(f"  Departments: {Department.objects.count()}")
        self.stdout.write(f"  Users: {User.objects.count()}")
        self.stdout.write(f"  Coordinators: {User.objects.filter(profile__is_coordinator=True).count()}")
