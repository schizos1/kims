import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Subject, Lesson, Question, UserAnswerLog, WrongAnswer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def concept_select(request):
    """
    문제 유형(개념/기출) 선택 페이지
    """
    return render(request, "quiz/concept_select.html")

@login_required
def concept_subject_list(request):
    """
    개념문제 - 과목선택 페이지
    - 필수/선택 과목 분리
    """
    required_names = ["국어", "수학", "사회", "과학"]
    subjects = Subject.objects.all()
    required_subjects = [s for s in subjects if s.name in required_names]
    elective_subjects = [s for s in subjects if s.name not in required_names]
    context = {
        "required_subjects": required_subjects,
        "elective_subjects": elective_subjects,
    }
    return render(request, "quiz/concept_subject_list.html", context)

@login_required
def concept_lesson_list(request, subject_id):
    """
    개념문제 - 단원선택 페이지
    """
    subject = get_object_or_404(Subject, pk=subject_id)
    lessons = Lesson.objects.filter(subject=subject)
    return render(request, "quiz/concept_lesson_list.html", {
        "subject": subject,
        "lessons": lessons,
    })

@login_required
def concept_question_list(request, subject_id, lesson_id):
    """
    개념문제 - 문제풀기 리스트 페이지
    - 랜덤 10문제 출제, 출제된 문제는 세션에 저장하여 제외
    - POST 요청 시 답안 제출 처리 후 결과 저장
    """
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id)

    if request.method == "POST":
        question_id = int(request.POST.get('question_id'))
        selected_answer = int(request.POST.get('answer'))
        question = get_object_or_404(Question, pk=question_id)

        is_correct = (selected_answer == question.answer)
        user = request.user

        UserAnswerLog.objects.create(
            user=user,
            question=question,
            user_answer=selected_answer,
            is_correct=is_correct,
        )

        if not is_correct:
            # 오답노트에 등록, 중복 방지
            if not WrongAnswer.objects.filter(user=user, question=question).exists():
                WrongAnswer.objects.create(user=user, question=question)

        return redirect('concept_question_list', subject_id=subject_id, lesson_id=lesson_id)

    all_questions = list(Question.objects.filter(subject=subject, lesson=lesson, question_type='concept'))
    used_questions = request.session.get('used_questions', [])

    remaining_questions = [q for q in all_questions if q.id not in used_questions]

    if len(remaining_questions) < 10:
        used_questions = []
        remaining_questions = all_questions

    selected_questions = random.sample(remaining_questions, min(10, len(remaining_questions)))

    used_questions.extend([q.id for q in selected_questions])
    request.session['used_questions'] = used_questions

    context = {
        "subject": subject,
        "lesson": lesson,
        "questions": selected_questions,
        "concept_description": lesson.concept,
    }
    return render(request, "quiz/concept_question_list.html", context)

