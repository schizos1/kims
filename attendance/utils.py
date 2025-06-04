from datetime import date, timedelta
import logging
from .models import AttendanceStreak

logger = logging.getLogger(__name__)

def update_attendance_streak(user):
    today = date.today()
    yesterday = today - timedelta(days=1)
    try:
        streak = AttendanceStreak.objects.filter(user=user).first()
        if not streak:
            AttendanceStreak.objects.create(user=user, streak_count=1, last_date=today, longest_streak=1)
            return
        if streak.last_date == yesterday:
            streak.streak_count += 1
            if streak.streak_count > streak.longest_streak:
                streak.longest_streak = streak.streak_count
            streak.last_date = today
            streak.save()
        elif streak.last_date < yesterday:
            streak.streak_count = 1
            streak.last_date = today
            streak.save()
    except Exception as e:
        logger.error("Error updating attendance streak: %s", e)
