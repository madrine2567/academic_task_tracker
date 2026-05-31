from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import StudentProfile


@receiver(post_save, sender=User)
def ensure_student_profile(sender, instance, created, **kwargs):
    if created:
        StudentProfile.objects.get_or_create(user=instance, defaults={"registration_number": f"TEMP-{instance.pk}"})
