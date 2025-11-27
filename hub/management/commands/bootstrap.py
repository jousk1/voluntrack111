from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hub.models import Department

class Command(BaseCommand):
    help = "Create sample departments and a coordinator user"

    def handle(self, *args, **options):
        depts = ["Logistics", "Outreach", "Fundraising", "Cleanup"]
        for name in depts:
            Department.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Departments ensured."))

        if not User.objects.filter(username="coordinator").exists():
            u = User.objects.create_user(username="coordinator", password="coordinator123", first_name="Club", last_name="Lead")
            # Profile is created via signal
            u.refresh_from_db()  # ensure profile is attached
            u.profile.is_coordinator = True
            u.profile.department = Department.objects.first()
            u.profile.save()
            self.stdout.write(self.style.SUCCESS("Coordinator user: coordinator / coordinator123"))
        else:
            self.stdout.write(self.style.WARNING("Coordinator user already exists."))