@csrf_exempt
@login_required
def submit_answers(request, subject_id, lesson_id):
    """
    답안 제출 처리 (POST)
    form-data 방식 제출 후 채점 결과 페이지로 렌더링
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용'}, status=405)

    user = request.user
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id)

    results = []
    correct_count = 0

    try:
        for key, value in request.POST.items():
            if key.startswith('q'):
                question_id = int(key[1:])
                selected_choice = int(value)
                question = get_object_or_404(Question, pk=question_id)
                is_correct = (selected_choice == question.answer)

                UserAnswerLog.objects.create(
                    user=user,
                    question=question,
                    user_answer=selected_choice,
                    is_correct=is_correct,
                )
                if not is_correct:
                    if not WrongAnswer.objects.filter(user=user, question=question).exists():
                        WrongAnswer.objects.create(user=user, question=question)
                else:
                    # 정답 맞히면 오답노트에서 삭제
                    WrongAnswer.objects.filter(user=user, question=question).delete()

                results.append({
                    'question': question,
                    'user_choice': selected_choice,
                    'is_correct': is_correct,
                })

                if is_correct:
                    correct_count += 1

        total = len(results)
        score = int((correct_count / total) * 100) if total > 0 else 0

        # 제출 후 세션 초기화 (출제 문제 초기화)
        request.session['used_questions'] = []

        context = {
            'subject': subject,
            'lesson': lesson,
            'results': results,
            'total': total,
            'correct': correct_count,
            'score': score,
        }
        return render(request, 'quiz/concept_result.html', context)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def wrong_note_list(request):
    """
    오답노트 메인 리스트: 과목/단원별 오답 수, 오답율 표시
    """
    user = request.user

    wrong_answers = WrongAnswer.objects.filter(user=user).select_related('question__subject', 'question__lesson')

    note_dict = {}

    for wa in wrong_answers:
        subject = wa.question.subject
        lesson = wa.question.lesson
        key = (subject.id, subject.name, lesson.id, lesson.unit_name)
        if key not in note_dict:
            note_dict[key] = {
                'subject': subject,
                'lesson': lesson,
                'count': 0,
                'questions': [],
            }
        note_dict[key]['count'] += 1
        note_dict[key]['questions'].append(wa.question)

    note_list = []
    for (subj_id, subj_name, les_id, les_name), data in note_dict.items():
        total_questions = Question.objects.filter(subject_id=subj_id, lesson_id=les_id).count()
        wrong_count = data['count']
        wrong_rate = (wrong_count / total_questions * 100) if total_questions > 0 else 0
        note_list.append({
            'subject': data['subject'],
            'lesson': data['lesson'],
            'wrong_count': wrong_count,
            'total_questions': total_questions,
            'wrong_rate': round(wrong_rate, 1),
            'questions': data['questions'][:10],  # 최대 10문제만 보여주기
        })

    context = {
        'note_list': note_list,
    }
    return render(request, 'quiz/wrong_note_list.html', context)

@login_required
def wrong_note_quiz(request, subject_id, lesson_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    user = request.user

    wrong_question_ids = WrongAnswer.objects.filter(user=user).values_list('question_id', flat=True)
    print(f"[로그] 오답 문제 IDs: {list(wrong_question_ids)}")  # 오답 문제 id 리스트 출력

    wrong_questions_qs = Question.objects.filter(
        id__in=wrong_question_ids,
        subject=subject,
        lesson=lesson,
        question_type='concept',
    )
    all_wrong_questions = list(wrong_questions_qs)
    print(f"[로그] 해당 단원의 오답 문제 총 개수: {len(all_wrong_questions)}")

    used_questions = request.session.get('used_wrong_questions', [])
    print(f"[로그] 세션에 저장된 사용된 문제 IDs: {used_questions}")

    remaining_questions = [q for q in all_wrong_questions if q.id not in used_questions]
    print(f"[로그] 남은 문제 개수: {len(remaining_questions)}")

    if len(remaining_questions) < 10:
        used_questions = []
        remaining_questions = all_wrong_questions
        print("[로그] 남은 문제가 10개 미만이라 세션 초기화")

    selected_questions = random.sample(remaining_questions, min(10, len(remaining_questions)))
    print(f"[로그] 선택된 문제 ID: {[q.id for q in selected_questions]}")

    used_questions.extend([q.id for q in selected_questions])
    request.session['used_wrong_questions'] = used_questions

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith('q'):
                question_id = int(key[1:])
                selected_answer = int(value)
                question = get_object_or_404(Question, pk=question_id)
                is_correct = (selected_answer == question.answer)

                print(f"[로그] 제출된 답안 - 문제ID: {question_id}, 선택지: {selected_answer}, 정답: {question.answer}, 정답여부: {is_correct}")

                UserAnswerLog.objects.create(
                    user=user,
                    question=question,
                    user_answer=selected_answer,
                    is_correct=is_correct,
                )

                if is_correct:
                    WrongAnswer.objects.filter(user=user, question=question).delete()
                    print(f"[로그] 정답인 문제 오답노트에서 삭제됨 - 문제ID: {question_id}")

                    if question.id in used_questions:
                        used_questions.remove(question.id)
                        request.session['used_wrong_questions'] = used_questions
                        request.session.modified = True
                        print(f"[로그] 세션에서 문제ID {question_id} 제거됨")

        return redirect('wrong_note_quiz', subject_id=subject_id, lesson_id=lesson_id)

    context = {
        "subject": subject,
        "lesson": lesson,
        "questions": selected_questions,
        "concept_description": lesson.concept,
    }
    return render(request, "quiz/wrong_note_quiz.html", context)

