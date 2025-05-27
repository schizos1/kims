# ============================================
# 📄 FILE: core/views_trophy.py
# 🏆 DESCRIPTION: 트로피 보관함 View
# ============================================

from core.models import Trophy, UserTrophy, UserAnswerLog, WrongAnswer
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def trophy_collection_view(request, user_id):
    user = request.user

    # 전체 트로피 목록
    all_trophies = Trophy.objects.all()

    # 사용자가 획득한 트로피
    user_trophies = UserTrophy.objects.filter(user=user).select_related('trophy')
    user_trophies_by_id = {ut.trophy.id: ut for ut in user_trophies}

    # 달성률 계산용
    user_log_count = UserAnswerLog.objects.filter(user=user).count()
    user_correct_count = UserAnswerLog.objects.filter(user=user, is_correct=True).count()
    user_resolved_count = WrongAnswer.objects.filter(user=user, is_resolved=True).count()

    progress_percent = {}
    for trophy in all_trophies:
        if trophy.id in user_trophies_by_id:
            progress_percent[trophy.id] = 100
        else:
            current = 0
            if trophy.trophy_type == 'activity':
                current = user_log_count
            elif trophy.trophy_type == 'correct':
                current = user_correct_count
            elif trophy.trophy_type == 'wrong':
                current = user_resolved_count
            percent = int((current / trophy.goal_value) * 100) if trophy.goal_value else 0
            percent = min(percent, 100)
            progress_percent[trophy.id] = percent

    return render(request, 'core/trophy_collection.html', {
        'all_trophies': all_trophies,
        'user_trophies_by_id': user_trophies_by_id,
        'user_log_count': user_log_count,
        'user_correct_count': user_correct_count,
        'user_resolved_count': user_resolved_count,
        'progress_percent': progress_percent,
    })
