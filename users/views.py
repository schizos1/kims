# users/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import calendar
import logging
from django.db import transaction # ✨ transaction 임포트 추가 (포인트 사용 시 원자성 보장)

# 현재 앱(.models) 및 다른 앱의 모델 임포트
from .models import UserProfile, Theme, Mascot, PointTransaction # ✨ PointTransaction 모델 임포트
from attendance.models import AttendanceStreak, DailyAttendance
from trophies.models import UserTrophy
from quiz.models import UserAnswerLog, Subject, Question

logger = logging.getLogger(__name__)

# student_dashboard_view 함수는 변경 없이 그대로 둡니다.
# ... (student_dashboard_view 함수 전체 내용 - 이전 답변과 동일) ...
@login_required
def student_dashboard_view(request):
    """학생 대시보드를 표시합니다 (통계, 출석 현황 등)."""
    user = request.user
    user_profile = None
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(request, "사용자 프로필을 찾을 수 없습니다.")
        return redirect('core:home')

    user_point = user_profile.points
    user_trophy_count = UserTrophy.objects.filter(user=user).count()
    user_quiz_count = UserAnswerLog.objects.filter(user=user).count()

    consecutive_days = 0
    longest_streak = 0
    try:
        streak = AttendanceStreak.objects.get(user=user) 
        consecutive_days = streak.streak_count
        longest_streak = streak.longest_streak
    except AttendanceStreak.DoesNotExist:
        pass

    today = timezone.now().date() 
    year = today.year
    month = today.month
    month_calendar_weeks = calendar.monthcalendar(year, month)
    calendar_cells = []
    for week in month_calendar_weeks:
        for day_num in week:
            calendar_cells.append(day_num if day_num != 0 else "")

    attendance_records_this_month = DailyAttendance.objects.filter( 
        user=user, date__year=year, date__month=month
    )
    attendance_days = {record.date.day for record in attendance_records_this_month}
    is_attended_today = DailyAttendance.objects.filter(user=user, date=today).exists()

    all_user_logs = UserAnswerLog.objects.filter(user=user)
    total_answered_count_for_accuracy = all_user_logs.count()
    correct_answered_count = all_user_logs.filter(is_correct=True).count()
    overall_accuracy = (correct_answered_count / total_answered_count_for_accuracy * 100) if total_answered_count_for_accuracy > 0 else 0

    all_subjects = Subject.objects.all()
    subject_stats_list = []
    for subject_obj in all_subjects:
        logs_in_subject = UserAnswerLog.objects.filter(user=user, question__subject=subject_obj)
        total_attempted_in_subject = logs_in_subject.count()
        correct_attempted_in_subject = logs_in_subject.filter(is_correct=True).count()
        subject_accuracy = (correct_attempted_in_subject / total_attempted_in_subject * 100) if total_attempted_in_subject > 0 else 0
        
        total_questions_in_subject = Question.objects.filter(subject=subject_obj).count()
        unique_questions_attempted_in_subject_count = UserAnswerLog.objects.filter(
            user=user, question__subject=subject_obj
        ).values('question_id').distinct().count()
        subject_progress_percentage = (unique_questions_attempted_in_subject_count / total_questions_in_subject * 100) if total_questions_in_subject > 0 else 0
        
        subject_stats_list.append({
            'id': subject_obj.id, 'name': subject_obj.name,
            'accuracy': round(subject_accuracy, 1),
            'total_attempted': total_attempted_in_subject,
            'correct_attempted': correct_attempted_in_subject,
            'progress': round(subject_progress_percentage, 1),
            'unique_attempted_count': unique_questions_attempted_in_subject_count,
            'total_questions': total_questions_in_subject,
        })

    context = {
        "user": user, "userprofile": user_profile,
        "user_point": user_point, "user_trophy_count": user_trophy_count,
        "user_quiz_count": user_quiz_count,
        "consecutive_days": consecutive_days, "longest_streak": longest_streak,
        "calendar_cells": calendar_cells, 
        "attendance_days": attendance_days, 
        "is_attended_today": is_attended_today,
        "current_month_name": today.strftime("%B"),
        "current_year": year,
        "overall_accuracy": round(overall_accuracy, 1),
        "subject_stats_list": subject_stats_list,
    }
    return render(request, "student_dashboard.html", context)


