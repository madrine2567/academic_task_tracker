from django.contrib import admin

from .models import Assignment, Notification, StudentProfile, StudySession


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "registration_number", "programme", "year_of_study")
    search_fields = ("user__username", "user__first_name", "user__last_name", "registration_number", "programme")
    list_filter = ("year_of_study", "programme")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "course_unit", "lecturer", "deadline", "priority", "status", "is_overdue")
    list_filter = ("status", "priority", "course_unit")
    search_fields = ("title", "course_unit", "lecturer", "description", "user__username")
    readonly_fields = ("created_at", "updated_at", "completed_at")
    date_hierarchy = "deadline"

    @admin.display(boolean=True, description="Overdue")
    def is_overdue(self, obj):
        return obj.is_overdue


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ("subject", "user", "study_date", "start_time", "end_time", "duration_hours")
    list_filter = ("study_date", "subject")
    search_fields = ("subject", "notes", "user__username")
    date_hierarchy = "study_date"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "notification_type", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("title", "message", "user__username")
