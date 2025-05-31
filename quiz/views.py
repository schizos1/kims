# quiz/views.py

import random
import logging
import json # admin_bulk_question_upload 에서 사용

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse # attendance_events 에서만 사용 (FullCalendar용)
# from django.views.decorators.csrf import csrf_exempt # submit_answers 에서는 제거 (템플릿에 csrf_token 사용)
from django.db import transaction, IntegrityError

from .models import Subject, Lesson, Question, UserAnswerLog, WrongAnswer
from users.models import UserProfile
from trophies.utils import check_and_award_trophies # 경로 및 함수 존재 확인 필요

logger = logging.getLogger(__name__)

@login_required
def concept_select(request):
    """문제 유형(개념/기출) 중 개념 문제 선택 후 과목 선택으로 연결되는 페이지입니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    # 이 뷰는 보통 과목 선택 페이지로 바로 연결되므로, 특별한 컨텍스트가 필요 없을 수 있습니다.
    # 여기서는 concept_subject_list로 바로 가는 버튼만 있는 페이지라고 가정하거나,
    # 아니면 이 뷰 없이 바로 concept_subject_list를 메뉴에 연결할 수도 있습니다.
    context = {
        "user": user,
        "userprofile": user_profile,
    }
    return render(request, "quiz/concept_select.html", context) # 해당 템플릿 필요

@login_required
def past_select(request):
    """기출문제 과목 선택 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    
    required_names = ["국어", "수학", "사회", "과학"]
    all_subjects = Subject.objects.all().order_by('name')

    required_subjects_with_delay = []
    elective_subjects_with_delay = []

    for i, subject_instance in enumerate(s for s in all_subjects if s.name in required_names):
        required_subjects_with_delay.append({
            'obj': subject_instance, 'animation_delay_s': f"{i * 0.1:.1f}s" 
        })
    
    elective_offset = len(required_subjects_with_delay)
    for i, subject_instance in enumerate(s for s in all_subjects if s.name not in required_names):
        elective_subjects_with_delay.append({
            'obj': subject_instance, 'animation_delay_s': f"{(elective_offset + i) * 0.05 + 0.1:.2f}s"
        })
        
    context = {
        "user": user, "userprofile": user_profile,
        "required_subjects": required_subjects_with_delay,
        "elective_subjects": elective_subjects_with_delay,
    }
    return render(request, "quiz/past_select.html", context)


@login_required
def concept_subject_list(request):
    """개념문제 과목 목록 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    required_names = ["국어", "수학", "사회", "과학"]
    all_subjects = Subject.objects.all().order_by('name')
    # (이하 로직은 사용자님이 보내주신 코드와 동일하게 유지)
    required_subjects_with_delay = []
    elective_subjects_with_delay = []
    for i, subject_instance in enumerate(s for s in all_subjects if s.name in required_names):
        required_subjects_with_delay.append({'obj': subject_instance, 'animation_delay_s': f"{i * 0.1:.1f}s"})
    elective_offset = len(required_subjects_with_delay) 
    for i, subject_instance in enumerate(s for s in all_subjects if s.name not in required_names):
        elective_subjects_with_delay.append({'obj': subject_instance, 'animation_delay_s': f"{(elective_offset + i) * 0.05 + 0.1:.2f}s"})
    context = {"user": user, "userprofile": user_profile, "required_subjects": required_subjects_with_delay, "elective_subjects": elective_subjects_with_delay,}
    logger.debug(f"Context for concept_subject_list: {context}")
    return render(request, "quiz/concept_subject_list.html", context)


@login_required
def concept_lesson_list(request, subject_id):
    """개념문제 단원 목록 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    subject = get_object_or_404(Subject, pk=subject_id)
    # (이하 로직은 사용자님이 보내주신 코드와 동일하게 유지)
    lessons_qs = Lesson.objects.filter(subject=subject).order_by('unit_name')
    lessons_with_delay = []
    for i, lesson_obj in enumerate(lessons_qs):
        lessons_with_delay.append({'obj': lesson_obj, 'animation_delay_s': f"{i * 0.08:.2f}s"})
    context = {"user": user, "userprofile": user_profile, "subject": subject, "lessons": lessons_with_delay,}
    return render(request, "quiz/concept_lesson_list.html", context)

