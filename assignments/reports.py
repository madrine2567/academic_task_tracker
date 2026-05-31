from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from django.utils import timezone

from .models import Assignment, StudySession


def _doc(response, title):
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"Academic Success Management System - {title}", styles["Title"]), Spacer(1, 16)]
    return doc, styles, story


def _table(rows):
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12355b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d5dde5")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fb")]),
            ]
        )
    )
    return table


def build_assignment_pdf(response, user):
    doc, styles, story = _doc(response, "Assignment Report")
    story.append(Paragraph(f"Student: {user.get_full_name() or user.username}", styles["Normal"]))
    rows = [["Title", "Course", "Lecturer", "Deadline", "Priority", "Status"]]
    for item in Assignment.objects.filter(user=user):
        rows.append([item.title, item.course_unit, item.lecturer, item.deadline.strftime("%d %b %Y %H:%M"), item.get_priority_display(), item.get_status_display()])
    story.extend([Spacer(1, 12), _table(rows)])
    doc.build(story)


def build_progress_pdf(response, user):
    doc, styles, story = _doc(response, "Progress Report")
    assignments = Assignment.objects.filter(user=user)
    total = assignments.count()
    completed = assignments.filter(status=Assignment.STATUS_COMPLETED).count()
    overdue = assignments.filter(status__in=[Assignment.STATUS_PENDING, Assignment.STATUS_IN_PROGRESS], deadline__lt=timezone.now()).count()
    rows = [
        ["Metric", "Value"],
        ["Total assignments", total],
        ["Completed assignments", completed],
        ["Pending or in progress", total - completed],
        ["Overdue assignments", overdue],
        ["Completion rate", f"{round((completed / total) * 100, 1) if total else 0}%"],
    ]
    story.extend([Paragraph(f"Student: {user.get_full_name() or user.username}", styles["Normal"]), Spacer(1, 12), _table(rows)])
    doc.build(story)


def build_study_pdf(response, user):
    doc, styles, story = _doc(response, "Study Report")
    rows = [["Subject", "Date", "Start", "End", "Hours", "Notes"]]
    for session in StudySession.objects.filter(user=user):
        rows.append([session.subject, session.study_date.strftime("%d %b %Y"), session.start_time.strftime("%H:%M"), session.end_time.strftime("%H:%M"), session.duration_hours, session.notes[:80]])
    story.extend([Paragraph(f"Student: {user.get_full_name() or user.username}", styles["Normal"]), Spacer(1, 12), _table(rows)])
    doc.build(story)
