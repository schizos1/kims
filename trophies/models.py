"""
trophies/models.py
- 트로피 정보와 획득 기록(학생별)
"""

from django.db import models
from django.contrib.auth.models import User

class Trophy(models.Model):
    """트로피 정보: 이름, 설명, 포인트, 조건 필드, 아이콘 등"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    points = models.IntegerField(default=100)
    icon = models.URLField(blank=True)
    # 조건 필드 예시 (확장 가능)
    required_login_days = models.IntegerField(default=0)
    required_total_quiz = models.IntegerField(default=0)
    required_right_rate = models.IntegerField(default=0)
    required_total_wrong = models.IntegerField(default=0)
    required_streak = models.IntegerField(default=0)
    required_point_used = models.IntegerField(default=0)
    required_subject = models.CharField(max_length=50, blank=True)
    required_subject_quiz = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class UserTrophy(models.Model):
    """학생별 트로피 획득 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trophy = models.ForeignKey(Trophy, on_delete=models.CASCADE)
    achieved_at = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField(default=False)  # 미획득 딤드 처리 등

    def __str__(self):
        return f"{self.user.username} - {self.trophy.name}"
