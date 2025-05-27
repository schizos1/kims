# ============================================
# 📄 FILE: core/views.py
# 🧠 DESCRIPTION: 문제 풀이, 오답노트, 로그인, 트로피 보관함 뷰
# ============================================

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Count
from core.models import Question, WrongAnswer, UserTrophy
from core.utils import submit_answer, grant_trophies

# ✅ 10문제 묶음 퀴즈 뷰
@login_required
def batch_quiz_view(request):
    user = request.user

    if request.method == 'POST':
        answers = request.POST
        results = []

        for key in answers:
            if key.startswith("question_"):
                qid = key.replace("question_", "")
                selected = int(answers[key])
                try:
                    question = Question.objects.get(id=qid)
                    is_correct = submit_answer(user, question, selected)
                    results.append({
                        "question": question,
                        "selected": selected,
                        "is_correct": is_correct,
                    })
                except Question.DoesNotExist:
                    continue

        return render(request, 'core/quiz_batch_result.html', {
            "results": results,
        })

    else:
        questions = Question.objects.filter(is_active=True).order_by('?')[:10]
        return render(request, 'core/quiz_batch.html', {
            "questions": questions,
        })


# ✅ 오답노트 뷰
@login_required
def wrongnote_view(request):
    user = request.user

    if request.method == 'POST':
        qid = request.POST.get("question_id")
        selected = int(request.POST.get("selected_answer"))

        try:
            question = Question.objects.get(id=qid)
            is_correct = submit_answer(user, question, selected)

            if is_correct:
                # 오답노트에서 제거
                wrong = WrongAnswer.objects.filter(user=user, question=question).first()
                if wrong:
                    wrong.is_resolved = True
                    wrong.save()

            return redirect('wrongnote')

        except Question.DoesNotExist:
            pass

    wrongs = WrongAnswer.objects.filter(user=user, is_resolved=False).select_related('question')
    return render(request, 'core/wrongnote.html', {
        'wrongs': wrongs,
    })


# ✅ 사용자 로그인 + 트로피 자동 지급 + 통계 리디렉션
class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)

        # ✅ 트로피 자동 지급
        new_trophies = grant_trophies(self.request.user)
        self.request.session['new_trophies'] = [t.name for t in new_trophies]

        return response

    def get_success_url(self):
        # ✅ 사용자 ID에 따라 stats 페이지로 리디렉션
        return reverse('user_stats', kwargs={'user_id': self.request.user.id})


# ✅ 트로피 보관함 뷰
@login_required
def trophy_collection_view(request, user_id):
    user = request.user
    if user.id != user_id:
        return redirect('quiz_batch')

    all_trophies = Trophy.objects.all()
    user_trophies = UserTrophy.objects.filter(user=user)
    user_trophies_by_id = {ut.trophy.id: ut for ut in user_trophies}

    # 현재 사용자 기록
    log_count = UserAnswerLog.objects.filter(user=user).count()
    correct_count = UserAnswerLog.objects.filter(user=user, is_correct=True).count()
    resolved_count = WrongAnswer.objects.filter(user=user, is_resolved=True).count()

    # 달성률 계산
    progress = {}
    for trophy in all_trophies:
        if trophy.trophy_type == 'activity':
            percent = min(int((log_count / trophy.goal_value) * 100), 100)
        elif trophy.trophy_type == 'correct':
            percent = min(int((correct_count / trophy.goal_value) * 100), 100)
        elif trophy.trophy_type == 'wrong':
            percent = min(int((resolved_count / trophy.goal_value) * 100), 100)
        else:
            percent = 0
        progress[trophy.id] = percent

    return render(request, 'core/trophy_collection.html', {
        'all_trophies': all_trophies,
        'user_trophies_by_id': user_trophies_by_id,
        'user_log_count': log_count,
        'user_correct_count': correct_count,
        'user_resolved_count': resolved_count,
        'progress_percent': progress,
    })
