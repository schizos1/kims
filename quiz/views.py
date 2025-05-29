"""
quiz/views.py
- 학생 대시보드: 메인 메뉴/기능 한눈에 보기
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def student_dashboard(request):
    """
    학생 대시보드: 주요 학습/기능 메뉴 홈
    """
    return render(request, "student_dashboard.html")
def concept_select(request):
    return render(request, 'concept_select.html')

def wrong_note(request):
    return render(request, 'wrong_note.html')

def wrong_note(request):
    user = request.user
    # 오답노트 예시: 최근 20개
    wrongs = user.wronganswer_set.select_related('question').order_by('-created_at')[:20]
    return render(request, 'wrong_note.html', {"wrongs": wrongs})   

def my_report(request):
    user = request.user
    # 누적, 과목별 정답률 등 예시
    total = user.useranswerlog_set.count()
    correct = user.useranswerlog_set.filter(is_correct=True).count()
    wrong = total - correct
    correct_rate = int((correct / total) * 100) if total else 0
    # 과목별 통계, etc...
    return render(request, "my_report.html", {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "correct_rate": correct_rate,
    })    