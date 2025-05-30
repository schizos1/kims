"""
attendance/views.py
- 출석 달력/출석 통계 대시보드
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import DailyAttendance
from datetime import date
import calendar

@login_required
def attendance_dashboard(request):
    user = request.user
    today = date.today()
    attendances = DailyAttendance.objects.filter(user=user, date__month=today.month)
    attendance_days = [a.date.day for a in attendances]
    _, last_day = calendar.monthrange(today.year, today.month)
    first_weekday = today.replace(day=1).weekday()

    # 달력 칸 생성
    calendar_cells = []
    for i in range(first_weekday):
        calendar_cells.append("")
    for day in range(1, last_day+1):
        calendar_cells.append(day)

    context = {
        "user": user,
        "today": today,
        "is_attended_today": today.day in attendance_days,
        "attendance_days": attendance_days,
        "calendar_cells": calendar_cells,
        "first_weekday": first_weekday,
        "last_day": last_day,
    }
    return render(request, "attendance_dashboard.html", context)
@login_required
def some_main_view(request):
    user = request.user
    today = date.today()

    # 오늘 출석 기록이 없으면 생성
    if not DailyAttendance.objects.filter(user=user, date=today).exists():
        DailyAttendance.objects.create(user=user, date=today)