@login_required
def past_lesson_list(request, subject_id):
    """기출문제 단원 목록 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    subject = get_object_or_404(Subject, pk=subject_id)
    # (이하 로직은 사용자님이 보내주신 코드와 동일하게 유지)
    lessons_qs = Lesson.objects.filter(subject=subject).order_by('unit_name')
    lessons_with_delay = []
    for i, lesson_obj in enumerate(lessons_qs):
        lessons_with_delay.append({'obj': lesson_obj, 'animation_delay_s': f"{i * 0.08:.2f}s"})
    context = {"user": user, "userprofile": user_profile, "subject": subject, "lessons": lessons_with_delay,}
    return render(request, "quiz/past_lesson_list.html", context)

@login_required
def concept_question_list(request, subject_id, lesson_id):
    """개념문제 문제풀이 페이지를 렌더링합니다. (답변 제출은 submit_answers 뷰로 처리)"""
    # POST 로직은 submit_answers로 이전되었으므로, 여기서는 GET 요청만 처리하여 문제 목록을 보여줍니다.
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, subject=subject) # subject 확인 추가

    # (이하 GET 요청 처리 로직은 사용자님이 보내주신 코드와 거의 동일하게 유지)
    session_key = f'used_questions_concept_{subject_id}_{lesson_id}' # 세션 키 명확화
    all_questions_in_lesson = list(Question.objects.filter(subject=subject, lesson=lesson, question_type='concept'))
    used_questions_session = request.session.get(session_key, [])

    submitted_question_ids = set(UserAnswerLog.objects.filter(
        user=request.user, question__in=all_questions_in_lesson
    ).values_list('question_id', flat=True))

    available_questions = [
        q for q in all_questions_in_lesson
        if q.id not in used_questions_session and q.id not in submitted_question_ids
    ]
    logger.debug(f"Session_key: {session_key}, Used_session: {used_questions_session}, Submitted_DB: {submitted_question_ids}, Available: {len(available_questions)}")

    if not available_questions and all_questions_in_lesson:
        logger.debug(f"All concept questions in lesson {lesson_id} for subject {subject_id} done. Resetting session.")
        if session_key in request.session: del request.session[session_key] # 세션에서 키 삭제
        used_questions_session = [] # 로컬 변수도 초기화
        available_questions = [q for q in all_questions_in_lesson if q.id not in submitted_question_ids]
        if not available_questions:
             messages.info(request, "이 단원의 모든 개념 문제를 이미 다 푸셨습니다!")

    selected_questions = []
    if available_questions:
        num_to_select = min(10, len(available_questions)) # 한 번에 보여줄 문제 수
        selected_questions = random.sample(available_questions, num_to_select)

    # 현재 선택된 문제들을 세션에 '이번에 풀 문제'로 기록 (선택 사항, 중복 방지 강화)
    # 또는 제출 시점에 세션 업데이트 없이, 다음 문제 요청 시 사용된 것으로 간주
    # 여기서는 일단 이전처럼 newly_used_ids를 used_questions_session에 추가하는 방식 유지
    newly_used_ids_for_session = [q.id for q in selected_questions]
    updated_used_questions_for_session = list(set(used_questions_session + newly_used_ids_for_session))
    request.session[session_key] = updated_used_questions_for_session
    # request.session.modified = True # 세션 리스트/딕셔너리 직접 수정 시 필요할 수 있음

    logger.debug(f"Selected concept questions IDs: {newly_used_ids_for_session}, Updated session for {session_key}: {updated_used_questions_for_session}")

    context = {
        "user": user, "userprofile": user_profile,
        "subject": subject, "lesson": lesson, "questions": selected_questions,
        "concept_description": lesson.concept,
        "question_type": "concept", # 템플릿에서 submit_answers URL 생성 시 사용
    }
    return render(request, "quiz/concept_question_list.html", context)

@login_required
def past_question_list(request, subject_id, lesson_id):
    """기출문제 문제풀이 페이지를 렌더링합니다. (답변 제출은 submit_answers 뷰로 처리)"""
    # POST 로직은 submit_answers로 이전, GET 요청만 처리
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, subject=subject)

    # (이하 GET 요청 처리 로직은 사용자님이 보내주신 코드와 거의 동일하게 유지, 세션키 명확화)
    session_key = f'used_questions_past_{subject_id}_{lesson_id}' # 세션 키 명확화
    all_questions_in_lesson = list(Question.objects.filter(subject=subject, lesson=lesson, question_type='past').order_by('year', 'number'))
    used_questions_session = request.session.get(session_key, [])
    submitted_question_ids = set(UserAnswerLog.objects.filter(user=request.user, question__in=all_questions_in_lesson).values_list('question_id', flat=True))
    available_questions = [q for q in all_questions_in_lesson if q.id not in used_questions_session and q.id not in submitted_question_ids]
    logger.debug(f"Session_key: {session_key}, Used_session: {used_questions_session}, Submitted_DB: {submitted_question_ids}, Available: {len(available_questions)}")

    if not available_questions and all_questions_in_lesson:
        logger.debug(f"All past questions in lesson {lesson_id} for subject {subject_id} done. Resetting session.")
        if session_key in request.session: del request.session[session_key]
        used_questions_session = []
        available_questions = [q for q in all_questions_in_lesson if q.id not in submitted_question_ids]
        if not available_questions:
            messages.info(request, "이 단원의 모든 기출 문제를 이미 다 푸셨습니다!")

    selected_questions = []
    if available_questions:
        num_to_select = min(10, len(available_questions))
        # 기출문제는 순서대로 (또는 random.sample)
        selected_questions = available_questions[:num_to_select] # 예시: 순서대로
        # selected_questions = random.sample(available_questions, num_to_select) 
    
    newly_used_ids_for_session = [q.id for q in selected_questions]
    updated_used_questions_for_session = list(set(used_questions_session + newly_used_ids_for_session))
    request.session[session_key] = updated_used_questions_for_session

    logger.debug(f"Selected past questions IDs: {newly_used_ids_for_session}, Updated session for {session_key}: {updated_used_questions_for_session}")

    context = {
        "user": user, "userprofile": user_profile,
        "subject": subject, "lesson": lesson, "questions": selected_questions,
        "concept_description": lesson.concept, # 기출문제 페이지에도 개념 설명 표시 가능
        "question_type": "past", # 템플릿에서 submit_answers URL 생성 시 사용
    }
    return render(request, "quiz/past_question_list.html", context)


# @csrf_exempt # 템플릿에 {% csrf_token %}을 사용하므로 제거하는 것이 좋습니다.
@login_required
def submit_answers(request, subject_id, lesson_id):
    """(개념/기출/오답 등) 다수 문제 동시 답변 제출 처리 및 채점 결과."""
    if request.method != 'POST':
        messages.error(request, "잘못된 요청 방식입니다.")
        question_type_for_redirect = request.GET.get('type', 'concept')
        if question_type_for_redirect == 'concept':
            return redirect('quiz:concept_lesson_list', subject_id=subject_id)
        elif question_type_for_redirect == 'past':
            return redirect('quiz:past_lesson_list', subject_id=subject_id)
        else:
            return redirect('quiz:concept_select')

    user = request.user
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, subject=subject)

    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(request, "사용자 프로필을 찾을 수 없습니다. 다시 로그인해주세요.")
        return redirect('core:home')

    logger.info(f"퀴즈 제출 처리 시작: 사용자={user.username}, 과목ID={subject_id}, 단원ID={lesson_id}")
    logger.debug(f"POST 데이터: {request.POST}")

    results = []
    correct_count = 0
    total_questions_attempted_in_form = 0

    logs_to_create = []
    wrong_answers_to_create_instances = []
    wrong_answers_to_delete_pks = []

    try:
        with transaction.atomic():
            for key, value_str in request.POST.items():
                if key.startswith('q_'):
                    question_id_str = key.split('_')[1]
                    if not question_id_str.isdigit():
                        logger.warning(f"잘못된 문제 ID 형식의 키: {key}")
                        continue

                    question_id = int(question_id_str)
                    selected_choice = None
                    if value_str and value_str.strip().isdigit():
                        selected_choice = int(value_str.strip())
                    else:
                        logger.warning(f"문제 ID {question_id}: 답변이 없거나 숫자 형식이 아님 (값: '{value_str}'). 오답 처리합니다.")

                    total_questions_attempted_in_form += 1

                    try:
                        question = Question.objects.get(pk=question_id, lesson=lesson, subject=subject)
                    except Question.DoesNotExist:
                        logger.error(f"제출된 문제 ID {question_id}를 DB에서 찾을 수 없거나 해당 단원/과목의 문제가 아님.")
                        messages.error(request, f"문제 ID {question_id}를 처리 중 오류가 발생했습니다.")
                        results.append({'question_text': f"문제 ID {question_id} (오류)", 'is_correct': False, 'error': '문제를 찾을 수 없음'})
                        continue

                    # 이미 제출한 문제인지 UserAnswerLog에서 확인
                    if UserAnswerLog.objects.filter(user=user, question=question).exists():
                        logger.warning(f"이미 제출된 문제입니다: 사용자={user.id}, 문제ID={question.id}. 기존 기록을 사용합니다.")
                        existing_log = UserAnswerLog.objects.get(user=user, question=question)
                        results.append({
                            'question_text': question.text, 'user_choice': existing_log.user_answer,
                            'correct_answer': question.answer, 'is_correct': existing_log.is_correct,
                            'explanation': question.explanation, 'already_submitted': True
                        })
                        if existing_log.is_correct: correct_count += 1
                        continue

                    is_correct = (selected_choice is not None and selected_choice == question.answer)
                    logger.info(f"채점: 문제ID={question.id}, 제출답={selected_choice}, 정답={question.answer}, 결과={is_correct}")

                    if is_correct:
                        correct_count += 1

                    logs_to_create.append(UserAnswerLog(
                        user=user, question=question, 
                        user_answer=selected_choice if selected_choice is not None else 0,
                        is_correct=is_correct
                    ))

                    if not is_correct:
                        if not WrongAnswer.objects.filter(user=user, question=question).exists():
                            wrong_answers_to_create_instances.append(WrongAnswer(user=user, question=question))
                    else:
                        wrong_answers_to_delete_pks.extend(
                            list(WrongAnswer.objects.filter(user=user, question=question).values_list('pk', flat=True))
                        )

                    results.append({
                        'question_text': question.text, 'user_choice': selected_choice,
                        'correct_answer': question.answer, 'is_correct': is_correct,
                        'explanation': question.explanation, 'already_submitted': False
                    })

            # DB 작업 실행
            if logs_to_create:
                UserAnswerLog.objects.bulk_create(logs_to_create)
            if wrong_answers_to_create_instances:
                WrongAnswer.objects.bulk_create(wrong_answers_to_create_instances, ignore_conflicts=True)
            if wrong_answers_to_delete_pks:
                WrongAnswer.objects.filter(pk__in=wrong_answers_to_delete_pks).delete()

            if logs_to_create:
                check_and_award_trophies(user)

    except IntegrityError as ie:
        logger.error(f"답변 저장 중 IntegrityError: {ie}", exc_info=True)
        messages.error(request, "답변 저장 중 오류가 발생했습니다. 이미 처리된 요청일 수 있습니다.")
        return redirect('quiz:concept_select')
    except Exception as e:
        logger.error(f"퀴즈 제출 처리 중 예기치 못한 오류: {e}", exc_info=True)
        messages.error(request, "퀴즈 제출 처리 중 오류가 발생했습니다.")
        return redirect('quiz:concept_select')

    score = 0
    if total_questions_attempted_in_form > 0:
        score = int((correct_count / total_questions_attempted_in_form) * 100)

    logger.info(f"최종 채점 결과: 총 제출 시도 문제={total_questions_attempted_in_form}, 정답 수={correct_count}, 점수={score}%")

    question_type = request.POST.get('question_type', 'concept')
    session_key_to_clear = f'used_questions_{question_type}_{subject_id}_{lesson_id}'
    if session_key_to_clear in request.session:
        del request.session[session_key_to_clear]
        logger.info(f"세션 키 '{session_key_to_clear}' 초기화 완료.")

    context = {
        'user': user, 'userprofile': user_profile,
        'subject': subject, 'lesson': lesson,
        'results': results, 
        'total_attempted': total_questions_attempted_in_form,
        'correct_count': correct_count, 'score': score,
        'question_type': question_type,
    }

    result_template_name = f'quiz/{question_type}_result.html'
    return render(request, result_template_name, context)


@login_required
def wrong_note_list(request):
    """오답노트 목록 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    # (이하 로직은 사용자님이 보내주신 코드와 동일하게 유지)
    wrong_answers = WrongAnswer.objects.filter(user=user).select_related('question__subject', 'question__lesson').order_by('question__subject__name', 'question__lesson__unit_name')
    note_dict = {}
    for wa in wrong_answers:
        subject = wa.question.subject
        lesson = wa.question.lesson
        lesson_id_key = lesson.id if lesson else 0
        lesson_unit_name_key = lesson.unit_name if lesson else "미지정 단원"
        key = (subject.id, subject.name, lesson_id_key, lesson_unit_name_key)
        if key not in note_dict: note_dict[key] = {'subject': subject, 'lesson': lesson, 'count': 0, 'questions': [], 'lesson_id_for_url': lesson_id_key}
        note_dict[key]['count'] += 1
        note_dict[key]['questions'].append(wa.question)
    cards_list = []
    for data_dict in note_dict.values():
        cards_list.append({'subject': data_dict['subject'], 'lesson': data_dict['lesson'], 'wrong_count': data_dict['count'], 'questions_preview': data_dict['questions'][:5], 'lesson_id_for_url': data_dict['lesson_id_for_url']})
    cards_list.sort(key=lambda x: (x['subject'].name, x['lesson'].unit_name if x['lesson'] else ""))
    context = {'user': user, 'userprofile': user_profile, 'cards': cards_list,}
    return render(request, 'quiz/wrong_note_list.html', context)


