"""
경로: core/admin.py
설명: 코어 리소스(이미지, 사운드, 프롬프트, 사이트설정) 관리자 등록
"""

from django.contrib import admin
from .models import ImageResource, Sound, SiteSetting, PromptTemplate

@admin.register(ImageResource)
class ImageResourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file_url')
    search_fields = ('name',)

@admin.register(Sound)
class SoundAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file_url')
    search_fields = ('name',)

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'key', 'value')
    search_fields = ('key',)

@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'description')
    search_fields = ('subject', 'description')
