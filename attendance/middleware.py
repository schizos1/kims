from datetime import date
from django.utils.deprecation import MiddlewareMixin
from .models import DailyAttendance
from .utils import update_attendance_streak  # update_attendance_streak 함수 반드시 존재해야 함

class AttendanceMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            today = date.today()
            user = request.user
            if not DailyAttendance.objects.filter(user=user, date=today).exists():
                DailyAttendance.objects.create(user=user, date=today)
                update_attendance_streak(user)  # 연속 출석 로직 실행
