"""
경로: users/admin.py
설명: 학생 프로필 관리자 등록
"""

from django.contrib import admin
from .models import UserProfile, Theme

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'nickname', 'mascot_name', 'selected_theme')
    search_fields = ('nickname', 'user__username')

@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_name', 'is_active')
    search_fields = ('name', 'display_name')
