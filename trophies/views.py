"""
trophies/views.py
- 내 트로피 보기 + 획득시 애니메이션/사운드
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserTrophy, Trophy

@login_required
def my_trophies(request):
    user = request.user
    user_trophies = UserTrophy.objects.filter(user=user)
    return render(request, "my_trophies.html", {
        "user_trophies": user_trophies,
    })
