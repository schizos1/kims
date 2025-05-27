# ============================================
# 📄 FILE: core/views_stats.py
# 🧮 사용자 통계 및 학습 페이지 뷰
# ============================================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from core.models import User, UserAnswerLog, WrongAnswer, Trophy, UserTrophy
from django.http import HttpResponse

@login_required
def user_stats_view(request, user_id):
    """
    사용자의 통계 정보를 보여주는 페이지
    """
    user = get_object_or_404(User, id=user_id)

    total_answers = UserAnswerLog.objects.filter(user=user).count()
    correct_answers = UserAnswerLog.objects.filter(user=user, is_correct=True).count()
    wrong_unresolved = WrongAnswer.objects.filter(user=user, is_resolved=False).count()
    correct_rate = int((correct_answers / total_answers) * 100) if total_answers > 0 else 0
    total_point = getattr(user, "total_point", 0)

    return render(request, 'core/user_stats.html', {
        "user": user,
        "total_answers": total_answers,
        "correct_answers": correct_answers,
        "wrong_unresolved": wrong_unresolved,
        "correct_rate": correct_rate,
        "total_point": total_point
    })

@login_required
def learn_start_view(request):
    """
    학습 시작 페이지
    """
    # TODO: 여기에 '학습 시작' 페이지에 필요한 실제 로직을 구현합니다.
    # 예를 들어, 과목 선택 페이지를 렌더링 할 수 있습니다.
    # return render(request, 'core/learn_start.html')
    return HttpResponse("학습 시작 페이지입니다.")

@login_required
def learn_detail_view(request, subject, lesson_id):
    """
    개별 학습 상세 페이지
    """
    # URL을 통해 전달받은 subject와 lesson_id를 사용할 수 있습니다.
    # TODO: 이 값들을 이용해 데이터베이스에서 특정 학습 내용을 조회하는 로직을 구현합니다.
    
    # 예시: 전달받은 값을 그대로 출력하는 응답
    return HttpResponse(f"과목: {subject}, 레슨 ID: {lesson_id}의 상세 학습 페이지입니다.")

@login_required
def wrong_list_view(request):
    """
    사용자의 오답 노트 목록을 보여주는 페이지
    """
    # 현재 로그인한 사용자의 해결되지 않은 오답 목록을 가져옵니다.
    wrong_answers = WrongAnswer.objects.filter(user=request.user, is_resolved=False)
    
    context = {
        'wrong_answers': wrong_answers,
    }
    
    # 이 context 데이터를 'core/wrong_list.html' 템플릿으로 전달하여 페이지를 렌더링합니다.
    return render(request, 'core/wrong_list.html', context)

@login_required
def wrong_detail_view(request, question_id):
    """
    사용자의 특정 오답 문제 상세 페이지
    """
    # 현재 로그인한 사용자의 오답 중에서, URL로 받은 question_id와 일치하는
    # 오답 문제를 찾습니다. 없거나 다른 사용자의 것이면 404 오류를 발생시킵니다.
    wrong_answer = get_object_or_404(WrongAnswer, id=question_id, user=request.user)
    
    context = {
        'wrong_answer': wrong_answer,
    }
    
    # 이 context 데이터를 'core/wrong_detail.html' 템플릿으로 전달하여 페이지를 렌더링합니다.
    return render(request, 'core/wrong_detail.html', context)