from datetime import date, timedelta
from .models import AttendanceStreak

def update_attendance_streak(user):
    today = date.today()
    yesterday = today - timedelta(days=1)

    try:
        streak = AttendanceStreak.objects.get(user=user)
    except AttendanceStreak.DoesNotExist:
        # 최초 출석 시 streak 생성
        AttendanceStreak.objects.create(user=user, streak_count=1, last_date=today)
        return

    if streak.last_date == yesterday:
        # 연속 출석 증가
        streak.streak_count += 1
        streak.last_date = today
        streak.save()
    elif streak.last_date < yesterday:
        # 출석 끊김 -> 다시 1부터 시작
        streak.streak_count = 1
        streak.last_date = today
        streak.save()
    else:
        # 이미 오늘 출석 처리 된 경우
        pass
