import random
import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from ..models import Question, WrongAnswer, Lesson, Subject, UserAnswerLog
from users.models import UserProfile
from trophies.utils import check_and_award_trophies

logger = logging.getLogger(__name__)


@login_required
def wrong_note_list(request):
    """오답노트 목록 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    wrong_answers = (
        WrongAnswer.objects.filter(user=user)
        .select_related("question__subject", "question__lesson")
        .order_by("question__subject__name", "question__lesson__unit_name")
    )
    note_dict = {}
    for wa in wrong_answers:
        subject = wa.question.subject
        lesson = wa.question.lesson
        lesson_id_key = lesson.id if lesson else 0
        lesson_unit_name_key = lesson.unit_name if lesson else "미지정 단원"
        key = (subject.id, subject.name, lesson_id_key, lesson_unit_name_key)
        if key not in note_dict:
            note_dict[key] = {
                "subject": subject,
                "lesson": lesson,
                "count": 0,
                "questions": [],
                "lesson_id_for_url": lesson_id_key,
            }
        note_dict[key]["count"] += 1
        note_dict[key]["questions"].append(wa.question)
    cards_list = []
    for data_dict in note_dict.values():
        cards_list.append(
            {
                "subject": data_dict["subject"],
                "lesson": data_dict["lesson"],
                "wrong_count": data_dict["count"],
                "questions_preview": data_dict["questions"][:5],
                "lesson_id_for_url": data_dict["lesson_id_for_url"],
            }
        )
    cards_list.sort(key=lambda x: (x["subject"].name, x["lesson"].unit_name if x["lesson"] else ""))
    context = {"user": user, "userprofile": user_profile, "cards": cards_list}
    return render(request, "quiz/wrong_note_list.html", context)


@login_required
def wrong_note_quiz(request, subject_id, lesson_id):
    """오답노트 문제를 풀이하는 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = None
    if int(lesson_id) != 0:
        lesson = get_object_or_404(Lesson, pk=lesson_id, subject=subject)

    q_filter = {"question__subject": subject}
    if lesson:
        q_filter["question__lesson"] = lesson
    else:
        q_filter["question__lesson__isnull"] = True
    wrong_question_ids = WrongAnswer.objects.filter(user=user, **q_filter).values_list("question_id", flat=True)
    all_available_wrong_questions = list(Question.objects.filter(pk__in=wrong_question_ids))

    session_key = f"used_questions_wrong_note_{subject_id}_{lesson_id}"

    if not all_available_wrong_questions:
        messages.success(
            request,
            f"{subject.name} ({lesson.unit_name if lesson else '미지정 단원'})의 모든 오답 문제를 해결하셨습니다!",
        )
        if session_key in request.session:
            del request.session[session_key]
        context = {
            "user": user,
            "userprofile": user_profile,
            "subject": subject,
            "lesson": lesson,
            "questions": [],
            "all_corrected": True,
            "question_type": "wrong_note",
        }
        return render(request, "quiz/wrong_answer.html", context)

    if request.method == "POST":
        answered_correctly_this_time_ids = []
        form_errors_post = []
        submission_warnings_post = []

        try:
            with transaction.atomic():
                for key, value_str in request.POST.items():
                    if key.startswith("q_") and key.split("_")[1].isdigit():
                        question_id = int(key.split("_")[1])
                        selected_answer_str = value_str.strip()

                        selected_answer = None
                        if not selected_answer_str or not selected_answer_str.isdigit():
                            logger.warning(
                                "오답노트: 문제 ID %s: 답변이 없거나 숫자 형식이 아님 (값: '%s').",
                                question_id,
                                selected_answer_str,
                            )
                            form_errors_post.append(
                                f"문제 ID {question_id}: 답변 형식이 올바르지 않거나 선택되지 않았습니다."
                            )
                            continue

                        selected_answer = int(selected_answer_str)
                        question = get_object_or_404(Question, pk=question_id)
                        is_correct = selected_answer == question.answer

                        if not UserAnswerLog.objects.filter(user=user, question=question).exists():
                            UserAnswerLog.objects.create(
                                user=user,
                                question=question,
                                user_answer=selected_answer,
                                is_correct=is_correct,
                            )
                        else:
                            logger.warning("오답노트: UserAnswerLog 이미 존재 (u=%s, q=%s). 새로 생성 안 함.", user.id, question_id)
                            submission_warnings_post.append(f"'{question.text[:20]}...' 문제는 이전에 푼 기록이 있습니다.")

                        if is_correct:
                            answered_correctly_this_time_ids.append(question_id)
                            WrongAnswer.objects.filter(user=user, question=question).delete()

                current_solved_in_session = request.session.get(session_key, [])
                current_solved_in_session.extend(answered_correctly_this_time_ids)
                request.session[session_key] = list(set(current_solved_in_session))

                if answered_correctly_this_time_ids:
                    messages.success(request, f"{len(answered_correctly_this_time_ids)}개의 오답을 해결했습니다!")

                check_and_award_trophies(user)

        except Exception as e:
            logger.error("[wrong_note_quiz POST] 답변 처리 중 오류: %s", e, exc_info=True)
            messages.error(request, "오답 처리 중 오류가 발생했습니다. 다시 시도해주세요.")
            return redirect("quiz:wrong_note_quiz", subject_id=subject_id, lesson_id=lesson_id)

        return redirect("quiz:wrong_note_quiz", subject_id=subject_id, lesson_id=lesson_id)

    solved_in_this_session_ids = request.session.get(session_key, [])
    remaining_questions_for_this_attempt = [q for q in all_available_wrong_questions if q.id not in solved_in_this_session_ids]

    if not remaining_questions_for_this_attempt and all_available_wrong_questions:
        if session_key in request.session:
            del request.session[session_key]
        messages.info(request, "이 오답 그룹의 문제들을 한 번씩 다 풀었습니다. 다시 시도합니다.")
        return redirect("quiz:wrong_note_quiz", subject_id=subject_id, lesson_id=lesson_id)

    selected_questions = []
    if remaining_questions_for_this_attempt:
        num_to_select = min(10, len(remaining_questions_for_this_attempt))
        selected_questions = random.sample(remaining_questions_for_this_attempt, num_to_select)

    logger.debug("[wrong_note_quiz GET] 선택된 문제 ID (%s): %s", session_key, [q.id for q in selected_questions])

    context = {
        "user": user,
        "userprofile": user_profile,
        "subject": subject,
        "lesson": lesson,
        "questions": selected_questions,
        "concept_description": lesson.concept if lesson else "오답 문제를 다시 풀어보세요.",
        "question_type": "wrong_note",
    }
    return render(request, "quiz/wrong_answer.html", context)


