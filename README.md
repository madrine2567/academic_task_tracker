# Academic Success Management System (ASMS)

ASMS is a Django 6 web application for university students to manage assignments, study plans, reminders, analytics, and PDF reports. It uses SQLite locally and PostgreSQL on Render through `DATABASE_URL`.

## Phases Delivered

1. Project structure: `tracker_project` Django project with the `assignments` application, reusable base template, Bootstrap 5 UI, and Render deployment files.
2. Database models: normalized `StudentProfile`, `Assignment`, `StudySession`, and `Notification` models.
3. Authentication: registration, login, logout, profile update, profile picture upload, and password change.
4. Assignment management: add, edit, delete, view, search, filter, status and priority tracking.
5. Study planner: create, edit, delete, list, and calendar views for study sessions.
6. Dashboard analytics: cards and Chart.js charts for completion trends, priority distribution, and weekly study hours.
7. Reports: assignment, progress, and study PDF exports using ReportLab.
8. Testing: model and integration tests plus `seed_asms` sample data command.
9. Render deployment: `requirements.txt`, `Procfile`, `runtime.txt`, `render.yaml`, WhiteNoise, PostgreSQL config, and environment variables.

## ER Diagram Explanation

`User` is Django's authentication table. Each `User` has one `StudentProfile` through a one-to-one relationship. A `User` owns many `Assignment`, `StudySession`, and `Notification` records. `Notification` optionally links to one `Assignment` or one `StudySession`, allowing reminders to be traced back to the academic item that triggered them.

Relationships:

- `User 1 -- 1 StudentProfile`
- `User 1 -- * Assignment`
- `User 1 -- * StudySession`
- `User 1 -- * Notification`
- `Assignment 1 -- * Notification`
- `StudySession 1 -- * Notification`

Constraints and indexes:

- `StudentProfile.registration_number` is unique.
- `Assignment` has a unique constraint on `user`, `title`, and `course_unit`.
- Assignment indexes support dashboard and filtering by user, deadline, status, and priority.
- Study session indexes support calendar queries by user and date.
- Notification indexes support unread reminder queries.

## Local Setup

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_asms
python manage.py runserver
```

Demo login:

- Username: `student`
- Password: `Student@12345`

## Quality Checks

```bash
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
```

## Render Deployment

Push this project to GitHub and create a Render Blueprint from `render.yaml`, or create a Render web service manually.

Required production environment variables:

- `DEBUG=False`
- `SECRET_KEY=<generated secret>`
- `DATABASE_URL=<Render PostgreSQL connection string>`
- `ALLOWED_HOSTS=.onrender.com`
- `CSRF_TRUSTED_ORIGINS=https://your-render-service.onrender.com`

Render build command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

Render start command:

```bash
gunicorn tracker_project.wsgi:application
```
