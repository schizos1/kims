"""
attendance/views.py
- 출석 달력/출석 통계 대시보드
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import DailyAttendance
from datetime import date
from django.utils import timezone
import calendar

@login_required
def attendance_dashboard(request):
    user = request.user
    today = date.today()
    # 해당 월의 출석 리스트 (간단 예시)
    attendances = DailyAttendance.objects.filter(user=user, date__month=today.month)
    attendance_days = [a.date.day for a in attendances]
    return render(request, "attendance_dashboard.html", {
        "today": today,
        "attendance_days": attendance_days,
    })
def attendance_dashboard(request):
    today = timezone.now().date()
    userprofile = request.user.userprofile
    attendances = DailyAttendance.objects.filter(user=userprofile, date__month=today.month)
    attendance_days = [a.date.day for a in attendances]
    # 연속 출석, 최장 기록 로직 예시 (없으면 0)
    try:
        streak = userprofile.attendancestreak.current_streak
        longest_streak = userprofile.attendancestreak.longest_streak
    except:
        streak = 0
        longest_streak = 0
    # 캘린더 row (이번달 일수 + 첫 요일 고려)
    _, last_day = calendar.monthrange(today.year, today.month)
    first_weekday = today.replace(day=1).weekday()
    context = {
        "user": request.user,
        "is_attended_today": today in [a.date for a in attendances],
        "attendance_days": attendance_days,
        "streak": streak,
        "longest_streak": longest_streak,
        "range": range(0, last_day + first_weekday),
        "first_weekday": first_weekday,
    }
    return render(request, "attendance_dashboard.html", context)