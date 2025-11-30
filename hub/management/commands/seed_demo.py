"""
hub/management/commands/seed_demo.py - Demo Data Seeder

Creates rich, realistic demo data for screenshots and product demos.

Usage:
    python manage.py seed_demo

What It Creates:
    - 6 departments with distinct purposes
    - 1 admin coordinator + 2 department coordinators
    - 10 volunteers with realistic names
    - 12 events (past completed, upcoming, one cancelled)
    - Signups for events
    - Contributions in all states (pending, approved, rejected)
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from hub.models import Contribution, Department, Event, Profile, Signup


class Command(BaseCommand):
    help = "Seed database with rich demo data for screenshots"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n🌱 Seeding Demo Data...\n"))

        # Clear existing data (optional - be careful in production!)
        self.stdout.write("  Clearing existing demo data...")
        Contribution.objects.all().delete()
        Signup.objects.all().delete()
        Event.objects.all().delete()
        # Keep superusers, delete others
        User.objects.filter(is_superuser=False).delete()
        Department.objects.all().delete()

        # Create departments
        departments = self.create_departments()
        
        # Create users
        coordinators, volunteers = self.create_users(departments)
        
        # Create events
        events = self.create_events(coordinators, departments)
        
        # Create signups
        self.create_signups(events, volunteers)
        
        # Create contributions
        self.create_contributions(volunteers, coordinators, departments, events)

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("✅ Demo Data Seeding Complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"  📁 Departments: {Department.objects.count()}")
        self.stdout.write(f"  👥 Users: {User.objects.count()}")
        self.stdout.write(f"     - Coordinators: {User.objects.filter(profile__is_coordinator=True).count()}")
        self.stdout.write(f"     - Volunteers: {User.objects.filter(profile__is_coordinator=False).count()}")
        self.stdout.write(f"  📅 Events: {Event.objects.count()}")
        self.stdout.write(f"  ✍️  Signups: {Signup.objects.count()}")
        self.stdout.write(f"  📊 Contributions: {Contribution.objects.count()}")
        self.stdout.write("")
        # Create easy login users
        self.create_easy_logins(departments)
        
        self.stdout.write(self.style.WARNING("Login credentials:"))
        self.stdout.write("  Coordinator: Coordinator / 1")
        self.stdout.write("  Volunteer:   Volunteer / 1")
        self.stdout.write("")

    def create_departments(self):
        """Create diverse departments."""
        dept_data = [
            "Community Outreach",
            "Environmental Cleanup", 
            "Food Bank Services",
            "Youth Mentorship",
            "Senior Support",
            "Event Logistics",
        ]
        
        departments = []
        for name in dept_data:
            dept = Department.objects.create(name=name)
            departments.append(dept)
            self.stdout.write(f"  ✓ Department: {name}")
        
        return departments

    def create_users(self, departments):
        """Create coordinators and volunteers."""
        # Coordinator data: (username, first, last, department_index)
        coord_data = [
            ("sarah.mitchell", "Sarah", "Mitchell", 0),  # Community Outreach
            ("mike.chen", "Mike", "Chen", 1),   # Environmental Cleanup
            ("lisa.rodriguez", "Lisa", "Rodriguez", 2),  # Food Bank
        ]
        
        coordinators = []
        for username, first, last, dept_idx in coord_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@volunteerorg.org",
                    "first_name": first,
                    "last_name": last
                }
            )
            if created:
                user.set_password("coord123")
                user.save()
            user.profile.is_coordinator = True
            user.profile.department = departments[dept_idx]
            user.profile.phone = f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"
            user.profile.save()
            coordinators.append(user)
            self.stdout.write(f"  ✓ Coordinator: {first} {last} ({username})")

        # Volunteer data: (username, first, last)
        vol_data = [
            ("emma.wilson", "Emma", "Wilson"),
            ("james.taylor", "James", "Taylor"),
            ("sophia.martinez", "Sophia", "Martinez"),
            ("noah.johnson", "Noah", "Johnson"),
            ("olivia.brown", "Olivia", "Brown"),
            ("liam.davis", "Liam", "Davis"),
            ("ava.garcia", "Ava", "Garcia"),
            ("mason.miller", "Mason", "Miller"),
            ("isabella.jones", "Isabella", "Jones"),
            ("ethan.williams", "Ethan", "Williams"),
        ]
        
        volunteers = []
        for username, first, last in vol_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@email.com",
                    "first_name": first,
                    "last_name": last
                }
            )
            if created:
                user.set_password("volunteer123")
                user.save()
            user.profile.department = random.choice(departments)
            user.profile.phone = f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"
            user.profile.save()
            volunteers.append(user)
            self.stdout.write(f"  ✓ Volunteer: {first} {last}")

        return coordinators, volunteers

    def create_events(self, coordinators, departments):
        """Create a variety of events."""
        now = timezone.now()
        
        # Event data: (title, description, location, dept_idx, days_offset, capacity, status, creator_idx)
        event_data = [
            # Past completed events
            ("Beach Cleanup Day", "Join us for our monthly beach cleanup! Gloves and bags provided.", 
             "Sunset Beach", 1, -30, 25, "COMPLETED", 1),
            ("Food Drive Collection", "Help sort and package donated food items for local families.",
             "Community Center", 2, -21, 20, "COMPLETED", 2),
            ("Senior Tech Workshop", "Teach seniors how to use smartphones and tablets.",
             "Riverside Library", 4, -14, 15, "COMPLETED", 0),
            ("Park Restoration", "Plant trees and restore native vegetation in Central Park.",
             "Central Park", 1, -7, 30, "COMPLETED", 1),
            
            # Upcoming events
            ("Youth Tutoring Session", "Help middle school students with homework and test prep.",
             "Lincoln Middle School", 3, 3, 12, "SCHEDULED", 0),
            ("Homeless Shelter Meal Service", "Prepare and serve meals at the downtown shelter.",
             "Hope Shelter", 2, 5, 20, "SCHEDULED", 2),
            ("River Trail Cleanup", "Clear debris and maintain hiking trails along the river.",
             "River Trail Head", 1, 7, 25, "SCHEDULED", 1),
            ("Senior Center Visit", "Spend time with seniors - games, conversation, and activities.",
             "Golden Years Center", 4, 10, 15, "SCHEDULED", 0),
            ("Charity Fun Run Setup", "Help set up water stations and signage for the charity run.",
             "City Stadium", 5, 12, 40, "SCHEDULED", 0),
            ("Community Garden Planting", "Spring planting day at the community garden.",
             "Oak Street Garden", 1, 14, 20, "SCHEDULED", 1),
            ("Back to School Supply Drive", "Sort and distribute school supplies to students in need.",
             "Community Center", 0, 21, 30, "SCHEDULED", 0),
            
            # Cancelled event
            ("Outdoor Movie Night", "Family movie night in the park - CANCELLED due to weather.",
             "Memorial Park", 0, 2, 100, "CANCELLED", 0),
        ]
        
        events = []
        for title, desc, location, dept_idx, days, capacity, status, creator_idx in event_data:
            event = Event.objects.create(
                title=title,
                description=desc,
                location=location,
                department=departments[dept_idx],
                date=now + timedelta(days=days, hours=random.randint(9, 17)),
                capacity=capacity,
                status=status,
                created_by=coordinators[creator_idx]
            )
            events.append(event)
            status_emoji = {"COMPLETED": "✅", "SCHEDULED": "📅", "CANCELLED": "❌"}
            self.stdout.write(f"  {status_emoji[status]} Event: {title}")

        return events

    def create_signups(self, events, volunteers):
        """Create event signups."""
        signup_count = 0
        
        for event in events:
            if event.status == "CANCELLED":
                continue
                
            # Random subset of volunteers sign up for each event
            num_signups = random.randint(3, min(8, len(volunteers)))
            event_volunteers = random.sample(volunteers, num_signups)
            
            for volunteer in event_volunteers:
                Signup.objects.create(
                    user=volunteer,
                    event=event,
                    status="CONFIRMED"
                )
                signup_count += 1

        self.stdout.write(f"  ✓ Created {signup_count} event signups")

    def create_contributions(self, volunteers, coordinators, departments, events):
        """Create contributions in various states."""
        now = timezone.now()
        
        # Descriptions for variety
        descriptions = [
            "Helped with setup and registration.",
            "Assisted with cleanup and organization.",
            "Worked directly with participants.",
            "Supported logistics and coordination.",
            "Provided administrative support.",
            "Led a small team of volunteers.",
            "Handled equipment and supplies.",
            "Greeted visitors and answered questions.",
            "Assisted with food preparation and serving.",
            "Helped with event photography and social media.",
        ]

        pending_count = 0
        approved_count = 0
        rejected_count = 0

        # Create approved contributions (past events)
        past_events = [e for e in events if e.status == "COMPLETED"]
        for event in past_events:
            signups = Signup.objects.filter(event=event)
            for signup in signups:
                hours = Decimal(str(random.choice([2, 2.5, 3, 3.5, 4, 4.5, 5, 6])))
                contrib = Contribution.objects.create(
                    user=signup.user,
                    event=event,
                    department=event.department,
                    date=event.date.date(),
                    hours=hours,
                    description=random.choice(descriptions),
                    status="APPROVED",
                    approved_by=random.choice(coordinators),
                    approved_at=event.date + timedelta(days=random.randint(1, 3))
                )
                approved_count += 1

        # Create some pending contributions (recent work)
        for _ in range(8):
            volunteer = random.choice(volunteers)
            dept = random.choice(departments)
            hours = Decimal(str(random.choice([1.5, 2, 2.5, 3, 3.5, 4])))
            days_ago = random.randint(0, 5)
            
            Contribution.objects.create(
                user=volunteer,
                department=dept,
                date=(now - timedelta(days=days_ago)).date(),
                hours=hours,
                description=random.choice(descriptions),
                status="PENDING"
            )
            pending_count += 1

        # Create a couple rejected contributions
        rejection_reasons = [
            "Hours claimed exceed the event duration. Please submit with corrected hours.",
            "This contribution was already logged under a different entry. Please check your records.",
            "Unable to verify attendance. Please contact your coordinator.",
        ]
        
        for _ in range(3):
            volunteer = random.choice(volunteers)
            dept = random.choice(departments)
            
            Contribution.objects.create(
                user=volunteer,
                department=dept,
                date=(now - timedelta(days=random.randint(7, 14))).date(),
                hours=Decimal(str(random.choice([8, 10, 12]))),  # Suspiciously high
                description="Helped with various activities throughout the day.",
                status="REJECTED",
                approved_by=random.choice(coordinators),
                approved_at=now - timedelta(days=random.randint(3, 6)),
                rejection_reason=random.choice(rejection_reasons)
            )
            rejected_count += 1

        # Add some extra approved contributions for top volunteers (for leaderboard variety)
        top_volunteers = random.sample(volunteers, 4)
        for volunteer in top_volunteers:
            for _ in range(random.randint(2, 5)):
                dept = random.choice(departments)
                days_ago = random.randint(15, 60)
                hours = Decimal(str(random.choice([3, 4, 5, 6])))
                
                Contribution.objects.create(
                    user=volunteer,
                    department=dept,
                    date=(now - timedelta(days=days_ago)).date(),
                    hours=hours,
                    description=random.choice(descriptions),
                    status="APPROVED",
                    approved_by=random.choice(coordinators),
                    approved_at=now - timedelta(days=days_ago - 2)
                )
                approved_count += 1

        self.stdout.write(f"  ✓ Contributions: {approved_count} approved, {pending_count} pending, {rejected_count} rejected")

    def create_easy_logins(self, departments):
        """Create simple login users for demos with sample data."""
        now = timezone.now()
        
        # Coordinator user
        coord, created = User.objects.get_or_create(
            username="Coordinator",
            defaults={
                "email": "coordinator@demo.com",
                "first_name": "Demo",
                "last_name": "Coordinator"
            }
        )
        coord.set_password("1")
        coord.save()
        coord.profile.is_coordinator = True
        coord.profile.department = departments[0]
        coord.profile.save()
        self.stdout.write(f"  ✓ Easy login: Coordinator / 1")

        # Volunteer user
        vol, created = User.objects.get_or_create(
            username="Volunteer",
            defaults={
                "email": "volunteer@demo.com",
                "first_name": "Alex",
                "last_name": "Demo"
            }
        )
        vol.set_password("1")
        vol.save()
        vol.profile.is_coordinator = False
        vol.profile.department = departments[1]
        vol.profile.save()
        self.stdout.write(f"  ✓ Easy login: Volunteer / 1")

        # Get some upcoming events for the volunteer to sign up for
        upcoming_events = Event.objects.filter(status="SCHEDULED").order_by("date")[:3]
        for event in upcoming_events:
            Signup.objects.get_or_create(user=vol, event=event, defaults={"status": "CONFIRMED"})
        self.stdout.write(f"  ✓ Volunteer signed up for {upcoming_events.count()} events")

        # Create approved contributions for the volunteer (past work)
        contribution_data = [
            (departments[0], 4, 14, "Helped organize community outreach materials and greeted visitors."),
            (departments[1], 3.5, 21, "Participated in river cleanup, collected 2 bags of trash."),
            (departments[2], 5, 28, "Sorted and packaged food donations for 50 families."),
            (departments[3], 2.5, 35, "Tutored 3 middle school students in math."),
            (departments[0], 4, 42, "Assisted with senior center activities and games."),
            (departments[1], 3, 7, "Helped plant trees at the community garden."),
        ]
        
        for dept, hours, days_ago, desc in contribution_data:
            Contribution.objects.create(
                user=vol,
                department=dept,
                date=(now - timedelta(days=days_ago)).date(),
                hours=Decimal(str(hours)),
                description=desc,
                status="APPROVED",
                approved_by=coord,
                approved_at=now - timedelta(days=days_ago - 2)
            )
        self.stdout.write(f"  ✓ Volunteer has {len(contribution_data)} approved contributions")

        # Create pending contributions for the volunteer
        pending_data = [
            (departments[1], 3, 1, "Helped with park restoration and trail maintenance."),
            (departments[2], 2.5, 3, "Assisted with meal service at the homeless shelter."),
        ]
        
        for dept, hours, days_ago, desc in pending_data:
            Contribution.objects.create(
                user=vol,
                department=dept,
                date=(now - timedelta(days=days_ago)).date(),
                hours=Decimal(str(hours)),
                description=desc,
                status="PENDING"
            )
        self.stdout.write(f"  ✓ Volunteer has {len(pending_data)} pending contributions")

