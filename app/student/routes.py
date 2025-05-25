from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from collections import defaultdict
from datetime import datetime, date
from pytz import timezone
from dateutil import parser

from . import student_bp
from app.extensions import db
from app.models import (
    Subject, StudyHistory, Concept, Step, Question,
    Mascot, UserTrophy, Trophy
)

# 대시보드
@student_bp.route("/dashboard")
@login_required
def dashboard():
    subjects = Subject.query.all()

    now = datetime.now(timezone("Asia/Seoul"))
    weekday_map = {
        'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
        'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
    }
    weekday_ko = weekday_map[now.strftime('%A')]

    trophy_count = current_user.user_trophies.count()
    total_trophies = Trophy.query.count()
    trophy_percent = int((trophy_count / total_trophies) * 100) if total_trophies else 0

    today = now.date()
    today_total = StudyHistory.query.filter_by(
        user_id=current_user.id
    ).filter(StudyHistory.timestamp >= datetime.combine(today, datetime.min.time())).count()

    last_activity = StudyHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(StudyHistory.timestamp.desc()).first()

    return render_template(
        "student/dashboard.html",
        subjects=subjects,
        user=current_user,
        now=now,
        weekday_ko=weekday_ko,
        trophy_count=trophy_count,
        trophy_percent=trophy_percent,
        today_total=today_total,
        last_activity=last_activity
    )

# 마이페이지
@student_bp.route("/my-page")
@login_required
def my_page():
    mascots = Mascot.query.all()
    trophies = UserTrophy.query.filter_by(user_id=current_user.id).all()
    return render_template("student/my_page.html", user=current_user, mascots=mascots, trophies=trophies)

# 오답노트
@student_bp.route("/my-mistake-notebook")
@login_required
def my_mistake_notebook():
    mistakes = StudyHistory.query.filter_by(
        user_id=current_user.id,
        is_correct=False,
        mistake_status='active'
    ).order_by(StudyHistory.timestamp.desc()).all()

    grouped = defaultdict(list)
    for m in mistakes:
        concept = m.question.concept
        grouped[concept.id].append(m.question)

    grouped_mistakes = []
    for concept_id, questions in grouped.items():
        concept = Concept.query.get(concept_id)
        subject = concept.subject
        grouped_mistakes.append({
            "concept_id": concept.id,
            "concept_name": concept.name,
            "subject_name": subject.name,
            "question_count": len(questions),
            "questions_sample": questions[:3]
        })

    return render_template("student/mistake_notebook.html", grouped_mistakes=grouped_mistakes, user=current_user)

# 통계
@student_bp.route("/my-stats")
@login_required
def my_stats():
    total_histories = StudyHistory.query.filter_by(user_id=current_user.id).all()
    total = len(total_histories)
    correct = sum(1 for h in total_histories if h.is_correct)
    accuracy = round((correct / total) * 100, 1) if total else None

    concepts_attempted = len(set(h.question.concept_id for h in total_histories))
    days_active = len(set(h.timestamp.date() for h in total_histories))

    ai_generated = sum(1 for h in total_histories if h.question.source_type == 'ai_generated')
    concept_learning = sum(1 for h in total_histories if h.question.source_type == 'manual_admin')
    past_exam = sum(1 for h in total_histories if h.question.source_type == 'past_exam')

    return render_template(
        "student/my_stats.html",
        user=current_user,
        total=total,
        correct=correct,
        accuracy=accuracy,
        concepts_attempted=concepts_attempted,
        days_active=days_active,
        ai_generated=ai_generated,
        concept_learning=concept_learning,
        past_exam=past_exam
    )

# 학습 캘린더
@student_bp.route("/my-calendar")
@login_required
def my_calendar():
    today = date.today()
    today_histories = StudyHistory.query.filter(
        StudyHistory.user_id == current_user.id,
        StudyHistory.timestamp >= datetime.combine(today, datetime.min.time()),
        StudyHistory.timestamp <= datetime.combine(today, datetime.max.time())
    ).all()

    today_total = len(today_histories)
    today_correct = sum(1 for h in today_histories if h.is_correct)
    today_accuracy = round((today_correct / today_total) * 100, 1) if today_total else None

    return render_template("student/my_calendar.html", user=current_user, today_total=today_total, today_accuracy=today_accuracy)

# JSON 캘린더 이벤트
@student_bp.route("/get-calendar-events")
@login_required
def get_calendar_events():
    start = request.args.get("start")
    end = request.args.get("end")

    try:
        start_date = parser.parse(start).date()
        end_date = parser.parse(end).date()
    except Exception:
        return jsonify([])

    histories = StudyHistory.query.filter_by(user_id=current_user.id).all()
    date_event_map = defaultdict(int)
    for h in histories:
        d = h.timestamp.date()
        if start_date <= d <= end_date:
            date_event_map[d.isoformat()] += 1

    events = [
        {"title": f"문제풀이 {count}회", "start": day, "color": "#0d6efd"}
        for day, count in date_event_map.items()
    ]

    return jsonify(events)

