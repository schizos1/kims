"""Quiz views package."""

import random
import logging
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction, IntegrityError

from ..models import Subject, Lesson, Question, UserAnswerLog, WrongAnswer
from users.models import UserProfile
from trophies.utils import check_and_award_trophies

logger = logging.getLogger(__name__)


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

    logger.info(
        "퀴즈 제출 처리 시작: 사용자=%s, 과목ID=%s, 단원ID=%s", user.username, subject_id, lesson_id
    )
    logger.debug("POST 데이터: %s", request.POST)

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
                        logger.warning("잘못된 문제 ID 형식의 키: %s", key)
                        continue

                    question_id = int(question_id_str)
                    selected_choice = None
                    if value_str and value_str.strip().isdigit():
                        selected_choice = int(value_str.strip())
                    else:
                        logger.warning(
                            "문제 ID %s: 답변이 없거나 숫자 형식이 아님 (값: '%s'). 오답 처리합니다.",
                            question_id,
                            value_str,
                        )

                    total_questions_attempted_in_form += 1

                    try:
                        question = Question.objects.get(pk=question_id, lesson=lesson, subject=subject)
                    except Question.DoesNotExist:
                        logger.error(
                            "제출된 문제 ID %s를 DB에서 찾을 수 없거나 해당 단원/과목의 문제가 아님.",
                            question_id,
                        )
                        messages.error(request, f"문제 ID {question_id}를 처리 중 오류가 발생했습니다.")
                        results.append(
                            {
                                'question_text': f"문제 ID {question_id} (오류)",
                                'is_correct': False,
                                'error': '문제를 찾을 수 없음',
                            }
                        )
                        continue

                    if UserAnswerLog.objects.filter(user=user, question=question).exists():
                        logger.warning(
                            "이미 제출된 문제입니다: 사용자=%s, 문제ID=%s. 기존 기록을 사용합니다.",
                            user.id,
                            question.id,
                        )
                        existing_log = UserAnswerLog.objects.get(user=user, question=question)
                        results.append(
                            {
                                'question_text': question.text,
                                'user_choice': existing_log.user_answer,
                                'correct_answer': question.answer,
                                'is_correct': existing_log.is_correct,
                                'explanation': question.explanation,
                                'already_submitted': True,
                            }
                        )
                        if existing_log.is_correct:
                            correct_count += 1
                        continue

                    is_correct = selected_choice is not None and selected_choice == question.answer
                    logger.info(
                        "채점: 문제ID=%s, 제출답=%s, 정답=%s, 결과=%s",
                        question.id,
                        selected_choice,
                        question.answer,
                        is_correct,
                    )

                    if is_correct:
                        correct_count += 1

                    logs_to_create.append(
                        UserAnswerLog(
                            user=user,
                            question=question,
                            user_answer=selected_choice if selected_choice is not None else 0,
                            is_correct=is_correct,
                        )
                    )

                    if not is_correct:
                        if not WrongAnswer.objects.filter(user=user, question=question).exists():
                            wrong_answers_to_create_instances.append(WrongAnswer(user=user, question=question))
                    else:
                        wrong_answers_to_delete_pks.extend(
                            list(WrongAnswer.objects.filter(user=user, question=question).values_list('pk', flat=True))
                        )

                    results.append(
                        {
                            'question_text': question.text,
                            'user_choice': selected_choice,
                            'correct_answer': question.answer,
                            'is_correct': is_correct,
                            'explanation': question.explanation,
                            'already_submitted': False,
                        }
                    )

            if logs_to_create:
                UserAnswerLog.objects.bulk_create(logs_to_create)
            if wrong_answers_to_create_instances:
                WrongAnswer.objects.bulk_create(wrong_answers_to_create_instances, ignore_conflicts=True)
            if wrong_answers_to_delete_pks:
                WrongAnswer.objects.filter(pk__in=wrong_answers_to_delete_pks).delete()

            if logs_to_create:
                check_and_award_trophies(user)

    except IntegrityError as ie:
        logger.error("답변 저장 중 IntegrityError: %s", ie, exc_info=True)
        messages.error(request, "답변 저장 중 오류가 발생했습니다. 이미 처리된 요청일 수 있습니다.")
        return redirect('quiz:concept_select')
    except Exception as e:
        logger.error("퀴즈 제출 처리 중 예기치 못한 오류: %s", e, exc_info=True)
        messages.error(request, "퀴즈 제출 처리 중 오류가 발생했습니다.")
        return redirect('quiz:concept_select')

    score = 0
    if total_questions_attempted_in_form > 0:
        score = int((correct_count / total_questions_attempted_in_form) * 100)

    logger.info(
        "최종 채점 결과: 총 제출 시도 문제=%s, 정답 수=%s, 점수=%s%%",
        total_questions_attempted_in_form,
        correct_count,
        score,
    )

    question_type = request.POST.get('question_type', 'concept')
    session_key_to_clear = f'used_questions_{question_type}_{subject_id}_{lesson_id}'
    if session_key_to_clear in request.session:
        del request.session[session_key_to_clear]
        logger.info("세션 키 '%s' 초기화 완료.", session_key_to_clear)

    context = {
        'user': user,
        'userprofile': user_profile,
        'subject': subject,
        'lesson': lesson,
        'results': results,
        'total_attempted': total_questions_attempted_in_form,
        'correct_count': correct_count,
        'score': score,
        'question_type': question_type,
    }

    result_template_name = f'quiz/{question_type}_result.html'
    return render(request, result_template_name, context)


