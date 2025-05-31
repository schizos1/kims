"""
경로: users/admin.py
설명: 학생 프로필 관리자 등록
"""

from django.contrib import admin
from .models import UserProfile, Theme, Mascot # Mascot은 이미 불러오셨네요!

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'nickname', 'mascot_name', 'selected_theme', 'selected_mascot') # selected_mascot도 추가하면 좋겠죠?
    search_fields = ('nickname', 'user__username')
    list_filter = ('selected_theme',) # 예시 필터

@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_name', 'is_active')
    list_editable = ('is_active',) # 관리자 목록에서 바로 활성 여부 수정 가능
    search_fields = ('name', 'display_name')
    list_filter = ('is_active',)

# ✨✨✨ Mascot 모델을 관리자 페이지에 등록하는 코드 추가 ✨✨✨
@admin.register(Mascot)
class MascotAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'image') # 목록에 보여줄 필드
    list_editable = ('is_active', 'name') # 목록에서 바로 수정 가능한 필드 (name은 unique라 주의)
    search_fields = ('name',) # 검색 가능한 필드
    list_filter = ('is_active',)  # 필터 옵션
    # image 필드는 이미지 업로드 위젯이 자동으로 나타납니다.