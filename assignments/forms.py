from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Assignment, StudentProfile, StudySession


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css = "form-check-input"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css}".strip()


class StudentRegistrationForm(BootstrapFormMixin, UserCreationForm):
    full_name = forms.CharField(max_length=120)
    registration_number = forms.CharField(max_length=40)
    email = forms.EmailField()
    programme = forms.CharField(max_length=120, initial="Bachelor of Science in Computer Science")
    year_of_study = forms.ChoiceField(choices=StudentProfile.YEAR_CHOICES)

    class Meta:
        model = User
        fields = ("username", "full_name", "registration_number", "email", "programme", "year_of_study", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        names = self.cleaned_data["full_name"].strip().split(" ", 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ""
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            StudentProfile.objects.update_or_create(
                user=user,
                defaults={
                    "registration_number": self.cleaned_data["registration_number"],
                    "programme": self.cleaned_data["programme"],
                    "year_of_study": self.cleaned_data["year_of_study"],
                },
            )
        return user


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    full_name = forms.CharField(max_length=120)

    class Meta:
        model = User
        fields = ("full_name", "email")

    def __init__(self, *args, **kwargs):
        user = kwargs.get("instance")
        initial = kwargs.setdefault("initial", {})
        if user:
            initial["full_name"] = user.get_full_name()
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def save(self, commit=True):
        user = super().save(commit=False)
        names = self.cleaned_data["full_name"].strip().split(" ", 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ""
        if commit:
            user.save()
        return user


class ProfileUpdateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ("registration_number", "programme", "year_of_study", "profile_picture")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class AssignmentForm(BootstrapFormMixin, forms.ModelForm):
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Assignment
        fields = ("title", "course_unit", "lecturer", "deadline", "description", "priority", "status")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class AssignmentSearchForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(required=False, label="", widget=forms.TextInput(attrs={"placeholder": "Search title, course unit, lecturer"}))
    status = forms.ChoiceField(required=False, choices=[("", "All statuses")] + Assignment.STATUS_CHOICES)
    priority = forms.ChoiceField(required=False, choices=[("", "All priorities")] + Assignment.PRIORITY_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class StudySessionForm(BootstrapFormMixin, forms.ModelForm):
    study_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))

    class Meta:
        model = StudySession
        fields = ("subject", "study_date", "start_time", "end_time", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class StyledPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
