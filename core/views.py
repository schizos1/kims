# 경로: /home/schizos/study_site/core/views.py
"""코어 앱의 뷰 모듈로, 로그인 및 대시보드 기능을 처리합니다."""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from users.models import UserProfile
from attendance.models import DailyAttendance, AttendanceStreak
from datetime import date, datetime
from calendar import monthrange

def quick_login(request):
    """빠른 로그인 화면을 렌더링합니다."""
    return render(request, "quick_login.html")

def quick_login_action(request, username):
    """사용자 이름으로 빠른 로그인을 처리합니다.

    Args:
        request: HTTP 요청 객체.
        username: 로그인할 사용자 이름.

    Returns:
        관리자 또는 학생 대시보드로 리디렉션, 실패 시 홈으로.
    """
    pw_map = {
        "kimrin": "0424",
        "kimik": "0928",
        "admin": "khan0829##@"
    }
    password = pw_map.get(username)
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        if username == "admin":
            return redirect("/admin_dashboard/")
        else:
            return redirect("/student_dashboard/")
    return redirect("/")

@login_required
def student_dashboard(request):
    """학생 대시보드 페이지를 렌더링합니다.

    Args:
        request: HTTP 요청 객체, 사용자 데이터 포함.

    Returns:
        사용자, 프로필, 출석 데이터를 포함한 렌더링된 템플릿.
    """
    if request.user.username == "admin":
        return redirect("/admin_dashboard/")
    
    user = request.user
    today = date.today()
    user_profile = getattr(request.user, 'userprofile', None)

    # 출석 데이터 조회
    attendances = DailyAttendance.objects.filter(user=user)
    streak = AttendanceStreak.objects.filter(user=user).first()
    consecutive_days = streak.streak_count if streak else 0
    longest_streak = streak.longest_streak if streak else 0

    # 달력 데이터 생성
    year, month = today.year, today.month
    _, last_day = monthrange(year, month)
    calendar_cells = [""] * (datetime(year, month, 1).weekday()) + [str(i) for i in range(1, last_day + 1)]
    attendance_days = [str(a.date.day) for a in attendances if a.date.month == month and a.date.year == year]

    context = {
        "user": user,
        "userprofile": user_profile,
        "is_attended_today": any(a.date == today for a in attendances),
        "consecutive_days": consecutive_days,
        "longest_streak": longest_streak,
        "calendar_cells": calendar_cells,
        "attendance_days": attendance_days,
        "user_trophy_count": 0,  # 추후 구현
        "user_point": 0,         # 추후 구현
        "user_quiz_count": 0,    # 추후 구현
    }
    return render(request, "student_dashboard.html", context)

@login_required
def admin_dashboard(request):
    """관리자 대시보드 페이지를 렌더링합니다."""
    if request.user.username != "admin":
        return redirect("/")
    return render(request, "admin_dashboard.html", {"user": request.user})