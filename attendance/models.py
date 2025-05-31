from django.db import models
from django.contrib.auth.models import User # 또는 settings.AUTH_USER_MODEL
from django.conf import settings # settings.AUTH_USER_MODEL 사용 시

class DailyAttendance(models.Model):
    """하루 출석 기록"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Django의 User 모델을 직접 참조하기보다 권장되는 방식
        on_delete=models.CASCADE,
        verbose_name="사용자"
    )
    date = models.DateField(verbose_name="출석일")
    checked_at = models.DateTimeField(auto_now_add=True, verbose_name="기록 시간")

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    class Meta:
        db_table = 'attendance_dailyattendance' # 테이블 이름 지정 (선택 사항이지만 권장)
        verbose_name = "일일 출석 기록"
        verbose_name_plural = "일일 출석 기록 목록"
        unique_together = ('user', 'date') # 하루에 한 번만 출석 기록

class AttendanceStreak(models.Model):
    """연속 출석 기록(출석 트로피, 통계용)"""
    # user 필드를 OneToOneField로 변경하는 것을 고려해볼 수 있습니다.
    # 각 사용자마다 하나의 연속 출석 기록만 가진다면 OneToOneField가 더 적합합니다.
    user = models.OneToOneField( # 또는 기존처럼 ForeignKey 사용
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="사용자"
    )
    streak_count = models.IntegerField(default=0, verbose_name="현재 연속 출석일")
    last_date = models.DateField(verbose_name="마지막 출석일")
    longest_streak = models.IntegerField(default=0, verbose_name="최장 연속 출석일")

    def __str__(self):
        return f"{self.user.username} - 현재 {self.streak_count}일 (최장 {self.longest_streak}일)"

    class Meta:
        db_table = 'attendance_attendancestreak' # 테이블 이름 지정
        verbose_name = "연속 출석 기록"
        verbose_name_plural = "연속 출석 기록 목록"