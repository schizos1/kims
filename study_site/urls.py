"""
study_site/urls.py
- 프로젝트 전체 URL 매핑
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('quiz/', include('quiz.urls')),
    path('trophies/', include('trophies.urls')),
    path('attendance/', include('attendance.urls')),
    path('shop/', include('shop.urls')),
    path('mypage/', include('users.urls')),
    path('minigame/', include('minigame.urls')),
    path('', include('core.urls')),  # 메인/홈 화면
]
