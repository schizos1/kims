"""
경로: minigame/models.py
설명: 미니게임, 플레이 기록, 오픈조건, 트로피/포인트 연동 모델
"""

from django.db import models
from users.models import UserProfile

class MiniGame(models.Model):
    name = models.CharField(max_length=50, verbose_name="게임명")
    description = models.TextField(blank=True, verbose_name="설명")
    icon = models.URLField(blank=True, verbose_name="아이콘")
    open_condition = models.CharField(max_length=200, blank=True, verbose_name="오픈조건")
    required_trophy = models.CharField(max_length=100, blank=True, verbose_name="필요 트로피명")
    min_point = models.PositiveIntegerField(default=0, verbose_name="필요 포인트")
    is_active = models.BooleanField(default=True, verbose_name="활성화")

    def __str__(self):
        return self.name

class GamePlayLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="플레이어")
    minigame = models.ForeignKey(MiniGame, on_delete=models.CASCADE, verbose_name="게임")
    score = models.PositiveIntegerField(default=0, verbose_name="점수")
    played_at = models.DateTimeField(auto_now_add=True, verbose_name="플레이 시간")
    reward_point = models.PositiveIntegerField(default=0, verbose_name="획득 포인트")

    def __str__(self):
        return f"{self.user.nickname} {self.minigame.name} {self.score}"
