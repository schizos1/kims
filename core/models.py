"""
core/models.py
- 사이트 전역 리소스(통계/사운드/설정 등) 예시
"""

from django.db import models

class SiteSetting(models.Model):
    """사이트 전역 설정 (예: 안내문구, 배경, 메인 사운드 등)"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()

class Sound(models.Model):
    """효과음/알림음 리소스 관리"""
    name = models.CharField(max_length=100)
    file_url = models.URLField()

class ImageResource(models.Model):
    """각종 아이콘/마스코트 이미지 리소스 관리"""
    name = models.CharField(max_length=100)
    file_url = models.URLField()

class PromptTemplate(models.Model):
    """AI 프롬프트 템플릿(과목/유형별 저장용)"""
    subject = models.CharField(max_length=50)
    template = models.TextField()
    description = models.TextField(blank=True)