@login_required
def admin_bulk_question_upload(request):
    """AI 문제 JSON 일괄 입력 폼 및 처리."""
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
                        required_fields = [
                            'subject',
                            'lesson',
                            'question_type',
                            'text',
                            'choice1_text',
                            'choice2_text',
                            'choice3_text',
                            'choice4_text',
                            'answer',
                        ]
                        for field in required_fields:
                            field_value = q_data.get(field)
                            if field == 'answer' and field_value is None:
                                raise ValueError(f"{i}번째:필수필드'{field}'없음")
                            elif field != 'answer' and not str(field_value).strip():
                                raise ValueError(f"{i}번째:필수필드'{field}'없거나공백")
                        subject_name = q_data['subject'].strip()
                        lesson_name = q_data['lesson'].strip()
                        grade = q_data.get('grade', '').strip()
                        subject, _ = Subject.objects.get_or_create(name=subject_name)
                        lesson_defaults = {'grade': grade}
                        if q_data.get('lesson_concept'):
                            lesson_defaults['concept'] = q_data['lesson_concept'].strip()
                        lesson, lesson_created = Lesson.objects.get_or_create(
                            subject=subject,
                            unit_name=lesson_name,
                            defaults=lesson_defaults,
                        )
                        if lesson_created and lesson.concept:
                            updated_lesson_info.add(f"'{lesson.unit_name}'({subject.name})-개념추가")
                        elif (
                            not lesson_created
                            and q_data.get('lesson_concept')
                            and lesson.concept != q_data['lesson_concept'].strip()
                        ):
                            lesson.concept = q_data['lesson_concept'].strip()
                            lesson.save(update_fields=['concept'])
                            updated_lesson_info.add(f"'{lesson.unit_name}'({subject.name})-개념업데이트")
                        question_instance_data = {
                            'subject': subject,
                            'lesson': lesson,
                            'question_type': q_data['question_type'].strip(),
                            'text': q_data['text'].strip(),
                            'answer': int(q_data['answer']),
                            'year': q_data.get('year', '').strip(),
                            'number': q_data.get('number', '').strip(),
                            'image': q_data.get('image', '').strip(),
                            'choice1_text': q_data['choice1_text'].strip(),
                            'choice1_image': q_data.get('choice1_image', '').strip(),
                            'choice2_text': q_data['choice2_text'].strip(),
                            'choice2_image': q_data.get('choice2_image', '').strip(),
                            'choice3_text': q_data['choice3_text'].strip(),
                            'choice3_image': q_data.get('choice3_image', '').strip(),
                            'choice4_text': q_data['choice4_text'].strip(),
                            'choice4_image': q_data.get('choice4_image', '').strip(),
                            'explanation': q_data.get('explanation', '').strip(),
                            'explanation_image': q_data.get('explanation_image', '').strip(),
                        }
                        questions_to_create.append(Question(**question_instance_data))
                    except ValueError as ve:
                        errors.append(f"{i}번째 문제: {ve}")
                    except Exception as e:
                        errors.append(f"{i}번째 문제 처리오류 ({type(e).__name__}): {e}")
                if not errors and questions_to_create:
                    Question.objects.bulk_create(questions_to_create)
                    msg = f"{len(questions_to_create)}개 문제 업로드 성공."
                    if updated_lesson_info:
                        msg += f" 단원정보 업데이트: {', '.join(list(updated_lesson_info))}."
                    messages.success(request, msg)
                elif errors:
                    messages.error(request, f"총{len(questions_input_list)}문제중 {len(errors)}개오류.저장안됨.")
                    for idx, err_msg in enumerate(errors[:5]):
                        messages.warning(request, f"오류{idx+1}: {err_msg}")
                elif not questions_to_create:
                    messages.info(request, "업로드할 유효한 문제 없음.")
        except json.JSONDecodeError:
            messages.error(request, "JSON 데이터 형식 오류. 배열/문법 확인.")
        except Exception as e:
            logger.error("JSON 일괄 업로드 중 오류: %s", e, exc_info=True)
            messages.error(request, f"처리 중 오류 발생: {e}")
        return redirect('quiz:admin_bulk_question_upload')
    return render(request, 'quiz/admin_bulk_question_upload.html')


from .concept_views import *  # noqa: F401,F403
from .past_views import *  # noqa: F401,F403
from .wrongnote_views import *  # noqa: F401,F403
from .stats_views import *  # noqa: F401,F403