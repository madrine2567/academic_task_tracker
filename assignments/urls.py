from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/password/", views.change_password_view, name="change_password"),
    path("assignments/", views.assignment_list, name="assignment_list"),
    path("assignments/add/", views.assignment_create, name="assignment_create"),
    path("assignments/<int:pk>/", views.assignment_detail, name="assignment_detail"),
    path("assignments/<int:pk>/edit/", views.assignment_edit, name="assignment_edit"),
    path("assignments/<int:pk>/delete/", views.assignment_delete, name="assignment_delete"),
    path("assignments/<int:pk>/complete/", views.mark_complete, name="mark_complete"),
    path("study/", views.study_session_list, name="study_session_list"),
    path("study/add/", views.study_session_create, name="study_session_create"),
    path("study/<int:pk>/edit/", views.study_session_edit, name="study_session_edit"),
    path("study/<int:pk>/delete/", views.study_session_delete, name="study_session_delete"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/<int:pk>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("reports/", views.reports_view, name="reports"),
    path("reports/<str:report_type>.pdf", views.report_pdf, name="report_pdf"),
]
