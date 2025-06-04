"""
study_site/urls.py
- 프로젝트 전체 URL 매핑
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings  # 파일 상단에 추가 (이미 있다면 생략)
from django.conf.urls.static import static # 파일 상단에 추가 (이미 있다면 생략)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('quiz/', include('quiz.urls')),
    path('trophies/', include('trophies.urls')),
    path('attendance/', include('attendance.urls')),
    path('shop/', include('shop.urls')),
    path('student_dashboard/', include('users.urls')), # '/mypage/' 경로로 users 앱의 URL들 연결
    path('minigame/', include('minigame.urls', namespace='minigame')),
    path('', include('core.urls')),  # 메인/홈 화면 (프로젝트 루트)
    path('accounts/', include('django.contrib.auth.urls')), # Django 기본 인증 URL
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'), # 로그아웃
    path('importer/', include('pdf_importer.urls'))
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)