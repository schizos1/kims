"""트로피 앱 설정 모듈"""
from django.apps import AppConfig

class TrophiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trophies'
    verbose_name = "트로피 관리"

    def ready(self):
        import trophies.signals  # 시그널 로드