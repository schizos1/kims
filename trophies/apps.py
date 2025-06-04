"""트로피 앱 설정 모듈"""
from django.apps import AppConfig

class TrophiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trophies'
    verbose_name = "트로피 관리"

    def ready(self):
        # 시그널 모듈들을 로드하여 로그인 및 퀴즈 이벤트에 대응한다.
        from . import signals, signals_login  # noqa: F401