# 테마 변경
@student_bp.route("/set-theme/<theme_name>")
@login_required
def set_theme(theme_name):
    session['user_theme'] = theme_name
    return redirect(url_for("student.my_page"))

# 마스코트 설정
@student_bp.route("/set-mascot", methods=["POST"])
@login_required
def set_mascot():
    mascot_id = request.form.get("mascot_id")
    mascot = Mascot.query.get(mascot_id)
    if mascot:
        current_user.selected_mascot_id = mascot.id
        db.session.commit()
        flash("마스코트가 변경되었습니다!", "success")
    else:
        flash("잘못된 마스코트입니다.", "danger")
    return redirect(url_for("student.my_page"))

# 포인트 사용
@student_bp.route("/use-points", methods=["POST"])
@login_required
def use_points():
    used = int(request.form.get("used_points", 0))
    if used > 0 and used <= current_user.total_earned_points:
        current_user.total_earned_points -= used
        db.session.commit()
        flash(f"{used}포인트를 사용했습니다.", "success")
    else:
        flash("잘못된 포인트 사용 요청입니다.", "danger")
    return redirect(url_for("student.my_page"))

# 과목 목록
@student_bp.route("/subjects")
@login_required
def subject_list():
    subjects = Subject.query.all()
    return render_template("student/subjects.html", subjects=subjects, user=current_user)

# 개념 목록
@student_bp.route("/subjects/<int:subject_id>/concepts")
@login_required
def view_subject_concepts(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    concepts = Concept.query.filter_by(subject_id=subject_id).order_by(Concept.id).all()
    return render_template("student/concepts.html", subject=subject, concepts=concepts, user=current_user)

# 개념 단계
@student_bp.route("/concepts/<int:concept_id>/steps")
@login_required
def view_concept_steps(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    steps = Step.query.filter_by(concept_id=concept.id).order_by(Step.step_order).all()
    return render_template("student/steps.html", concept=concept, steps=steps, user=current_user)

# 문제 풀이
@student_bp.route("/concepts/<int:concept_id>/quiz")
@login_required
def quiz_start(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    questions = Question.query.filter_by(concept_id=concept_id).all()
    return render_template("student/quiz.html", concept=concept, questions=questions, user=current_user)

# 문제 제출
@student_bp.route("/concepts/<int:concept_id>/quiz/submit", methods=["POST"])
@login_required
def quiz_submit(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    questions = Question.query.filter_by(concept_id=concept_id).all()

    results = []
    total_correct = 0
    submitted_count = 0

    for q in questions:
        user_answer = request.form.get(f"q{q.id}")
        if user_answer:
            submitted_count += 1
            is_correct = (user_answer == q.answer)
            if is_correct:
                total_correct += 1
                current_user.total_earned_points += 10

            existing = StudyHistory.query.filter_by(
                user_id=current_user.id, question_id=q.id
            ).first()

            if existing:
                existing.submitted_answer = user_answer
                existing.is_correct = is_correct
                existing.mistake_status = "active" if not is_correct else "cleared"
            else:
                history = StudyHistory(
                    user_id=current_user.id,
                    question_id=q.id,
                    submitted_answer=user_answer,
                    is_correct=is_correct,
                    mistake_status="active" if not is_correct else "cleared"
                )
                db.session.add(history)

            results.append({
                "question": q,
                "user_answer": user_answer,
                "is_correct": is_correct
            })

    db.session.commit()

    return render_template(
        "student/quiz_result.html",
        concept=concept,
        results=results,
        total=submitted_count,
        correct=total_correct,
        user=current_user
    )

# 오답 복습 처리
@student_bp.route("/mistake/<int:question_id>/clear", methods=["POST"])
@login_required
def clear_mistake(question_id):
    history = StudyHistory.query.filter_by(
        user_id=current_user.id,
        question_id=question_id,
        mistake_status='active'
    ).first()
    if history:
        history.mistake_status = 'cleared'
        db.session.commit()
        flash("복습 완료로 처리되었습니다!", "success")
    return redirect(url_for("student.my_mistake_notebook"))

# 오답만 다시 풀기
@student_bp.route("/concepts/<int:concept_id>/mistake-quiz")
@login_required
def reattempt_mistakes_by_concept(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    mistake_histories = (
        StudyHistory.query
        .filter_by(user_id=current_user.id, is_correct=False, mistake_status='active')
        .join(Question)
        .filter(Question.concept_id == concept_id)
        .all()
    )
    questions = [m.question for m in mistake_histories]
    return render_template(
        "student/quiz.html",
        concept=concept,
        questions=questions,
        user=current_user,
        reattempt=True
    )
