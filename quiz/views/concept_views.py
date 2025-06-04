import random
import logging

from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from ..models import Subject, Lesson, Question, UserAnswerLog
from users.models import UserProfile

logger = logging.getLogger(__name__)


@login_required
def concept_select(request):
    """문제 유형(개념/기출) 중 개념 문제 선택 후 과목 선택으로 연결되는 페이지입니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    context = {"user": user, "userprofile": user_profile}
    return render(request, "quiz/concept_select.html", context)


@login_required
def concept_subject_list(request):
    """개념문제 과목 목록 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    required_names = ["국어", "수학", "사회", "과학"]
    all_subjects = Subject.objects.all().order_by("name")
    required_subjects_with_delay = []
    elective_subjects_with_delay = []
    for i, subject_instance in enumerate(s for s in all_subjects if s.name in required_names):
        required_subjects_with_delay.append({"obj": subject_instance, "animation_delay_s": f"{i * 0.1:.1f}s"})
    elective_offset = len(required_subjects_with_delay)
    for i, subject_instance in enumerate(s for s in all_subjects if s.name not in required_names):
        elective_subjects_with_delay.append({"obj": subject_instance, "animation_delay_s": f"{(elective_offset + i) * 0.05 + 0.1:.2f}s"})
    context = {
        "user": user,
        "userprofile": user_profile,
        "required_subjects": required_subjects_with_delay,
        "elective_subjects": elective_subjects_with_delay,
    }
    logger.debug("Context for concept_subject_list: %s", context)
    return render(request, "quiz/concept_subject_list.html", context)


@login_required
def concept_lesson_list(request, subject_id):
    """개념문제 단원 목록 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    subject = get_object_or_404(Subject, pk=subject_id)
    lessons_qs = Lesson.objects.filter(subject=subject).order_by("unit_name")
    lessons_with_delay = []
    for i, lesson_obj in enumerate(lessons_qs):
        lessons_with_delay.append({"obj": lesson_obj, "animation_delay_s": f"{i * 0.08:.2f}s"})
    context = {
        "user": user,
        "userprofile": user_profile,
        "subject": subject,
        "lessons": lessons_with_delay,
    }
    return render(request, "quiz/concept_lesson_list.html", context)


@login_required
def concept_question_list(request, subject_id, lesson_id):
    """개념문제 문제풀이 페이지를 렌더링합니다."""
    user = request.user
    user_profile = UserProfile.objects.filter(user=user).first()
    subject = get_object_or_404(Subject, pk=subject_id)
    lesson = get_object_or_404(Lesson, pk=lesson_id, subject=subject)

    session_key = f"used_questions_concept_{subject_id}_{lesson_id}"
    all_questions_in_lesson = list(Question.objects.filter(subject=subject, lesson=lesson, question_type="concept"))
    used_questions_session = request.session.get(session_key, [])

    submitted_question_ids = set(
        UserAnswerLog.objects.filter(user=request.user, question__in=all_questions_in_lesson).values_list("question_id", flat=True)
    )

    available_questions = [
        q for q in all_questions_in_lesson if q.id not in used_questions_session and q.id not in submitted_question_ids
    ]
    logger.debug(
        "Session_key: %s, Used_session: %s, Submitted_DB: %s, Available: %d",
        session_key,
        used_questions_session,
        submitted_question_ids,
        len(available_questions),
    )

    if not available_questions and all_questions_in_lesson:
        logger.debug("All concept questions in lesson %s for subject %s done. Resetting session.", lesson_id, subject_id)
        if session_key in request.session:
            del request.session[session_key]
        used_questions_session = []
        available_questions = [q for q in all_questions_in_lesson if q.id not in submitted_question_ids]
        if not available_questions:
            messages.info(request, "이 단원의 모든 개념 문제를 이미 다 푸셨습니다!")

    selected_questions = []
    if available_questions:
        num_to_select = min(10, len(available_questions))
        selected_questions = random.sample(available_questions, num_to_select)

    newly_used_ids_for_session = [q.id for q in selected_questions]
    updated_used_questions_for_session = list(set(used_questions_session + newly_used_ids_for_session))
    request.session[session_key] = updated_used_questions_for_session

    logger.debug(
        "Selected concept questions IDs: %s, Updated session for %s: %s",
        newly_used_ids_for_session,
        session_key,
        updated_used_questions_for_session,
    )

    context = {
        "user": user,
        "userprofile": user_profile,
        "subject": subject,
        "lesson": lesson,
        "questions": selected_questions,
        "concept_description": lesson.concept,
        "question_type": "concept",
    }
    return render(request, "quiz/concept_question_list.html", context)