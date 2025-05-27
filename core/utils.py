# ============================================
# 📄 FILE: core/utils.py
# 🧠 DESCRIPTION: 문제 제출 + 트로피 자동 지급 유틸
# ============================================

from core.models import UserAnswerLog, WrongAnswer, Trophy, UserTrophy
from django.utils.timezone import now


# ✅ 문제 정답 제출 처리
def submit_answer(user, question, selected_answer):
    is_correct = (selected_answer == question.correct_answer)

    # 풀이 로그 기록
    UserAnswerLog.objects.create(
        user=user,
        question=question,
        selected_answer=selected_answer,
        is_correct=is_correct
    )

    # 오답 저장 (중복 저장 방지)
    if not is_correct:
        exists = WrongAnswer.objects.filter(user=user, question=question, is_resolved=False).exists()
        if not exists:
            WrongAnswer.objects.create(user=user, question=question)

    return is_correct


# ✅ 트로피 자동 지급 로직
def grant_trophies(user):
    newly_awarded = []

    # 이미 획득한 트로피 제외
    earned_ids = UserTrophy.objects.filter(user=user).values_list('trophy_id', flat=True)
    trophies = Trophy.objects.exclude(id__in=earned_ids)

    for trophy in trophies:
        awarded = False

        if trophy.trophy_type == 'activity':
            count = UserAnswerLog.objects.filter(user=user).count()
            if count >= trophy.goal_value:
                awarded = True

        elif trophy.trophy_type == 'correct':
            count = UserAnswerLog.objects.filter(user=user, is_correct=True).count()
            if count >= trophy.goal_value:
                awarded = True

        elif trophy.trophy_type == 'wrong':
            resolved = WrongAnswer.objects.filter(user=user, is_resolved=True).count()
            if resolved >= trophy.goal_value:
                awarded = True

        if awarded:
            UserTrophy.objects.create(user=user, trophy=trophy)
            user.total_point += trophy.point
            user.save()
            newly_awarded.append(trophy)

    return newly_awarded
