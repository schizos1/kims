"""
users/views.py
- 마이페이지: 테마/프로필 관리
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Theme

@login_required
def mypage(request):
    userprofile = UserProfile.objects.get(user=request.user)
    themes = Theme.objects.filter(is_active=True)
    if request.method == "POST" and "select_theme" in request.POST:
        theme_id = int(request.POST["select_theme"])
        theme = Theme.objects.get(id=theme_id)
        userprofile.selected_theme = theme
        userprofile.save()
        return redirect("mypage")
    return render(request, "mypage.html", {"userprofile": userprofile, "themes": themes})
