from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from assignments.models import Assignment, StudentProfile, StudySession


class Command(BaseCommand):
    help = "Create sample ASMS data for demos and testing."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="student",
            defaults={"first_name": "Demo", "last_name": "Student", "email": "student@example.com"},
        )
        if created:
            user.set_password("Student@12345")
            user.save()

        StudentProfile.objects.update_or_create(
            user=user,
            defaults={
                "registration_number": "ASMS/2026/001",
                "programme": "Bachelor of Science in Computer Science",
                "year_of_study": 3,
            },
        )

        samples = [
            ("Database ER Diagram", "CSC 3204 Database Systems", "Dr. Amina Kato", 2, Assignment.PRIORITY_HIGH, Assignment.STATUS_IN_PROGRESS),
            ("Software Engineering Report", "CSC 3102 Software Engineering", "Mr. Peter Okello", 5, Assignment.PRIORITY_MEDIUM, Assignment.STATUS_PENDING),
            ("AI Lab Exercise", "CSC 3301 Artificial Intelligence", "Dr. Grace Nsubuga", -1, Assignment.PRIORITY_HIGH, Assignment.STATUS_PENDING),
            ("Web Security Reflection", "CSC 3208 Web Development", "Ms. Sarah Nakimuli", 8, Assignment.PRIORITY_LOW, Assignment.STATUS_COMPLETED),
        ]
        for title, course, lecturer, offset, priority, status in samples:
            Assignment.objects.update_or_create(
                user=user,
                title=title,
                course_unit=course,
                defaults={
                    "lecturer": lecturer,
                    "deadline": timezone.now() + timedelta(days=offset),
                    "description": f"Complete and submit {title.lower()} for {course}.",
                    "priority": priority,
                    "status": status,
                },
            )

        today = timezone.localdate()
        StudySession.objects.update_or_create(
            user=user,
            subject="Database Systems revision",
            study_date=today,
            start_time="18:00",
            defaults={"end_time": "20:00", "notes": "Normalize schema and revise SQL joins."},
        )
        StudySession.objects.update_or_create(
            user=user,
            subject="Software Engineering documentation",
            study_date=today + timedelta(days=1),
            start_time="09:00",
            defaults={"end_time": "11:30", "notes": "Prepare diagrams and testing evidence."},
        )

        self.stdout.write(self.style.SUCCESS("Seed data ready. Login with username 'student' and password 'Student@12345'."))
