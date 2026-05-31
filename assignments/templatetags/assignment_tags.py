"""
assignments/templatetags/assignment_tags.py
Custom template filters used in the HTML templates.

Usage in templates:
  {% load assignment_tags %}
  {{ value|abs_value }}
  {{ assignment|overdue_days }}
"""

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def abs_value(value):
    """Return absolute value of a number."""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    return value - arg


@register.filter
def percentage(part, total):
    """Return part/total as a rounded percentage string."""
    try:
        return round((part / total) * 100)
    except (ZeroDivisionError, TypeError):
        return 0
