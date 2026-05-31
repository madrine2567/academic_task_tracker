import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AssignmentForm,
    AssignmentSearchForm,
    ProfileUpdateForm,
    StudentRegistrationForm,
    StudySessionForm,
    StyledPasswordChangeForm,
    UserUpdateForm,
)
from .models import Assignment, Notification, StudentProfile, StudySession
from .reports import build_assignment_pdf, build_progress_pdf, build_study_pdf
from .services import refresh_notifications


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created successfully.")
        return redirect("dashboard")
    return render(request, "assignments/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = AuthenticationForm(request, data=request.POST or None)
    for field in form.fields.values():
        field.widget.attrs["class"] = "form-control"
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect(request.GET.get("next") or "dashboard")
    return render(request, "assignments/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


@login_required
def dashboard_view(request):
    refresh_notifications(request.user)
    now = timezone.now()
    assignments = Assignment.objects.filter(user=request.user)
    sessions = StudySession.objects.filter(user=request.user)
    week_start = now.date() - timedelta(days=now.weekday())

    priority_counts = {
        item["priority"]: item["count"]
        for item in assignments.values("priority").annotate(count=Count("id"))
    }
    trend_rows = (
        assignments.filter(completed_at__isnull=False)
        .annotate(day=TruncDate("completed_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    weekly_sessions = sessions.filter(study_date__gte=week_start, study_date__lte=week_start + timedelta(days=6))
    weekly_hours = [0, 0, 0, 0, 0, 0, 0]
    for session in weekly_sessions:
        weekly_hours[session.study_date.weekday()] += session.duration_hours

    context = {
        "total": assignments.count(),
        "completed": assignments.filter(status=Assignment.STATUS_COMPLETED).count(),
        "pending": assignments.filter(status=Assignment.STATUS_PENDING).count(),
        "overdue": assignments.filter(deadline__lt=now).exclude(status=Assignment.STATUS_COMPLETED).count(),
        "study_sessions": sessions.count(),
        "upcoming": assignments.exclude(status=Assignment.STATUS_COMPLETED).order_by("deadline")[:6],
        "notifications": Notification.objects.filter(user=request.user, is_read=False)[:5],
        "completion_labels": json.dumps([row["day"].strftime("%d %b") for row in trend_rows]),
        "completion_values": json.dumps([row["count"] for row in trend_rows]),
        "priority_labels": json.dumps(["High", "Medium", "Low"]),
        "priority_values": json.dumps([
            priority_counts.get(Assignment.PRIORITY_HIGH, 0),
            priority_counts.get(Assignment.PRIORITY_MEDIUM, 0),
            priority_counts.get(Assignment.PRIORITY_LOW, 0),
        ]),
        "study_labels": json.dumps(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
        "study_values": json.dumps(weekly_hours),
    }
    return render(request, "assignments/dashboard.html", context)


@login_required
def profile_view(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user, defaults={"registration_number": f"TEMP-{request.user.pk}"})
    user_form = UserUpdateForm(request.POST or None, instance=request.user)
    profile_form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")
    return render(request, "assignments/profile.html", {"user_form": user_form, "profile_form": profile_form})


@login_required
def change_password_view(request):
    form = StyledPasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password changed.")
        return redirect("profile")
    return render(request, "assignments/password_change.html", {"form": form})


@login_required
def assignment_list(request):
    qs = Assignment.objects.filter(user=request.user)
    form = AssignmentSearchForm(request.GET)
    if form.is_valid():
        q = form.cleaned_data.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(course_unit__icontains=q) | Q(lecturer__icontains=q))
        if form.cleaned_data.get("status"):
            qs = qs.filter(status=form.cleaned_data["status"])
        if form.cleaned_data.get("priority"):
            qs = qs.filter(priority=form.cleaned_data["priority"])
    page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
    return render(request, "assignments/assignment_list.html", {"form": form, "page_obj": page_obj})


@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    return render(request, "assignments/assignment_detail.html", {"assignment": assignment})


@login_required
def assignment_create(request):
    form = AssignmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)
        assignment.user = request.user
        assignment.save()
        messages.success(request, "Assignment saved.")
        return redirect("assignment_detail", pk=assignment.pk)
    return render(request, "assignments/assignment_form.html", {"form": form, "title": "Add Assignment"})


@login_required
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    form = AssignmentForm(request.POST or None, instance=assignment)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Assignment updated.")
        return redirect("assignment_detail", pk=assignment.pk)
    return render(request, "assignments/assignment_form.html", {"form": form, "title": "Edit Assignment", "assignment": assignment})


@login_required
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    if request.method == "POST":
        assignment.delete()
        messages.success(request, "Assignment deleted.")
        return redirect("assignment_list")
    return render(request, "assignments/assignment_confirm_delete.html", {"assignment": assignment})


@login_required
def mark_complete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, user=request.user)
    if request.method == "POST":
        assignment.status = Assignment.STATUS_COMPLETED if assignment.status != Assignment.STATUS_COMPLETED else Assignment.STATUS_PENDING
        assignment.save()
    return redirect(request.META.get("HTTP_REFERER", "assignment_list"))


@login_required
def study_session_list(request):
    sessions = StudySession.objects.filter(user=request.user)
    page_obj = Paginator(sessions, 10).get_page(request.GET.get("page"))
    return render(request, "assignments/study_session_list.html", {"page_obj": page_obj})


@login_required
def study_session_create(request):
    form = StudySessionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        session = form.save(commit=False)
        session.user = request.user
        session.full_clean()
        session.save()
        messages.success(request, "Study session saved.")
        return redirect("study_session_list")
    return render(request, "assignments/study_session_form.html", {"form": form, "title": "Add Study Session"})


@login_required
def study_session_edit(request, pk):
    session = get_object_or_404(StudySession, pk=pk, user=request.user)
    form = StudySessionForm(request.POST or None, instance=session)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Study session updated.")
        return redirect("study_session_list")
    return render(request, "assignments/study_session_form.html", {"form": form, "title": "Edit Study Session"})


@login_required
def study_session_delete(request, pk):
    session = get_object_or_404(StudySession, pk=pk, user=request.user)
    if request.method == "POST":
        session.delete()
        messages.success(request, "Study session deleted.")
        return redirect("study_session_list")
    return render(request, "assignments/study_session_confirm_delete.html", {"session": session})


@login_required
def calendar_view(request):
    sessions = StudySession.objects.filter(user=request.user)
    return render(request, "assignments/calendar.html", {"sessions": sessions})


@login_required
def notification_list(request):
    refresh_notifications(request.user)
    notifications = Notification.objects.filter(user=request.user)
    return render(request, "assignments/notifications.html", {"notifications": notifications})


@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("notification_list")


@login_required
def reports_view(request):
    assignments = Assignment.objects.filter(user=request.user)
    sessions = StudySession.objects.filter(user=request.user)
    total_hours = sum(session.duration_hours for session in sessions)
    context = {
        "total_assignments": assignments.count(),
        "completed_assignments": assignments.filter(status=Assignment.STATUS_COMPLETED).count(),
        "pending_assignments": assignments.exclude(status=Assignment.STATUS_COMPLETED).count(),
        "study_sessions": sessions.count(),
        "study_hours": total_hours,
    }
    return render(request, "assignments/reports.html", context)


@login_required
def report_pdf(request, report_type):
    builders = {
        "assignments": build_assignment_pdf,
        "progress": build_progress_pdf,
        "study": build_study_pdf,
    }
    builder = builders.get(report_type)
    if builder is None:
        return redirect("reports")
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{report_type}-report.pdf"'
    builder(response, request.user)
    return response
