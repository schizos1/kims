"""
경로: minigame/admin.py
설명: 미니게임, 플레이로그 등 관리자 등록
"""

from django.contrib import admin
from .models import MiniGame, GamePlayLog

@admin.register(MiniGame)
class MiniGameAdmin(admin.ModelAdmin):
    list_display = ('name', 'open_condition', 'is_active')

@admin.register(GamePlayLog)
class GamePlayLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'minigame', 'score', 'played_at', 'reward_point')
