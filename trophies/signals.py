# 경로: /home/schizos/study_site/trophies/signals.py
"""트로피 부여를 위한 시그널 모듈

로그인 및 퀴즈 풀이 후 트로피 조건을 체크하고 부여합니다.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from django.db.models import F
from .utils import check_and_award_trophies
from quiz.models import UserAnswerLog
from users.models import UserProfile

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def check_trophy_on_login(sender, user, request, **kwargs):
    """로그인 시 UserProfile.login_count 증가 및 트로피 체크

    Args:
        sender: 시그널 발신자
        user: 로그인한 사용자 객체
        request: HTTP 요청 객체
        kwargs: 추가 인자
    """
    try:
        with transaction.atomic():
            user_profile = UserProfile.objects.get(user=user)
            user_profile.login_count = F('login_count') + 1
            user_profile.save(update_fields=['login_count'])
            logger.debug(f"Login count incremented for {user.username}: {user_profile.login_count}")

            check_and_award_trophies(user)
            logger.info(f"Trophy check completed for login: {user.username}")
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {user.username}")
    except Exception as e:
        logger.error(f"Error in login trophy check for {user.username}: {e}")


@receiver(post_save, sender=UserAnswerLog)
def check_trophy_on_quiz(sender, instance, created, **kwargs):
    """퀴즈 풀이 후 트로피 체크

    Args:
        sender: 시그널 발신자 (UserAnswerLog)
        instance: 생성/수정된 UserAnswerLog 객체
        created: 새로 생성 여부
        kwargs: 추가 인자
    """
    if created:
        try:
            user = instance.user
            question_id = instance.question_id
            is_correct = instance.is_correct
            logger.debug(f"Quiz submission for {user.username}, question {question_id}, correct: {is_correct}")

            check_and_award_trophies(user)
            logger.info(f"Trophy check completed for quiz: {user.username}, question {question_id}")
        except Exception as e:
            logger.error(f"Error in quiz trophy check for {user.username}, question {question_id}: {e}")
