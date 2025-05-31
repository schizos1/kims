# users/urls.py

from django.urls import path
from . import views # users 앱의 views.py

app_name = 'users' # 네임스페이스는 'users'로 유지합니다.

urlpatterns = [
    # 1. 학생 대시보드 (통계, 현황 등)
    # views.py에 정의된 함수 이름이 'student_dashboard_view'라고 가정하고 수정합니다.
    path('', views.student_dashboard_view, name='student_dashboard'), 

    # 2. 마이페이지 (개인 설정: 테마, 마스코트 등)
    # views.py에 mypage_settings_view 함수가 정의되어 있어야 합니다.
    path('settings/', views.mypage_settings_view, name='mypage_settings'),
]