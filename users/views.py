from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Theme
from attendance.models import AttendanceStreak  # 출석 연속기록 모델

@login_required
def mypage(request):
    userprofile = UserProfile.objects.get(user=request.user)
    themes = Theme.objects.filter(is_active=True)

    # 출석 기록 조회 (연속 출석, 최장 기록)
    try:
        streak = AttendanceStreak.objects.get(user=request.user)
        consecutive_days = streak.streak_count
        # 만약 최장 기록을 별도로 관리한다면 그 필드를 쓰세요.
        longest_streak = getattr(streak, 'longest_streak', consecutive_days)  
    except AttendanceStreak.DoesNotExist:
        consecutive_days = 0
        longest_streak = 0

    context = {
        "userprofile": userprofile,
        "themes": themes,
        "consecutive_days": consecutive_days,
        "longest_streak": longest_streak,
    }

    if request.method == "POST" and "select_theme" in request.POST:
        theme_id = int(request.POST["select_theme"])
        theme = Theme.objects.get(id=theme_id)
        userprofile.selected_theme = theme
        userprofile.save()
        return redirect("mypage")

    return render(request, "mypage.html", context)
