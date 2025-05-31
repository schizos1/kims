# 경로: /home/schizos/study_site/users/apps.py
"""사용자 앱의 설정 모듈로, 앱 초기화를 정의합니다."""
from django.apps import AppConfig  # <--- 들여쓰기 없음

class UsersConfig(AppConfig):  # <--- 들여쓰기 없음
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        # ready 메소드 내의 코드는 class 정의에 맞춰 한 단계 들여쓰기 됩니다.
        from . import signals  # 시그널 모듈 로드