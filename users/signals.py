# 경로: /home/schizos/study_site/users/signals.py
"""사용자 앱의 시그널 모듈로, 로그인 시 사용자 프로필을 업데이트합니다.

이 모듈은 user_logged_in 시그널을 처리하여 last_accessed 필드를 갱신합니다.
"""
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.timezone import now
from django.apps import apps

@receiver(user_logged_in)
def update_last_accessed(sender, user, request, **kwargs):
    """로그인 시 사용자 프로필의 last_accessed 필드를 업데이트합니다.

    Args:
        sender: 시그널을 보낸 클래스.
        user: 로그인한 사용자 객체.
        request: HTTP 요청 객체.
        kwargs: 추가 키워드 인수.
    """
    UserProfile = apps.get_model('users', 'UserProfile')
    # 함수 내의 코드는 함수 정의에 맞춰 한 단계 들여쓰기 됩니다.
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.last_accessed = now()
    profile.save()