@login_required
def wrong_note_quiz(request, subject_id, lesson_id):
    """오답노트 문제를 풀이하는 페이지를 렌더링하고, 답변 제출은 submit_answers로 처리합니다."""
    # POST 로직은 submit_answers 뷰로 이전될 수 있으나, 현재는 자체 POST 처리 로직이 있음.
    # 일관성을 위해 wrong_note_quiz도 GET만 처리하고, 폼 action을 submit_answers로 보내는 것을 고려할 수 있습니다.
    # 여기서는 일단 기존 POST 로직을 유지하되, submit_answers와 유사하게 개선할 여지가 있습니다.
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = None
    if int(lesson_id) != 0: # lesson_id가 0이면 "미지정 단원"으로 간주
        lesson = get_object_or_404(Lesson, pk=lesson_id, subject=subject)

    # (이하 GET 및 POST 로직은 사용자님이 보내주신 코드와 거의 동일하게 유지, 일부 로깅 및 메시지 추가 가능)
    q_filter = {'question__subject': subject}
    if lesson: q_filter['question__lesson'] = lesson
    else: q_filter['question__lesson__isnull'] = True
    wrong_question_ids = WrongAnswer.objects.filter(user=user, **q_filter).values_list('question_id', flat=True)
    all_available_wrong_questions = list(Question.objects.filter(pk__in=wrong_question_ids))

    session_key = f'used_questions_wrong_note_{subject_id}_{lesson_id}' # 세션 키 명확화

    if not all_available_wrong_questions:
        messages.success(request, f"{subject.name} ({lesson.unit_name if lesson else '미지정 단원'})의 모든 오답 문제를 해결하셨습니다!")
        if session_key in request.session: del request.session[session_key]
        context = {"user": user, "userprofile": user_profile, "subject": subject, "lesson": lesson, "questions": [], "all_corrected": True, "question_type": "wrong_note"}
        return render(request, "quiz/wrong_answer.html", context) # wrong_answer.html 템플릿 사용 가정

    # POST 요청 처리 (개선된 submit_answers와 유사하게 리팩토링 가능)
    # POST 요청 처리
    if request.method == "POST":
        answered_correctly_this_time_ids = []
        form_errors_post = [] # 폼 제출 자체의 오류 (예: 형식 오류)
        submission_warnings_post = [] # 제출 관련 경고 (예: 중복 제출)

        try:
            with transaction.atomic(): # 트랜잭션 시작
                for key, value_str in request.POST.items():
                    if key.startswith('q_') and key.split('_')[1].isdigit():
                        question_id = int(key.split('_')[1])
                        selected_answer_str = value_str.strip()
                        
                        selected_answer = None
                        if not selected_answer_str or not selected_answer_str.isdigit():
                            logger.warning(f"오답노트: 문제 ID {question_id}: 답변이 없거나 숫자 형식이 아님 (값: '{selected_answer_str}').")
                            form_errors_post.append(f"문제 ID {question_id}: 답변 형식이 올바르지 않거나 선택되지 않았습니다.")
                            # 필요시 results 리스트 등에 오류 정보 추가
                            continue # 다음 문제로
                        
                        selected_answer = int(selected_answer_str)
                        question = get_object_or_404(Question, pk=question_id)
                        is_correct = (selected_answer == question.answer)

                        # UserAnswerLog 처리: 이미 기록이 있다면 만들지 않음 (또는 업데이트)
                        # 오답노트 풀이에서는 매번 새로운 로그를 남길 수도 있고,
                        # 기존 로그를 업데이트하거나, 아예 로그를 남기지 않을 수도 있습니다.
                        # 여기서는 submit_answers와 유사하게, 기존 로그가 없다면 새로 생성합니다.
                        # 만약 오답노트 풀이는 로그를 남기지 않으려면 이 부분을 주석 처리합니다.
                        if not UserAnswerLog.objects.filter(user=user, question=question).exists():
                            UserAnswerLog.objects.create(user=user, question=question, user_answer=selected_answer, is_correct=is_correct)
                        else:
                            # 이미 로그가 있다면, 이번 시도에 대한 별도 기록은 남기지 않거나,
                            # 혹은 마지막 시도 시간 등을 업데이트 할 수 있습니다.
                            logger.warning(f"오답노트: UserAnswerLog 이미 존재 (u={user.id}, q={question_id}). 새로 생성 안 함.")
                            submission_warnings_post.append(f"'{question.text[:20]}...' 문제는 이전에 푼 기록이 있습니다.")


                        if is_correct:
                            answered_correctly_this_time_ids.append(question_id)
                            # 정답을 맞혔으므로 WrongAnswer 테이블에서 해당 오답 기록 삭제
                            WrongAnswer.objects.filter(user=user, question=question).delete()
                
                # 세션 업데이트 (이번 시도에서 맞힌 문제 ID들 추가 - 오답노트에서 제거되었으므로)
                current_solved_in_session = request.session.get(session_key, [])
                current_solved_in_session.extend(answered_correctly_this_time_ids)
                request.session[session_key] = list(set(current_solved_in_session)) 
                # request.session.modified = True # 리스트가 변경되었으므로 명시

                if answered_correctly_this_time_ids:
                    messages.success(request, f"{len(answered_correctly_this_time_ids)}개의 오답을 해결했습니다!")
                
                # 모든 문제 처리 후 트로피 조건 확인
                check_and_award_trophies(user)

        except Exception as e: # 포괄적인 예외 처리
            logger.error(f"[wrong_note_quiz POST] 답변 처리 중 오류: {e}", exc_info=True)
            messages.error(request, "오답 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
            # 오류 발생 시 현재 페이지로 다시 돌아가거나, 오답노트 목록으로 리다이렉트
            return redirect('quiz:wrong_note_quiz', subject_id=subject_id, lesson_id=lesson_id) # 현재 페이지로
        
        # 모든 POST 처리가 끝난 후 리다이렉트
        # (맞힌 문제가 있다면 다음 오답 문제 세트를 보여주기 위해 같은 페이지로 리다이렉트)
        return redirect('quiz:wrong_note_quiz', subject_id=subject_id, lesson_id=lesson_id)


    # GET 요청 시 문제 선택 로직 (기존과 유사)
    solved_in_this_session_ids = request.session.get(session_key, [])
    remaining_questions_for_this_attempt = [q for q in all_available_wrong_questions if q.id not in solved_in_this_session_ids]

    if not remaining_questions_for_this_attempt and all_available_wrong_questions: # 세션에서 다 풀었지만, 아직 오답이 남아있을 수 있음
        if session_key in request.session: del request.session[session_key] # 세션 초기화하고 다시 문제 로드
        messages.info(request, "이 오답 그룹의 문제들을 한 번씩 다 풀었습니다. 다시 시도합니다.")
        return redirect('quiz:wrong_note_quiz', subject_id=subject_id, lesson_id=lesson_id)

    selected_questions = []
    if remaining_questions_for_this_attempt:
        num_to_select = min(10, len(remaining_questions_for_this_attempt)) # 한 번에 보여줄 오답 수
        selected_questions = random.sample(remaining_questions_for_this_attempt, num_to_select)
    
    logger.debug(f"[wrong_note_quiz GET] 선택된 문제 ID ({session_key}): {[q.id for q in selected_questions]}")

    context = {
        "user": user, "userprofile": user_profile,
        "subject": subject, "lesson": lesson, "questions": selected_questions,
        "concept_description": lesson.concept if lesson else "오답 문제를 다시 풀어보세요.",
        "question_type": "wrong_note", # 템플릿 폼 action URL 생성 시 또는 결과 페이지에서 사용
    }
    return render(request, "quiz/wrong_answer.html", context) # 오답풀이용 템플릿


@login_required
def retry_question(request, question_id):
    """오답노트의 특정 문제를 재도전하는 페이지를 렌더링하고 답변을 처리합니다."""
    # (이하 로직은 사용자님이 보내주신 코드와 동일하게 유지, 일부 로깅 및 메시지 추가 가능)
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    question = get_object_or_404(Question, pk=question_id)
    subject = question.subject
    lesson = question.lesson

    if request.method == "POST":
        selected_answer_str = request.POST.get('answer')
        if not selected_answer_str or not selected_answer_str.strip().isdigit():
            messages.error(request, "답변을 선택하거나 올바른 형식으로 입력해주세요.")
            return redirect('quiz:retry_question', question_id=question_id)
        selected_answer = int(selected_answer_str.strip())

        is_correct = selected_answer == question.answer
        
        try:
            with transaction.atomic(): # 트랜잭션 시작
                # UserAnswerLog 처리: 이미 기록이 있는지 확인
                ual_exists = UserAnswerLog.objects.filter(user=user, question=question).exists()
                if not ual_exists:
                    UserAnswerLog.objects.create(user=user, question=question, user_answer=selected_answer, is_correct=is_correct)
                else:
                    # 이미 기록이 있다면, 업데이트하거나 무시할 수 있습니다.
                    # 여기서는 일단 새로 생성하지 않고, 기존 기록을 존중합니다.
                    logger.warning(f"UserAnswerLog 이미 존재 (재시도): u={user.id}, q={question_id}")
                    # 만약 재시도 시 정답을 맞혔다면 기존 로그의 is_correct를 업데이트 할 수도 있습니다.
                    # 예: if is_correct: UserAnswerLog.objects.filter(user=user, question=question).update(is_correct=True, user_answer=selected_answer, timestamp=timezone.now())

                # WrongAnswer 처리
                if not is_correct:
                    # 오답인 경우, WrongAnswer에 없으면 추가
                    if not WrongAnswer.objects.filter(user=user, question=question).exists():
                        WrongAnswer.objects.create(user=user, question=question)
                elif is_correct: # 정답인 경우
                    deleted_count, _ = WrongAnswer.objects.filter(user=user, question=question).delete()
                    if deleted_count > 0: 
                        messages.success(request, "정답! 오답노트에서 삭제되었습니다.")
                    else: # 이미 오답노트에 없던 문제 (원래 정답이었거나, 이전 재시도에서 맞힘)
                        messages.success(request, "정답입니다!")
                
                check_and_award_trophies(user)

        except Exception as e: # 포괄적인 예외 처리
            logger.error(f"[retry_question POST] 답변 처리 중 오류: {e}", exc_info=True)
            messages.error(request, "답변 처리 중 오류가 발생했습니다.")
            return redirect('quiz:retry_question', question_id=question_id) # 현재 페이지로 리다이렉트
        
        return redirect('quiz:wrong_note_list') # 재시도 후 오답노트 목록으로

    context = {
        'user': user, 'userprofile': user_profile,
        'subject': subject, 'lesson': lesson, 'questions': [question], # 단일 문제
        'concept_description': lesson.concept if lesson else "문제를 다시 풀어보세요.",
        'is_retry_page': True,
        'question_type': 'retry', # 템플릿에서 필요시 사용
    }
    return render(request, 'quiz/wrong_answer.html', context) # 오답풀이용 템플릿 공유


@login_required
def admin_bulk_question_upload(request):
    """AI 문제 JSON 일괄 입력 폼 및 처리."""
    # (이하 로직은 사용자님이 보내주신 코드와 동일하게 유지)
    if not request.user.is_staff:
        messages.error(request, "이 페이지에 접근할 권한이 없습니다.")
        return redirect('/')
    if request.method == 'POST':
        json_data_str = request.POST.get('json_data')
        if not json_data_str:
            messages.error(request, "입력된 JSON 데이터가 없습니다.")
            return render(request, 'quiz/admin_bulk_question_upload.html')
        try:
            questions_input_list = json.loads(json_data_str)
            if not isinstance(questions_input_list, list):
                messages.error(request, "JSON 데이터는 배열(리스트) 형태여야 합니다.")
                return render(request, 'quiz/admin_bulk_question_upload.html')
            questions_to_create = []
            updated_lesson_info = set()
            errors = []
            with transaction.atomic():
                for i, q_data in enumerate(questions_input_list, 1):
                    try:
                        required_fields = ['subject', 'lesson', 'question_type', 'text', 'choice1_text', 'choice2_text', 'choice3_text', 'choice4_text', 'answer']
                        for field in required_fields:
                            field_value = q_data.get(field)
                            if field == 'answer' and field_value is None: raise ValueError(f"{i}번째:필수필드'{field}'없음")
                            elif field != 'answer' and not str(field_value).strip(): raise ValueError(f"{i}번째:필수필드'{field}'없거나공백")
                        subject_name = q_data['subject'].strip()
                        lesson_name = q_data['lesson'].strip()
                        grade = q_data.get('grade', '').strip()
                        subject, _ = Subject.objects.get_or_create(name=subject_name)
                        lesson_defaults = {'grade': grade}
                        if q_data.get('lesson_concept'): lesson_defaults['concept'] = q_data['lesson_concept'].strip()
                        lesson, lesson_created = Lesson.objects.get_or_create(subject=subject, unit_name=lesson_name, defaults=lesson_defaults)
                        if lesson_created and lesson.concept: updated_lesson_info.add(f"'{lesson.unit_name}'({subject.name})-개념추가")
                        elif not lesson_created and q_data.get('lesson_concept') and lesson.concept != q_data['lesson_concept'].strip():
                            lesson.concept = q_data['lesson_concept'].strip()
                            lesson.save(update_fields=['concept'])
                            updated_lesson_info.add(f"'{lesson.unit_name}'({subject.name})-개념업데이트")
                        question_instance_data = { 'subject': subject, 'lesson': lesson, 'question_type': q_data['question_type'].strip(), 'text': q_data['text'].strip(), 'answer': int(q_data['answer']), 'year': q_data.get('year', '').strip(), 'number': q_data.get('number', '').strip(), 'image': q_data.get('image', '').strip(), 'choice1_text': q_data['choice1_text'].strip(), 'choice1_image': q_data.get('choice1_image', '').strip(), 'choice2_text': q_data['choice2_text'].strip(), 'choice2_image': q_data.get('choice2_image', '').strip(), 'choice3_text': q_data['choice3_text'].strip(), 'choice3_image': q_data.get('choice3_image', '').strip(), 'choice4_text': q_data['choice4_text'].strip(), 'choice4_image': q_data.get('choice4_image', '').strip(), 'explanation': q_data.get('explanation', '').strip(), 'explanation_image': q_data.get('explanation_image', '').strip() }
                        questions_to_create.append(Question(**question_instance_data))
                    except ValueError as ve: errors.append(f"{i}번째 문제: {ve}")
                    except Exception as e: errors.append(f"{i}번째 문제 처리오류 ({type(e).__name__}): {e}")
                if not errors and questions_to_create:
                    Question.objects.bulk_create(questions_to_create)
                    msg = f"{len(questions_to_create)}개 문제 업로드 성공."
                    if updated_lesson_info: msg += f" 단원정보 업데이트: {', '.join(list(updated_lesson_info))}."
                    messages.success(request, msg)
                elif errors:
                    messages.error(request, f"총{len(questions_input_list)}문제중 {len(errors)}개오류.저장안됨.")
                    for idx, err_msg in enumerate(errors[:5]): messages.warning(request, f"오류{idx+1}: {err_msg}")
                elif not questions_to_create: messages.info(request, "업로드할 유효한 문제 없음.")
        except json.JSONDecodeError: messages.error(request, "JSON 데이터 형식 오류. 배열/문법 확인.")
        except Exception as e:
            logger.error(f"JSON 일괄 업로드 중 오류: {e}", exc_info=True)
            messages.error(request, f"처리 중 오류 발생: {e}")
        return redirect('quiz:admin_bulk_question_upload')
    return render(request, 'quiz/admin_bulk_question_upload.html')