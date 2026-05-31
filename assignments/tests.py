from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Assignment, Notification, StudentProfile, StudySession
from .services import refresh_notifications


class ASMSModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass123", email="alice@example.com")

    def test_profile_is_created_for_new_user(self):
        self.assertTrue(StudentProfile.objects.filter(user=self.user).exists())

    def test_assignment_overdue_and_completion_state(self):
        assignment = Assignment.objects.create(
            user=self.user,
            title="Past task",
            course_unit="CSC 1001",
            lecturer="Dr. Test",
            deadline=timezone.now() - timedelta(days=1),
            priority=Assignment.PRIORITY_HIGH,
        )
        self.assertTrue(assignment.is_overdue)
        assignment.status = Assignment.STATUS_COMPLETED
        assignment.save()
        self.assertFalse(assignment.is_overdue)
        self.assertIsNotNone(assignment.completed_at)

    def test_study_session_duration(self):
        session = StudySession.objects.create(
            user=self.user,
            subject="Algorithms",
            study_date=timezone.localdate(),
            start_time="10:00",
            end_time="12:30",
        )
        self.assertEqual(session.duration_hours, 2.5)


class ASMSIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="student", password="StrongPass123", email="student@example.com")

    def test_registration_page_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newstudent",
                "full_name": "New Student",
                "registration_number": "REG/001",
                "email": "new@example.com",
                "programme": "Bachelor of Science in Computer Science",
                "year_of_study": "2",
                "password1": "ComplexPass12345",
                "password2": "ComplexPass12345",
            },
            follow=True,
        )
        self.assertContains(response, "Academic Dashboard")
        self.assertTrue(User.objects.filter(username="newstudent").exists())

    def test_authenticated_user_can_create_assignment(self):
        self.client.login(username="student", password="StrongPass123")
        response = self.client.post(
            reverse("assignment_create"),
            {
                "title": "Portfolio",
                "course_unit": "CSC 3000",
                "lecturer": "Dr. Example",
                "deadline": (timezone.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M"),
                "description": "Build ASMS",
                "priority": Assignment.PRIORITY_HIGH,
                "status": Assignment.STATUS_PENDING,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Assignment.objects.filter(user=self.user, title="Portfolio").exists())

    def test_notifications_are_generated(self):
        Assignment.objects.create(
            user=self.user,
            title="Soon",
            course_unit="CSC 2000",
            lecturer="Dr. Reminder",
            deadline=timezone.now() + timedelta(days=1),
        )
        refresh_notifications(self.user)
        self.assertEqual(Notification.objects.filter(user=self.user, notification_type=Notification.TYPE_DEADLINE).count(), 1)

    def test_reports_page_and_pdf_are_protected_and_available(self):
        protected = self.client.get(reverse("reports"))
        self.assertEqual(protected.status_code, 302)
        self.client.login(username="student", password="StrongPass123")
        response = self.client.get(reverse("report_pdf", args=["progress"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
