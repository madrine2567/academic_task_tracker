from datetime import datetime, time

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class StudentProfile(models.Model):
    YEAR_CHOICES = [
        (1, "Year 1"),
        (2, "Year 2"),
        (3, "Year 3"),
        (4, "Year 4"),
        (5, "Year 5"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    registration_number = models.CharField(max_length=40, unique=True)
    programme = models.CharField(max_length=120, default="Bachelor of Science in Computer Science")
    year_of_study = models.PositiveSmallIntegerField(choices=YEAR_CHOICES, default=1)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name"]
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.registration_number}"


class Assignment(models.Model):
    PRIORITY_HIGH = "high"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_LOW = "low"
    PRIORITY_CHOICES = [
        (PRIORITY_HIGH, "High"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_LOW, "Low"),
    ]

    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_OVERDUE = "overdue"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_OVERDUE, "Overdue"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    course_unit = models.CharField(max_length=120)
    lecturer = models.CharField(max_length=120)
    deadline = models.DateTimeField()
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["deadline", "-priority"]
        indexes = [
            models.Index(fields=["user", "deadline"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "priority"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["user", "title", "course_unit"], name="unique_assignment_per_course"),
        ]

    def __str__(self):
        return f"{self.title} ({self.course_unit})"

    def clean(self):
        if self.status == self.STATUS_COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        if self.created_at and self.completed_at and self.completed_at < self.created_at:
            raise ValidationError("Completion date cannot be before creation date.")

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        if self.status != self.STATUS_COMPLETED:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        return self.status == self.STATUS_COMPLETED

    @property
    def is_overdue(self):
        return self.deadline < timezone.now() and self.status != self.STATUS_COMPLETED

    @property
    def effective_status(self):
        return self.STATUS_OVERDUE if self.is_overdue else self.status

    @property
    def days_until_due(self):
        return (self.deadline - timezone.now()).days

    @property
    def priority_badge_class(self):
        return {
            self.PRIORITY_HIGH: "danger",
            self.PRIORITY_MEDIUM: "warning",
            self.PRIORITY_LOW: "success",
        }.get(self.priority, "secondary")

    @property
    def status_badge_class(self):
        return {
            self.STATUS_PENDING: "secondary",
            self.STATUS_IN_PROGRESS: "primary",
            self.STATUS_COMPLETED: "success",
            self.STATUS_OVERDUE: "danger",
        }.get(self.effective_status, "secondary")


class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="study_sessions")
    subject = models.CharField(max_length=120)
    study_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["study_date", "start_time"]
        indexes = [models.Index(fields=["user", "study_date"])]

    def __str__(self):
        return f"{self.subject} on {self.study_date}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be later than start time.")

    @property
    def duration_hours(self):
        start_time = time.fromisoformat(self.start_time) if isinstance(self.start_time, str) else self.start_time
        end_time = time.fromisoformat(self.end_time) if isinstance(self.end_time, str) else self.end_time
        start = datetime.combine(self.study_date, start_time)
        end = datetime.combine(self.study_date, end_time)
        return round((end - start).seconds / 3600, 2)


class Notification(models.Model):
    TYPE_DEADLINE = "deadline"
    TYPE_OVERDUE = "overdue"
    TYPE_STUDY = "study"
    TYPE_CHOICES = [
        (TYPE_DEADLINE, "Upcoming Deadline"),
        (TYPE_OVERDUE, "Overdue Assignment"),
        (TYPE_STUDY, "Study Reminder"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, blank=True, null=True, related_name="notifications")
    study_session = models.ForeignKey(StudySession, on_delete=models.CASCADE, blank=True, null=True, related_name="notifications")
    title = models.CharField(max_length=160)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "created_at"])]

    def __str__(self):
        return self.title
