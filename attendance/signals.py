# attendance/signals.py

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.timezone import now
from .models import DailyAttendance

@receiver(user_logged_in)
def create_attendance_record(sender, request, user, **kwargs):
    today = now().date()
    if not DailyAttendance.objects.filter(user=user, date=today).exists():
        DailyAttendance.objects.create(user=user, date=today)
