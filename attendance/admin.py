"""
경로: attendance/admin.py
설명: 출석, 연속 출석 모델 관리자 등록
"""

from django.contrib import admin
from .models import DailyAttendance, AttendanceStreak

@admin.register(DailyAttendance)
class DailyAttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'checked_at')
    search_fields = ('user__username', 'date')

@admin.register(AttendanceStreak)
class AttendanceStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'streak_count', 'last_date')
    search_fields = ('user__username',)
