import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Subject, Lesson, Question, UserAnswerLog, WrongAnswer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

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
    필수/선택 과목 분리
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
    랜덤 10문제 출제, 이미 출제된 문제는 세션에 저장하여 제외
    POST 요청 시 답안 제출 처리 후 결과 저장
    """
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id)

    if request.method == "POST":
        question_id = int(request.POST.get('question_id'))
        selected_answer = int(request.POST.get('answer'))
        question = get_object_or_404(Question, pk=question_id)

        is_correct = (selected_answer == question.answer)
        user = request.user

        logger.debug(f"[concept_question_list POST] user:{user}, question:{question.id}, answer:{selected_answer}, correct:{is_correct}")

        UserAnswerLog.objects.create(
            user=user,
            question=question,
            user_answer=selected_answer,
            is_correct=is_correct,
        )

        if not is_correct:
            if not WrongAnswer.objects.filter(user=user, question=question).exists():
                WrongAnswer.objects.create(user=user, question=question)
                logger.debug(f"[concept_question_list POST] 오답노트에 추가 - 문제ID: {question.id}")

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

                logger.debug(f"[submit_answers] user:{user}, question:{question_id}, choice:{selected_choice}, correct:{is_correct}")

                UserAnswerLog.objects.create(
                    user=user,
                    question=question,
                    user_answer=selected_choice,
                    is_correct=is_correct,
                )

                if not is_correct:
                    if not WrongAnswer.objects.filter(user=user, question=question).exists():
                        WrongAnswer.objects.create(user=user, question=question)
                        logger.debug(f"[submit_answers] 오답노트에 추가 - 문제ID: {question_id}")
                else:
                    WrongAnswer.objects.filter(user=user, question=question).delete()
                    logger.debug(f"[submit_answers] 오답노트에서 삭제 - 문제ID: {question_id}")

                results.append({
                    'question': question,
                    'user_choice': selected_choice,
                    'is_correct': is_correct,
                })

                if is_correct:
                    correct_count += 1

        total = len(results)
        score = int((correct_count / total) * 100) if total > 0 else 0

        # 제출 후 세션 초기화
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
        logger.error(f"[submit_answers Exception] {e}")
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
            'questions': data['questions'][:10],
        })

    context = {
        'note_list': note_list,
    }
    return render(request, 'wrong_note_list.html', context)


@login_required
def wrong_note_quiz(request, subject_id, lesson_id):
    """
    오답노트 문제풀이 전용 뷰
    - 해당 사용자, 과목, 단원의 오답 문제만 랜덤 10문제 출제
    - 세션 기반으로 문제 재출제 방지
    - 정답 시 오답노트에서 삭제 및 세션에서 문제 제거
    - 오답이 없거나 남은 문제가 없으면 빈 리스트 전달
    """
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    user = request.user

    # 뷰 진입 시 세션 초기화 (이전 데이터 영향 제거)
    request.session['used_wrong_questions'] = []
    request.session.modified = True
    logger.debug(f"[wrong_note_quiz] 세션 초기화 - used_wrong_questions: {request.session['used_wrong_questions']}")

    # 오답 문제 ID 리스트
    wrong_answers = WrongAnswer.objects.filter(user=user)
    wrong_question_ids = list(wrong_answers.values_list('question_id', flat=True))
    logger.debug(f"[wrong_note_quiz] 오답 문제 IDs: {wrong_question_ids}")
    logger.debug(f"[wrong_note_quiz] 사용자 {user}의 오답노트 항목 수: {wrong_answers.count()}")

    # 오답 문제 필터링
    wrong_questions_qs = Question.objects.filter(
        id__in=wrong_question_ids,
        subject=subject,
        lesson=lesson,
        question_type='concept',
    )
    all_wrong_questions = list(wrong_questions_qs)
    logger.debug(f"[wrong_note_quiz] 해당 단원의 오답 문제 총 개수: {len(all_wrong_questions)}")
    logger.debug(f"[wrong_note_quiz] 오답 문제 ID 목록: {[q.id for q in all_wrong_questions]}")

    # 오답 문제가 없으면 빈 리스트로 템플릿 렌더링
    if not all_wrong_questions:
        logger.debug("[wrong_note_quiz] 오답 문제가 없음")
        context = {
            "subject": subject,
            "lesson": lesson,
            "questions": [],
            "concept_description": lesson.concept,
        }
        return render(request, "wrong_note_quiz.html", context)

    # 세션에서 사용된 문제 가져오기
    used_questions = request.session.get('used_wrong_questions', [])
    logger.debug(f"[wrong_note_quiz] 세션에 저장된 사용된 문제 IDs: {used_questions}")

    # 남은 문제 계산
    remaining_questions = [q for q in all_wrong_questions if q.id not in used_questions]
    logger.debug(f"[wrong_note_quiz] 남은 문제 개수: {len(remaining_questions)}")
    logger.debug(f"[wrong_note_quiz] 남은 문제 ID 목록: {[q.id for q in remaining_questions]}")

    # 남은 문제가 없으면 빈 리스트로 템플릿 렌더링
    if not remaining_questions:
        logger.debug("[wrong_note_quiz] 남은 오답 문제가 없음")
        context = {
            "subject": subject,
            "lesson": lesson,
            "questions": [],
            "concept_description": lesson.concept,
        }
        return render(request, "wrong_note_quiz.html", context)

    # 최대 10문제 선택
    selected_questions = random.sample(remaining_questions, min(10, len(remaining_questions)))
    logger.debug(f"[wrong_note_quiz] 선택된 문제 ID: {[q.id for q in selected_questions]}")

    # 세션에 사용된 문제 ID 추가
    used_questions.extend([q.id for q in selected_questions])
    request.session['used_wrong_questions'] = used_questions
    request.session.modified = True

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith('q'):
                question_id = int(key[1:])
                selected_answer = int(value)
                question = get_object_or_404(Question, pk=question_id)
                is_correct = (selected_answer == question.answer)

                logger.debug(f"[wrong_note_quiz POST] 제출된 답안 - 문제ID: {question_id}, 선택지: {selected_answer}, 정답: {question.answer}, 정답여부: {is_correct}")

                UserAnswerLog.objects.create(
                    user=user,
                    question=question,
                    user_answer=selected_answer,
                    is_correct=is_correct,
                )

                if is_correct:
                    WrongAnswer.objects.filter(user=user, question=question).delete()
                    logger.debug(f"[wrong_note_quiz POST] 정답인 문제 오답노트에서 삭제됨 - 문제ID: {question_id}")

                    if question.id in used_questions:
                        used_questions.remove(question.id)
                        request.session['used_wrong_questions'] = used_questions
                        request.session.modified = True
                        logger.debug(f"[wrong_note_quiz POST] 세션에서 문제ID {question_id} 제거됨")

        return redirect('wrong_note_quiz', subject_id=subject_id, lesson_id=lesson_id)

    context = {
        "subject": subject,
        "lesson": lesson,
        "questions": selected_questions,
        "concept_description": lesson.concept,
    }
    return render(request, "wrong_note_quiz.html", context)


@login_required
def retry_question(request, question_id):
    """
    오답노트 내 특정 문제 재도전용 뷰
    단일 문제만 문제풀이 화면에 전달하여 바로 문제풀이 시작
    """
    question = get_object_or_404(Question, pk=question_id)
    user = request.user

    # 해당 문제가 오답노트에 존재하는지 체크
    if not WrongAnswer.objects.filter(user=user, question=question).exists():
        # 오답노트에 없으면 리스트로 리다이렉트
        return redirect('wrong_note_list')

    subject = question.subject
    lesson = question.lesson

    # 세션 초기화 후 해당 문제만 저장
    request.session['used_wrong_questions'] = [question.id]
    request.session.modified = True

    context = {
        'subject': subject,
        'lesson': lesson,
        'questions': [question],  # 단일 문제 리스트 전달
        'concept_description': lesson.concept,
    }
    return render(request, 'wrong_note_quiz.html', context)