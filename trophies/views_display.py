from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Trophy, UserTrophy
from users.models import UserProfile
from quiz.models import UserAnswerLog
from attendance.models import AttendanceStreak
import logging

logger = logging.getLogger(__name__)


def get_user_progress_for_condition(user, user_profile, trophy):
    """조건별 현재 진행도를 계산한다."""
    condition_type = trophy.condition_type
    required_subject_name = trophy.required_subject
    current_val = 0

    if user_profile is None and condition_type in [
        Trophy.ConditionType.LOGIN_DAYS,
        Trophy.ConditionType.POINT_USED,
    ]:
        logger.warning(
            "Calculating progress for user %s but UserProfile is None."
            " Condition type: %s",
            user.username,
            condition_type,
        )
        return 0

    if condition_type == Trophy.ConditionType.LOGIN_DAYS:
        current_val = user_profile.login_count
    elif condition_type == Trophy.ConditionType.TOTAL_QUIZ:
        current_val = UserAnswerLog.objects.filter(user=user).count()
    elif condition_type == Trophy.ConditionType.SUBJECT_QUIZ and required_subject_name:
        current_val = UserAnswerLog.objects.filter(
            user=user,
            question__subject__name=required_subject_name,
            is_correct=True,
        ).count()
    elif condition_type == Trophy.ConditionType.RIGHT_RATE:
        logs_for_rate = UserAnswerLog.objects.filter(user=user)
        if required_subject_name:
            logs_for_rate = logs_for_rate.filter(
                question__subject__name=required_subject_name
            )
        total_answered = logs_for_rate.count()
        if total_answered:
            correct_answered = logs_for_rate.filter(is_correct=True).count()
            current_val = round((correct_answered / total_answered) * 100, 1)
    elif condition_type == Trophy.ConditionType.TOTAL_WRONG:
        current_val = UserAnswerLog.objects.filter(user=user, is_correct=False).count()
    elif condition_type == Trophy.ConditionType.STREAK:
        streak_record = AttendanceStreak.objects.filter(user=user).first()
        current_val = streak_record.streak_count if streak_record else 0
    elif condition_type == Trophy.ConditionType.POINT_USED:
        current_val = user_profile.points_used

    return current_val


@login_required
def my_trophies(request):
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()

    all_trophies_qs = Trophy.objects.all().order_by('id')
    user_acquired_trophy_ids = set(
        UserTrophy.objects.filter(user=user).values_list('trophy_id', flat=True)
    )

    display_trophies_list = []
    for trophy in all_trophies_qs:
        is_acquired = trophy.id in user_acquired_trophy_ids
        progress_info_for_template = None

        if not is_acquired:
            current_progress_val = get_user_progress_for_condition(
                user, user_profile, trophy
            )
            target_value = trophy.condition_value
            remaining = 0
            percentage = 0
            message = ""

            if trophy.condition_type == Trophy.ConditionType.RIGHT_RATE:
                if current_progress_val >= target_value:
                    message = f"목표 달성! (현재: {current_progress_val}%)"
                    percentage = 100
                else:
                    message = (
                        f"현재 달성률: {current_progress_val}% (목표: {target_value}%)"
                    )
                    percentage = int(
                        (current_progress_val / target_value) * 100
                    ) if target_value else 0
                    remaining = target_value - current_progress_val
            else:
                remaining = target_value - current_progress_val
                if remaining <= 0:
                    percentage = 100
                    message = "조건 달성!"
                else:
                    percentage = int(
                        (current_progress_val / target_value) * 100
                    ) if target_value else 0
                    if trophy.condition_type == Trophy.ConditionType.LOGIN_DAYS:
                        message = f"로그인 {remaining}일 더 필요"
                    elif trophy.condition_type == Trophy.ConditionType.TOTAL_QUIZ:
                        message = f"퀴즈 {remaining}개 더 풀기"
                    elif trophy.condition_type == Trophy.ConditionType.SUBJECT_QUIZ:
                        message = f"{trophy.required_subject} 퀴즈 {remaining}개 더 풀기"
                    elif trophy.condition_type == Trophy.ConditionType.TOTAL_WRONG:
                        message = f"오답 {remaining}개 더 기록"
                    elif trophy.condition_type == Trophy.ConditionType.STREAK:
                        message = f"연속 출석 {remaining}일 더 필요"
                    elif trophy.condition_type == Trophy.ConditionType.POINT_USED:
                        message = f"포인트 {remaining}점 더 사용"
                    else:
                        message = f"{remaining} 더 필요"

            progress_info_for_template = {
                "current": current_progress_val,
                "target": target_value,
                "remaining": remaining,
                "percentage": percentage,
                "message": message,
            }

        display_trophies_list.append(
            {
                "trophy_object": trophy,
                "is_acquired": is_acquired,
                "progress_info": progress_info_for_template,
            }
        )

    total_trophies_count = all_trophies_qs.count()
    overall_progress_percent = (
        int(len(user_acquired_trophy_ids) / total_trophies_count * 100)
        if total_trophies_count
        else 0
    )

    context = {
        "user": user,
        "display_trophies": display_trophies_list,
        "overall_progress_percent": overall_progress_percent,
        "acquired_trophy_count": len(user_acquired_trophy_ids),
        "total_trophy_count": total_trophies_count,
    }
    return render(request, "trophies/my_trophies.html", context)

