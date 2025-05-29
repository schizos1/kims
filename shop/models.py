"""
경로: shop/models.py
설명: 상점, 아이템, 구매/사용 기록, 용돈신청 등 보상·소비 모델 정의
"""

from django.db import models
from users.models import UserProfile

class Item(models.Model):
    name = models.CharField(max_length=50, verbose_name="아이템명")
    description = models.TextField(blank=True, verbose_name="설명")
    icon = models.URLField(blank=True, verbose_name="아이콘")
    price = models.PositiveIntegerField(verbose_name="포인트 가격")
    is_active = models.BooleanField(default=True, verbose_name="판매중")

    def __str__(self):
        return self.name

class Purchase(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="구매자")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="아이템")
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="구매일시")
    used = models.BooleanField(default=False, verbose_name="사용여부")

class AllowanceRequest(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="신청자")
    point = models.PositiveIntegerField(verbose_name="신청 포인트")
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="신청일")
    is_approved = models.BooleanField(default=False, verbose_name="승인여부")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="승인일")

    def __str__(self):
        return f"{self.user.nickname} {self.point}P"
