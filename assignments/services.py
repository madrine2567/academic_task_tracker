from datetime import timedelta

from django.utils import timezone

from .models import Assignment, Notification, StudySession


def _upsert_notification(user, notification_type, title, message, assignment=None, study_session=None):
    lookup = {
        "user": user,
        "notification_type": notification_type,
        "assignment": assignment,
        "study_session": study_session,
    }
    Notification.objects.get_or_create(defaults={"title": title, "message": message}, **lookup)


def refresh_notifications(user):
    now = timezone.now()
    soon = now + timedelta(days=3)

    for assignment in Assignment.objects.filter(user=user, deadline__gte=now, deadline__lte=soon).exclude(status=Assignment.STATUS_COMPLETED):
        _upsert_notification(
            user,
            Notification.TYPE_DEADLINE,
            f"{assignment.title} is due soon",
            f"{assignment.course_unit} is due on {assignment.deadline:%d %b %Y at %H:%M}.",
            assignment=assignment,
        )

    for assignment in Assignment.objects.filter(user=user, deadline__lt=now).exclude(status=Assignment.STATUS_COMPLETED):
        _upsert_notification(
            user,
            Notification.TYPE_OVERDUE,
            f"{assignment.title} is overdue",
            f"{assignment.course_unit} passed its deadline on {assignment.deadline:%d %b %Y at %H:%M}.",
            assignment=assignment,
        )

    today = now.date()
    for session in StudySession.objects.filter(user=user, study_date__gte=today, study_date__lte=today + timedelta(days=1)):
        _upsert_notification(
            user,
            Notification.TYPE_STUDY,
            f"Study session: {session.subject}",
            f"Scheduled for {session.study_date:%d %b %Y}, {session.start_time:%H:%M}-{session.end_time:%H:%M}.",
            study_session=session,
        )
