# trophies/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserTrophy, Trophy
from users.models import UserProfile
from quiz.models import UserAnswerLog
from attendance.models import AttendanceStreak # UserProfile의 login_count와 별개로 연속 출석일 경우 필요
import logging

logger = logging.getLogger(__name__)

# --- 헬퍼 함수 정의 ---
def get_user_progress_for_condition(user, user_profile, trophy):
    """
    주어진 트로피의 조건 유형에 따라 사용자의 현재 진행 상황 값을 반환합니다.
    """
    condition_type = trophy.condition_type
    required_subject_name = trophy.required_subject
    # trophy.condition_value는 뷰 함수 내에서 target_value로 직접 사용됩니다.

    current_val = 0
    if user_profile is None and condition_type in ['login_days', 'point_used']: # UserProfile이 필요한 조건들
        logger.warning(f"Calculating progress for user {user.username}, but UserProfile is None. Condition type: {condition_type}")
        return 0 # UserProfile이 없으면 이 조건들의 진행도는 0

    if condition_type == 'login_days':
        current_val = user_profile.login_count
    elif condition_type == 'total_quiz':
        current_val = UserAnswerLog.objects.filter(user=user).count()
    elif condition_type == 'subject_quiz':
        if required_subject_name:
            # utils.py의 check_trophy_condition와 일관성을 위해 is_correct=True 사용
            current_val = UserAnswerLog.objects.filter(
                user=user, question__subject__name=required_subject_name, is_correct=True
            ).count()
    elif condition_type == 'right_rate': # 현재 달성률 %를 반환
        logs_for_rate = UserAnswerLog.objects.filter(user=user)
        if required_subject_name: # 특정 과목 정답률인 경우
            logs_for_rate = logs_for_rate.filter(question__subject__name=required_subject_name)
        
        total_answered = logs_for_rate.count()
        if total_answered == 0:
            current_val = 0
        else:
            correct_answered = logs_for_rate.filter(is_correct=True).count()
            current_val = round((correct_answered / total_answered) * 100, 1)
    elif condition_type == 'total_wrong':
        current_val = UserAnswerLog.objects.filter(user=user, is_correct=False).count()
    elif condition_type == 'streak':
        streak_record = AttendanceStreak.objects.filter(user=user).first()
        # student_dashboard_view에서 streak_count를 사용했으므로, 여기서도 일관성 있게 사용
        current_val = streak_record.streak_count if streak_record else 0
    elif condition_type == 'point_used':
        current_val = user_profile.points_used
    # --- 'acquired_trophy_count' 같은 새로운 조건 유형 로직 추가 가능 ---
    # elif condition_type == 'acquired_trophy_count': # 예시: 이 조건 유형을 사용하려면 Trophy 모델 condition_type choices에도 추가 필요
    #     current_val = UserTrophy.objects.filter(user=user).count()
    
    return current_val
# --- 헬퍼 함수 정의 끝 ---


@login_required
def my_trophies(request):
    user = request.user
    user_profile = None
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {user.username} in my_trophies view. Progress for some trophies might not be calculated accurately.")
        # UserProfile이 없는 경우, UserProfile이 필요한 조건들의 진행도는 0으로 처리될 것입니다 (헬퍼 함수 내 로직).

    all_trophies_qs = Trophy.objects.all().order_by('id') # 일관된 순서를 위해 정렬
    user_acquired_trophy_ids = set(UserTrophy.objects.filter(user=user).values_list('trophy_id', flat=True))

    display_trophies_list = []
    for trophy in all_trophies_qs:
        is_acquired = trophy.id in user_acquired_trophy_ids
        progress_info_for_template = None # 템플릿에 전달될 진행 정보

        if not is_acquired: # 미획득 트로피에 대해서만 진행도 계산
            current_progress_val = get_user_progress_for_condition(user, user_profile, trophy)
            target_value = trophy.condition_value
            
            remaining = 0
            individual_percentage = 0
            progress_message = ""

            if trophy.condition_type == 'right_rate': # 정답률 조건의 경우
                if current_progress_val >= target_value:
                    progress_message = f"목표 달성! (현재: {current_progress_val}%)"
                    individual_percentage = 100
                    remaining = 0 # 이미 달성했으므로 남은 것은 0
                else:
                    progress_message = f"현재 달성률: {current_progress_val}% (목표: {target_value}%)"
                    if target_value > 0 : # 목표치가 0이 아닐 때만 비율 계산
                         individual_percentage = int((current_progress_val / target_value) * 100)
                    else: # 목표치가 0이면 (이상한 경우지만) 달성한 것으로 간주
                        individual_percentage = 100
                    remaining = target_value - current_progress_val # 개선 필요 점수 (양수)
                
            else: # 카운트 기반 조건의 경우 (퀴즈 수, 로그인 일수 등)
                remaining = target_value - current_progress_val
                if remaining <= 0: # 이미 달성했거나 초과한 경우
                    remaining = 0 
                    individual_percentage = 100
                    progress_message = "조건 달성!"
                else: # 아직 달성 못한 경우
                    if target_value > 0:
                        individual_percentage = int((current_progress_val / target_value) * 100)
                    else: # target_value가 0인데 current_progress_val도 0이면 달성으로 볼 수도 있음 (트로피 정의에 따라 다름)
                        individual_percentage = 0 # 여기서는 0으로 처리

                    # 조건 유형별 메시지 생성
                    if trophy.condition_type == 'login_days':
                        progress_message = f"로그인 {remaining}일 더 필요"
                    elif trophy.condition_type == 'total_quiz':
                        progress_message = f"퀴즈 {remaining}개 더 풀기"
                    elif trophy.condition_type == 'subject_quiz':
                        progress_message = f"{trophy.required_subject} 퀴즈 {remaining}개 더 풀기"
                    elif trophy.condition_type == 'total_wrong':
                        progress_message = f"오답 {remaining}개 더 기록"
                    elif trophy.condition_type == 'streak':
                        progress_message = f"연속 출석 {remaining}일 더 필요"
                    elif trophy.condition_type == 'point_used':
                        progress_message = f"포인트 {remaining}점 더 사용"
                    # elif trophy.condition_type == 'acquired_trophy_count':
                    #     progress_message = f"트로피 {remaining}개 더 모으기"
                    else: # 알 수 없는 조건 타입 또는 기본 메시지
                        progress_message = f"{remaining} 더 필요"
            
            progress_info_for_template = {
                "current": current_progress_val,
                "target": target_value,
                "remaining": remaining,
                "percentage": individual_percentage,
                "message": progress_message
            }

        display_trophies_list.append({
            'trophy_object': trophy,
            'is_acquired': is_acquired,
            'progress_info': progress_info_for_template
        })

    # 전체 트로피 진행률
    overall_progress_percent = 0
    total_trophies_count = all_trophies_qs.count()
    if total_trophies_count > 0:
        overall_progress_percent = int(len(user_acquired_trophy_ids) / total_trophies_count * 100)
    
    context = {
        "user": user,
        "display_trophies": display_trophies_list,
        "overall_progress_percent": overall_progress_percent,
        "acquired_trophy_count": len(user_acquired_trophy_ids), # 템플릿에서 전체 진행률 분수 표시용
        "total_trophy_count": total_trophies_count,       # 템플릿에서 전체 진행률 분수 표시용
    }
    
    return render(request, "my_trophies.html", context)