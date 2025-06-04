# 경로: /home/schizos/study_site/trophies/signals.py
"""트로피 부여를 위한 시그널 모듈

로그인 및 퀴즈 풀이 후 트로피 조건을 체크하고 부여합니다.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .utils import check_and_award_trophies
from quiz.models import UserAnswerLog

logger = logging.getLogger(__name__)

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
