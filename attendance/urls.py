# attendance/urls.py

from django.urls import path
from . import views # attendance 앱의 views.py를 가져옵니다.

app_name = 'attendance' # 네임스페이스 정의

urlpatterns = [
    # 학생 대시보드의 "출석" 메뉴에서 {% url 'attendance:calendar' %}로 연결될 경로입니다.
    # views.attendance_dashboard 함수가 출석 메인 페이지 역할을 하므로, name='calendar'로 지정합니다.
    # 앱의 루트 URL (예: /attendance/)로 접속 시 이 뷰가 실행됩니다.
    path('', views.attendance_dashboard, name='calendar'),

    # FullCalendar 등에서 출석 이벤트 데이터를 가져갈 API 경로
    path('events/', views.attendance_events, name='events'), # 기존 name='attendance_events'도 좋음

    # "출석하기" 버튼 등에서 호출될 출석 기록 처리 경로
    # views.py에서 some_main_view를 record_daily_attendance로 이름 변경 제안드렸었습니다.
    # 해당 함수 이름을 사용합니다.
    path('record/', views.record_daily_attendance, name='record_attendance'),
]