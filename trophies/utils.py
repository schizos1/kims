# 경로: /home/schizos/study_site/trophies/utils.py
"""트로피 조건 체크와 부여를 위한 유틸리티 모듈"""

from django.db.models import F
from django.db import transaction
from .models import Trophy, UserTrophy
from quiz.models import UserAnswerLog
from attendance.models import AttendanceStreak
from users.models import UserProfile
import logging

logger = logging.getLogger(__name__)


def check_and_award_trophies(user):
    """사용자의 활동을 체크하고 트로피를 부여

    Args:
        user: 조건을 체크할 사용자 객체
    Returns:
        bool: 트로피 부여 여부
    """
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {user.username}")
        return False

    trophies = Trophy.objects.all()
    awarded = False

    with transaction.atomic():
        for trophy in trophies:
            if not UserTrophy.objects.filter(user=user, trophy=trophy).exists():
                if check_trophy_condition(user, user_profile, trophy):
                    UserTrophy.objects.create(user=user, trophy=trophy)
                    user_profile.points = F('points') + trophy.points
                    user_profile.save(update_fields=['points'])
                    awarded = True
                    logger.info(
                        f"Trophy awarded: {trophy.name} to {user.username}, points added: {trophy.points}"
                    )

        if awarded:
            user_profile.refresh_from_db()
            logger.info(f"Points updated for {user.username}: {user_profile.points}")

    return awarded


def check_trophy_condition(user, user_profile, trophy):
    """트로피 조건 충족 여부 확인

    Args:
        user: 사용자 객체
        user_profile: 사용자 프로필 객체
        trophy: 확인할 트로피 객체
    Returns:
        bool: 조건 충족 여부
    """
    try:
        if trophy.condition_type == Trophy.ConditionType.LOGIN_DAYS:
            return user_profile.login_count >= trophy.condition_value

        elif trophy.condition_type == Trophy.ConditionType.TOTAL_QUIZ:
            quiz_count = UserAnswerLog.objects.filter(user=user).count()
            return quiz_count >= trophy.condition_value

        elif trophy.condition_type == Trophy.ConditionType.SUBJECT_QUIZ:
            if trophy.required_subject:
                subject_count = UserAnswerLog.objects.filter(
                    user=user,
                    question__subject__name=trophy.required_subject,
                    is_correct=True
                ).count()
                return subject_count >= trophy.condition_value
            return False

        elif trophy.condition_type == Trophy.ConditionType.RIGHT_RATE:
            total = UserAnswerLog.objects.filter(user=user).count()
            if total == 0:
                return False
            correct = UserAnswerLog.objects.filter(user=user, is_correct=True).count()
            rate = (correct / total) * 100
            return rate >= trophy.condition_value

        elif trophy.condition_type == Trophy.ConditionType.TOTAL_WRONG:
            wrong_count = UserAnswerLog.objects.filter(user=user, is_correct=False).count()
            return wrong_count >= trophy.condition_value

        elif trophy.condition_type == Trophy.ConditionType.STREAK:
            streak = AttendanceStreak.objects.filter(user=user).first()
            if streak:
                return streak.streak_count >= trophy.condition_value
            return False

        elif trophy.condition_type == Trophy.ConditionType.POINT_USED:
            return user_profile.points_used >= trophy.condition_value

        elif trophy.condition_type == Trophy.ConditionType.GAME_WIN:
            return getattr(user_profile, 'minigame_win_count', 0) >= trophy.condition_value

        elif trophy.condition_type == Trophy.ConditionType.GAME_LOSS:
            return getattr(user_profile, 'minigame_loss_count', 0) >= trophy.condition_value

        elif trophy.condition_type == Trophy.ConditionType.POINT_GAINED:
            return getattr(user_profile, 'points', 0) >= trophy.condition_value

        elif trophy.condition_type == Trophy.ConditionType.TROPHY_COUNT:
            owned = UserTrophy.objects.filter(user=user).count()
            return owned >= trophy.condition_value

        return False

    except Exception as e:
        logger.error(f"트로피 조건 체크 에러: {trophy.name} - {e}")
        return False
