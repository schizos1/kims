"""
users/models.py
- 학생 프로필 + 테마 선택
"""

from django.db import models
from django.contrib.auth.models import User

class Theme(models.Model):
    """선택 테마(캐릭터, 색상, 배경 등)"""
    name = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=30)  # 화면에 보일 한글명
    description = models.CharField(max_length=100, blank=True)
    bg_color = models.CharField(max_length=15, blank=True)
    main_color = models.CharField(max_length=15, blank=True)
    mascot_image = models.URLField(blank=True)
    preview_image = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.display_name

class UserProfile(models.Model):
    """학생 프로필 + 테마 선택"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=20)
    mascot_name = models.CharField(max_length=20, blank=True)
    selected_theme = models.ForeignKey(Theme, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.nickname

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=20)
    mascot_name = models.CharField(max_length=20, blank=True)
    selected_theme = models.ForeignKey(Theme, null=True, blank=True, on_delete=models.SET_NULL)
    
    last_accessed = models.DateTimeField(null=True, blank=True)  # 접속일자 필드 추가

    def __str__(self):
        return self.nickname