"""Shared helper functions for core app."""
from users.models import UserProfile
from attendance.models import DailyAttendance, AttendanceStreak
from datetime import date, datetime
from calendar import monthrange


def get_user_profile(user):
    """Return related UserProfile or None."""
    return UserProfile.objects.filter(user=user).first()


def get_attendance_context(user):
    """Return attendance information for dashboards."""
    today = date.today()
    attendances = DailyAttendance.objects.filter(user=user)
    streak = AttendanceStreak.objects.filter(user=user).first()
    consecutive_days = streak.streak_count if streak else 0
    longest_streak = streak.longest_streak if streak else 0

    year, month = today.year, today.month
    _, last_day = monthrange(year, month)
    calendar_cells = [""] * (datetime(year, month, 1).weekday()) + [str(i) for i in range(1, last_day + 1)]
    attendance_days = [str(a.date.day) for a in attendances if a.date.month == month and a.date.year == year]

    return {
        "is_attended_today": any(a.date == today for a in attendances),
        "consecutive_days": consecutive_days,
        "longest_streak": longest_streak,
        "calendar_cells": calendar_cells,
        "attendance_days": attendance_days,
    }

