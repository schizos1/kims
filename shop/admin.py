"""
경로: shop/admin.py
설명: 아이템, 구매기록, 용돈신청 등 관리자 등록
"""

from django.contrib import admin
from .models import Item, Purchase, AllowanceRequest

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'purchased_at', 'used')

@admin.register(AllowanceRequest)
class AllowanceRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'point', 'request_date', 'is_approved', 'approved_at')
