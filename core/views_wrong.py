# ============================================
# 📄 FILE: core/views_wrong.py
# 📝 DESCRIPTION: 오답노트 - 오답 목록 및 풀이/정답 처리
# ============================================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from core.models import WrongAnswer, Question
from core.utils import submit_answer

@login_required
def wrong_list_view(request):
    wrongs = WrongAnswer.objects.filter(user=request.user, is_resolved=False)
    return render(request, 'core/wrong_list.html', {'wrongs': wrongs})


@login_required
def wrong_detail_view(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    wrong_entry = get_object_or_404(WrongAnswer, user=request.user, question=question, is_resolved=False)

    if request.method == 'POST':
        selected = int(request.POST.get("selected_answer"))
        is_correct = submit_answer(request.user, question, selected)

        if is_correct:
            wrong_entry.is_resolved = True
            wrong_entry.save()

        return render(request, 'core/wrong_check.html', {
            'question': question,
            'selected': selected,
            'is_correct': is_correct,
        })

    return render(request, 'core/wrong_detail.html', {'question': question})
