"""
경로: trophies/admin.py
설명: 트로피, 유저트로피 모델 관리자 등록
"""

from django.contrib import admin
from .models import Trophy, UserTrophy

@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'points', 'description')
    search_fields = ('name', 'description')

@admin.register(UserTrophy)
class UserTrophyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trophy', 'achieved_at', 'is_hidden')
    search_fields = ('user__username', 'trophy__name')