@login_required
def mypage_settings_view(request):
    """사용자 개인 설정(닉네임, 마스코트, 테마, 포인트 사용) 페이지를 표시하고 처리합니다."""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "사용자 프로필을 찾을 수 없습니다. 먼저 프로필을 완성해주세요.")
        return redirect('core:home')

    gallery_mascots = Mascot.objects.filter(is_active=True)
    themes = Theme.objects.filter(is_active=True) # 테마 목록도 계속 가져옵니다.

    if request.method == "POST":
        changes_made = False # 프로필/테마/마스코트 변경 여부
        points_action_message = None # 포인트 사용 관련 메시지

        # 폼 제출 버튼의 name 속성으로 어떤 작업인지 구분
        action = request.POST.get("action")

        if action == "update_profile_settings": # 닉네임, 마스코트, 테마 등 일반 설정 저장
            # 1. 닉네임 변경 처리
            new_nickname = request.POST.get("nickname", user_profile.nickname).strip()
            if new_nickname and new_nickname != user_profile.nickname:
                if len(new_nickname) > 20: 
                    messages.error(request, "닉네임은 20자 이하로 설정해주세요.")
                else:
                    user_profile.nickname = new_nickname
                    changes_made = True
            
            # 2. 마스코트 애칭 변경 처리
            new_mascot_name = request.POST.get("mascot_name", user_profile.mascot_name).strip()
            if new_mascot_name != user_profile.mascot_name:
                if len(new_mascot_name) > 20:
                    messages.error(request, "마스코트 애칭은 20자 이하로 설정해주세요.")
                else:
                    user_profile.mascot_name = new_mascot_name
                    changes_made = True
            
            # 3. 갤러리 마스코트 선택 처리
            selected_mascot_id = request.POST.get("gallery_mascot_select")
            current_selected_mascot_id_str = str(user_profile.selected_mascot.id) if user_profile.selected_mascot else ""
            if selected_mascot_id is not None and selected_mascot_id != current_selected_mascot_id_str:
                if selected_mascot_id == "none" or selected_mascot_id == "": 
                    if user_profile.selected_mascot is not None:
                        user_profile.selected_mascot = None
                        changes_made = True
                else:
                    try:
                        chosen_mascot = Mascot.objects.get(id=int(selected_mascot_id), is_active=True)
                        user_profile.selected_mascot = chosen_mascot
                        changes_made = True
                    except (Mascot.DoesNotExist, ValueError):
                        messages.error(request, "선택하신 마스코트를 찾을 수 없습니다.")
            
            # 4. 테마 변경 요청 처리
            theme_id_str = request.POST.get("select_theme")
            current_selected_theme_id_str = str(user_profile.selected_theme.id) if user_profile.selected_theme else ""
            if theme_id_str is not None and theme_id_str != current_selected_theme_id_str :
                if theme_id_str == "": 
                     if user_profile.selected_theme is not None:
                        user_profile.selected_theme = None
                        changes_made = True
                else:
                    try:
                        theme_id = int(theme_id_str)
                        selected_theme_obj = Theme.objects.get(id=theme_id, is_active=True)
                        user_profile.selected_theme = selected_theme_obj
                        changes_made = True
                    except ValueError: messages.error(request, "잘못된 테마 ID 형식입니다.")
                    except Theme.DoesNotExist: messages.error(request, "선택하신 테마를 찾을 수 없습니다.")
            
            if changes_made:
                user_profile.save()
                messages.success(request, "설정이 성공적으로 저장되었습니다!")
            else:
                messages.info(request, "변경된 설정 내용이 없습니다.")
            
            return redirect("users:mypage_settings")

        elif action == "request_allowance": # ✨ 포인트 사용 신청 (용돈) 처리 ✨
            try:
                points_to_use_str = request.POST.get("points_to_use", "0").strip()
                points_to_use = int(points_to_use_str)
                
                available_points_for_allowance = user_profile.points - user_profile.points_used

                if points_to_use <= 0:
                    messages.error(request, "사용할 포인트는 0보다 커야 합니다.")
                elif points_to_use > available_points_for_allowance:
                    messages.error(request, f"사용 가능 포인트를 초과했습니다. (현재: {available_points_for_allowance}P)")
                else:
                    # 포인트 사용 처리 (원자적 연산을 위해 transaction 사용)
                    with transaction.atomic():
                        # UserProfile의 points_used 업데이트
                        user_profile.points_used += points_to_use
                        user_profile.save(update_fields=['points_used'])

                        # PointTransaction 기록 생성
                        PointTransaction.objects.create(
                            user=request.user,
                            transaction_type='allowance_request', # PointTransaction 모델에 정의된 choices 값
                            points_changed= -points_to_use, # 사용이니까 음수
                            description=f"{points_to_use}P 용돈 신청"
                        )
                        messages.success(request, f"{points_to_use}P를 사용하여 용돈 신청이 완료되었습니다!")
                    return redirect("users:mypage_settings") # 성공 시 새로고침

            except ValueError:
                messages.error(request, "사용할 포인트를 숫자로 정확히 입력해주세요.")
            except Exception as e:
                logger.error(f"포인트 사용 신청 중 오류 발생: {e}", exc_info=True)
                messages.error(request, "포인트 사용 신청 중 오류가 발생했습니다.")
            # 오류 발생 시에도 현재 페이지에 머무르도록 redirect 제거 (메시지 표시)

    # GET 요청 또는 포인트 사용 신청 실패 시 보여줄 데이터
    available_points = 0
    if user_profile:
        available_points = user_profile.points - user_profile.points_used
        if available_points < 0:
            available_points = 0
            
    # 포인트 사용 내역 가져오기 (최신 10개 또는 전부)
    point_transactions = PointTransaction.objects.filter(user=request.user).order_by('-timestamp')[:10] # 예시: 최신 10개
    
    context = {
        "user": request.user,
        "userprofile": user_profile,
        "themes": themes,
        "gallery_mascots": gallery_mascots,
        "available_points": available_points,
        "point_transactions": point_transactions, # ✨ 포인트 사용 내역 전달 ✨
    }
    return render(request, "users/mypage_settings.html", context)