@login_required
def retry_question(request, question_id):
    """오답노트의 특정 문제를 재도전하는 페이지를 렌더링하고 답변을 처리합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    question = get_object_or_404(Question, pk=question_id)
    subject = question.subject
    lesson = question.lesson

    if request.method == "POST":
        selected_answer_str = request.POST.get("answer")
        if not selected_answer_str or not selected_answer_str.strip().isdigit():
            messages.error(request, "답변을 선택하거나 올바른 형식으로 입력해주세요.")
            return redirect("quiz:retry_question", question_id=question_id)
        selected_answer = int(selected_answer_str.strip())

        is_correct = selected_answer == question.answer

        try:
            with transaction.atomic():
                ual_exists = UserAnswerLog.objects.filter(user=user, question=question).exists()
                if not ual_exists:
                    UserAnswerLog.objects.create(user=user, question=question, user_answer=selected_answer, is_correct=is_correct)
                else:
                    logger.warning("UserAnswerLog 이미 존재 (재시도): u=%s, q=%s", user.id, question_id)

                if not is_correct:
                    if not WrongAnswer.objects.filter(user=user, question=question).exists():
                        WrongAnswer.objects.create(user=user, question=question)
                elif is_correct:
                    deleted_count, _ = WrongAnswer.objects.filter(user=user, question=question).delete()
                    if deleted_count > 0:
                        messages.success(request, "정답! 오답노트에서 삭제되었습니다.")
                    else:
                        messages.success(request, "정답입니다!")

                check_and_award_trophies(user)

        except Exception as e:
            logger.error("[retry_question POST] 답변 처리 중 오류: %s", e, exc_info=True)
            messages.error(request, "답변 처리 중 오류가 발생했습니다.")
            return redirect("quiz:retry_question", question_id=question_id)

        return redirect("quiz:wrong_note_list")

    context = {
        "user": user,
        "userprofile": user_profile,
        "subject": subject,
        "lesson": lesson,
        "questions": [question],
        "concept_description": lesson.concept if lesson else "문제를 다시 풀어보세요.",
        "is_retry_page": True,
        "question_type": "retry",
    }
    return render(request, "quiz/wrong_answer.html", context)