"""
attendance/models.py
- 학생 출석일/연속출석/출석 통계 등
"""
from django.db import models
from django.contrib.auth.models import User

class DailyAttendance(models.Model):
    """하루 출석 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    checked_at = models.DateTimeField(auto_now_add=True)

class AttendanceStreak(models.Model):
    """연속 출석 기록(출석 트로피, 통계용)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    streak_count = models.IntegerField(default=0)
    last_date = models.DateField()
