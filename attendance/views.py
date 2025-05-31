# attendance/views.py
"""출석 관련 기능을 처리하는 뷰 모듈입니다.

이 모듈은 다음 기능을 포함합니다:
- 사용자의 출석 대시보드 표시 (월별 달력, 출석 현황, 활동 기록 요약)
- FullCalendar용 출석 이벤트 데이터 제공 (JSON API)
- 일일 출석 기록 처리
"""

import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, redirect

from quiz.models import UserAnswerLog  # 활동 기록(문제 풀이 수)을 위해 임포트
from users.models import UserProfile
from .models import DailyAttendance, AttendanceStreak
# .utils에서 update_attendance_streak를 사용한다고 가정합니다. 실제 경로에 맞게 확인 필요.
# from .utils import update_attendance_streak 
# 만약 utils.py가 없다면, 해당 함수 로직이 이 파일 내에 있거나 다른 곳에 있어야 합니다.
# 여기서는 .utils.update_attendance_streak를 호출하는 부분이 record_daily_attendance에 있으므로,
# 해당 파일과 함수가 실제로 존재하는지 확인이 필요합니다. 편의상 주석 처리합니다.
# 실제 사용 시에는 주석을 해제하거나, 해당 함수를 직접 정의/임포트해야 합니다.

import logging
logger = logging.getLogger(__name__)


# 이 함수는 현재 attendance_dashboard에서 직접 사용되지는 않지만,
# 만약 날짜별 상세 활동을 별도 함수로 분리한다면 유용할 수 있어 수정해 둡니다.
def get_user_activity_for_day(user, year, month, day_num):
    """특정 날짜의 사용자 활동 요약을 반환합니다. (예: 푼 문제 수)

    Args:
        user: 사용자 객체.
        year: 해당 연도.
        month: 해당 월.
        day_num: 해당 일.

    Returns:
        dict: 해당 날짜의 활동 정보 (예: {'problems_solved': 5}).
              현재는 문제 풀이 수만 반환.
    """
    # UserAnswerLog의 날짜 필드를 'timestamp'로 수정
    problems_solved_count = UserAnswerLog.objects.filter(
        user=user,
        timestamp__year=year,    # 'created_at' -> 'timestamp'
        timestamp__month=month,  # 'created_at' -> 'timestamp'
        timestamp__day=day_num   # 'created_at' -> 'timestamp'
    ).count()
    return {"problems_solved": problems_solved_count}


@login_required
def attendance_dashboard(request):
    """로그인한 사용자의 출석 대시보드를 렌더링합니다.

    월별 달력 형태로 출석 현황과 일별 활동(푼 문제 수) 요약을 표시합니다.

    Args:
        request: HttpRequest 객체.

    Returns:
        HttpResponse: 출석 대시보드 HTML 페이지를 렌더링하여 반환합니다.
                      컨텍스트에는 달력 데이터, 오늘 출석 정보, 연속 출석 정보 등이 포함됩니다.
    """
    user = request.user
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    user_profile = None
    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(request, "사용자 프로필을 찾을 수 없습니다. 일부 정보가 정확하지 않을 수 있습니다.")
        pass

    is_attended_today = DailyAttendance.objects.filter(user=user, date=today).exists()

    streak_data = AttendanceStreak.objects.filter(user=user).first()
    consecutive_days = streak_data.streak_count if streak_data else 0
    longest_streak = streak_data.longest_streak if streak_data else 0

    month_calendar_weeks = calendar.monthcalendar(current_year, current_month)
    
    attended_days_set = {
        record.date.day for record in DailyAttendance.objects.filter(
            user=user, date__year=current_year, date__month=current_month
        )
    }

    # UserAnswerLog의 날짜 필드를 'timestamp'로 수정
    problem_logs_this_month = UserAnswerLog.objects.filter(
        user=user,
        timestamp__year=current_year,    # 'created_at__year' -> 'timestamp__year'
        timestamp__month=current_month   # 'created_at__month' -> 'timestamp__month'
    ).values('timestamp__day').annotate(count=Count('id')).order_by('timestamp__day') 
    # 위 .values() 및 .order_by() 에서도 'timestamp__day' 사용
    
    problems_solved_per_day_map = {log['timestamp__day']: log['count'] for log in problem_logs_this_month}

    calendar_display_data = []
    for week in month_calendar_weeks:
        current_week_data = []
        for day_num in week:
            cell_data = {"day_num": "", "is_attended": False, "activities": {}}
            if day_num != 0: 
                cell_data["day_num"] = day_num
                cell_data["is_attended"] = day_num in attended_days_set
                
                problems_solved_count = problems_solved_per_day_map.get(day_num, 0)
                if problems_solved_count > 0:
                    cell_data["activities"]["problems_solved"] = problems_solved_count
            current_week_data.append(cell_data)
        calendar_display_data.append(current_week_data)
            
    context = {
        "user": user,
        "userprofile": user_profile,
        "today": today,
        "is_attended_today": is_attended_today,
        "consecutive_days": consecutive_days,
        "longest_streak": longest_streak,
        "calendar_weeks_data": calendar_display_data,
        "current_month_display": today.strftime("%-m월"), # Linux/macOS. Windows에서는 '%#m월' 또는 '%m월'
        "current_year_display": current_year,
        "current_month_int": current_month, # ✨ 오늘 날짜 강조를 위해 현재 월(숫자) 추가
    }
    
    return render(request, "attendance/attendance_dashboard.html", context)


@login_required
def attendance_events(request):
    """FullCalendar용 출석 이벤트를 JSON 형식으로 제공합니다. (현재 간단 달력에서는 직접 사용 안 함)"""
    user = request.user
    attendances = DailyAttendance.objects.filter(user=user)
    events = []
    for a in attendances:
        events.append({
            "title": f"출석 ({a.checked_at.strftime('%H:%M')})",
            "start": a.date.isoformat(),
            "allDay": True,
            "extendedProps": {
                "checked_at_time": a.checked_at.strftime('%H:%M:%S')
            },
        })
    return JsonResponse(events, safe=False)


@login_required
def record_daily_attendance(request):
    """일일 출석을 기록하고 출석 대시보드로 리디렉션합니다."""
    user = request.user
    today = date.today()
    
    if not DailyAttendance.objects.filter(user=user, date=today).exists():
        DailyAttendance.objects.create(user=user, date=today)
        # update_attendance_streak 함수가 .utils 모듈에 실제로 정의되어 있고,
        # 해당 모듈이 import 되어 있어야 아래 라인이 정상 작동합니다.
        # from .utils import update_attendance_streak # 파일 상단에 추가 필요
        try:
            from .utils import update_attendance_streak # 여기서 임포트 시도
            update_attendance_streak(user) 
            messages.success(request, f"{today.strftime('%Y년 %m월 %d일')} 출석이 완료되었습니다!")
        except ImportError:
            logger.error("attendance.utils.update_attendance_streak 함수를 찾을 수 없습니다.")
            messages.warning(request, f"{today.strftime('%Y년 %m월 %d일')} 출석은 기록되었으나, 연속 출석 정보 업데이트에 실패했습니다.")
        except Exception as e:
            logger.error(f"update_attendance_streak 함수 실행 중 오류: {e}")
            messages.warning(request, f"{today.strftime('%Y년 %m월 %d일')} 출석은 기록되었으나, 연속 출석 정보 업데이트 중 오류가 발생했습니다.")
    else:
        messages.info(request, "오늘은 이미 출석했습니다.")
        
    return redirect('attendance:calendar')