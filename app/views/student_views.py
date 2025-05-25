# app/views/student_views.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, case, distinct, and_
import re
from textwrap import dedent
import google.generativeai as genai

from app import db
from app.models import User, Subject, Concept, Step, Question, Trophy, UserTrophy, StudyHistory, DailyActivity

bp = Blueprint('student', __name__)

AVAILABLE_MASCOTS = ['lion.png', 'robot.png', 'bunny.png', 'cat.png', 'dog.png']

# --- Helper Functions ---
def log_daily_activity(user_id):
    today = date.today()
    activity = DailyActivity.query.filter_by(user_id=user_id, date=today).first()
    if activity:
        activity.actions_count += 1
    else:
        activity = DailyActivity(user_id=user_id, date=today, actions_count=1)
        db.session.add(activity)

def award_trophy(user, trophy_id, commit_now=True):
    if not user: return False
    if trophy_id == 1 and UserTrophy.query.filter_by(user_id=user.id, trophy_id=1).first():
        return False
    already_has_trophy = UserTrophy.query.filter_by(user_id=user.id, trophy_id=trophy_id).first()
    if not already_has_trophy:
        trophy_to_award = Trophy.query.get(trophy_id)
        if trophy_to_award:
            current_user_trophy_count_before_this = UserTrophy.query.filter_by(user_id=user.id).count()
            new_user_trophy = UserTrophy(user_id=user.id, trophy_id=trophy_id)
            db.session.add(new_user_trophy)
            user.total_earned_points += trophy_to_award.points
            flash(f"🎉 축하합니다! '{trophy_to_award.name}' 트로피 ({trophy_to_award.points}P)를 획득했습니다! 🎉", "success")
            if current_user_trophy_count_before_this == 0 and trophy_id != 1:
                FIRST_EVER_TROPHY_ID = 1
                first_trophy_definition = Trophy.query.get(FIRST_EVER_TROPHY_ID)
                if first_trophy_definition and not UserTrophy.query.filter_by(user_id=user.id, trophy_id=FIRST_EVER_TROPHY_ID).first():
                    first_ever_user_trophy_obj = UserTrophy(user_id=user.id, trophy_id=FIRST_EVER_TROPHY_ID)
                    db.session.add(first_ever_user_trophy_obj)
                    user.total_earned_points += first_trophy_definition.points
                    flash(f"✨ 그리고... '{first_trophy_definition.name}' 트로피 ({first_trophy_definition.points}P)도 획득했습니다! ✨", "success")
            if commit_now:
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Error during awarding trophy (id: {trophy_id}) commit: {e}")
                    flash("트로피 수여 중 오류가 발생했습니다.", "danger")
                    return False
            return True
    return False

def check_and_award_login_trophies(user):
    if user.consecutive_login_days >= 30: award_trophy(user, 13, commit_now=False)
    elif user.consecutive_login_days >= 15: award_trophy(user, 12, commit_now=False)
    elif user.consecutive_login_days >= 7: award_trophy(user, 11, commit_now=False)
    elif user.consecutive_login_days >= 3: award_trophy(user, 10, commit_now=False)

def check_and_award_activity_time_trophies(user):
    now_time_hour_utc = datetime.utcnow().hour
    now_hour_kst = (now_time_hour_utc + 9) % 24
    if 0 <= now_hour_kst < 5 or 22 <= now_hour_kst < 24:
        award_trophy(user, 17, commit_now=False)
    today_weekday = date.today().weekday()
    if today_weekday == 5 or today_weekday == 6:
        award_trophy(user, 14, commit_now=False)

def check_and_award_effort_trophies(user):
    total_questions_solved = StudyHistory.query.filter_by(user_id=user.id).count()
    if total_questions_solved >= 100: award_trophy(user, 16, commit_now=False)
    elif total_questions_solved >= 50: award_trophy(user, 15, commit_now=False)

def check_and_award_concept_mastery_trophies(user):
    passed_concepts_query = db.session.query(
        Question.concept_id,
        func.count(StudyHistory.id).label('attempts'),
        func.sum(case((StudyHistory.is_correct == True, 1), else_=0)).label('corrects')
    ).join(StudyHistory, Question.id == StudyHistory.question_id)\
    .filter(StudyHistory.user_id == user.id)\
    .group_by(Question.concept_id).all()
    passed_concept_ids = set()
    for concept_result in passed_concepts_query:
        if concept_result.attempts > 0 and (concept_result.corrects / concept_result.attempts) >= 0.6:
            passed_concept_ids.add(concept_result.concept_id)
    num_passed_concepts = len(passed_concept_ids)
    if num_passed_concepts >= 20: award_trophy(user, 32, commit_now=False)
    elif num_passed_concepts >= 10: award_trophy(user, 31, commit_now=False)
    elif num_passed_concepts >= 3: award_trophy(user, 30, commit_now=False)
    perfect_score_concepts_count = 0
    all_concepts_attempted_by_user = db.session.query(distinct(Question.concept_id))\
        .join(StudyHistory, Question.id == StudyHistory.question_id)\
        .filter(StudyHistory.user_id == user.id).all()
    for concept_tuple in all_concepts_attempted_by_user:
        concept_id = concept_tuple[0]
        total_questions_in_concept = Question.query.filter_by(concept_id=concept_id).count()
        if total_questions_in_concept == 0: continue
        correct_answers_for_concept = db.session.query(func.count(distinct(StudyHistory.question_id)))\
            .join(Question, StudyHistory.question_id == Question.id)\
            .filter(StudyHistory.user_id == user.id, Question.concept_id == concept_id, StudyHistory.is_correct == True)\
            .scalar()
        if correct_answers_for_concept == total_questions_in_concept:
            perfect_score_concepts_count += 1
    if perfect_score_concepts_count >= 3: award_trophy(user, 35, commit_now=False)

def check_and_award_collection_trophies(user):
    num_user_trophies = UserTrophy.query.filter_by(user_id=user.id).count()
    if num_user_trophies >= 20: award_trophy(user, 42, commit_now=False)
    elif num_user_trophies >= 10: award_trophy(user, 41, commit_now=False)
    elif num_user_trophies >= 5: award_trophy(user, 40, commit_now=False)

def check_and_award_points_trophies(user):
    if user.total_earned_points >= 10000:
        award_trophy(user, 45, commit_now=False)

def check_all_trophies(user):
    if not user: return
    check_and_award_login_trophies(user)
    check_and_award_activity_time_trophies(user)
    check_and_award_effort_trophies(user)
    check_and_award_concept_mastery_trophies(user)
    check_and_award_collection_trophies(user)
    check_and_award_points_trophies(user)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error during check_all_trophies commit: {e}")
        flash("트로피 상태 업데이트 중 오류가 발생했습니다.", "danger")

# --- Student Routes ---
@bp.route('/')
@login_required
def index():
    return redirect(url_for('student.dashboard'))

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('dashboard.html', subjects=subjects)

@bp.route('/subject/<int:subject_id>/concepts')
@login_required
def view_subject_concepts(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    return render_template('student/concepts_list.html', subject=subject)

@bp.route('/concept/<int:concept_id>/learn/step/<int:step_order>')
@login_required
def learn_concept_step(concept_id, step_order):
    concept = Concept.query.get_or_404(concept_id)
    current_step_obj = Step.query.filter_by(concept_id=concept.id, step_order=step_order).first_or_404()
    total_steps = Step.query.filter_by(concept_id=concept.id).count()
    if step_order == total_steps and total_steps > 0:
        log_daily_activity(current_user.id)
        award_trophy(current_user, 2, commit_now=False)
        check_all_trophies(current_user)
    return render_template('student/learn_step.html',
                           concept=concept,
                           current_step=current_step_obj,
                           current_step_order=step_order,
                           total_steps=total_steps)

@bp.route('/concept/<int:concept_id>/test', methods=['GET', 'POST'])
@login_required
def start_concept_test(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    if request.method == 'POST':
        num_correct = 0
        questions_in_test = list(concept.questions) # 현재는 해당 컨셉의 모든 문제를 대상으로 함
        for question in questions_in_test:
            submitted_answer = request.form.get(f'answer_{question.id}')
            is_correct = False
            if submitted_answer is not None: # 답을 제출한 경우에만
                if question.question_type == 'multiple_choice':
                    is_correct = (submitted_answer == str(question.answer))
                else: # 주관식 등 기타 유형
                    is_correct = (submitted_answer.strip().lower() == str(question.answer).strip().lower())
                
                history_entry = StudyHistory(
                    user_id=current_user.id,
                    question_id=question.id,
                    submitted_answer=submitted_answer,
                    is_correct=is_correct,
                    mistake_status='active' if not is_correct else 'n/a' # 오답이면 'active', 정답이면 'n/a'
                )
                db.session.add(history_entry)
            
            if is_correct:
                num_correct += 1
        
        log_daily_activity(current_user.id)
        total_questions_in_test_count = len(questions_in_test)
        
        if total_questions_in_test_count > 0:
            if num_correct == total_questions_in_test_count: # 만점
                award_trophy(current_user, 4, commit_now=False) # "만점의 별!"
            if (num_correct / total_questions_in_test_count) >= 0.6: # 60점 이상 통과
                award_trophy(current_user, 3, commit_now=False) # "첫 테스트 통과!"
        
        check_all_trophies(current_user) # 트로피 관련 변경사항 일괄 커밋

        flash(f"테스트 완료! 총 {total_questions_in_test_count}문제 중 {num_correct}문제를 맞혔습니다.", "info")
        return redirect(url_for('student.view_test_results', concept_id=concept.id))

    # GET 요청 시: 테스트 페이지 보여주기
    questions_to_display = list(concept.questions)
    if not questions_to_display:
        flash("이 개념에 대한 문제가 아직 준비되지 않았습니다.", "warning")
        return redirect(url_for('student.view_subject_concepts', subject_id=concept.subject_id))
    
    return render_template('student/take_test.html', concept=concept, questions=questions_to_display)


@bp.route('/concept/<int:concept_id>/results')
@login_required
def view_test_results(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    results_data = []
    num_correct_from_history = 0
    all_questions_in_concept = Question.query.filter_by(concept_id=concept.id).order_by(Question.id).all()
    for question in all_questions_in_concept:
        latest_history = StudyHistory.query.filter_by(
            user_id=current_user.id,
            question_id=question.id
        ).order_by(StudyHistory.timestamp.desc()).first()
        submitted_ans = '선택 안 함'
        is_cor = False
        if latest_history:
            submitted_ans = latest_history.submitted_answer if latest_history.submitted_answer is not None else '선택 안 함'
            is_cor = latest_history.is_correct
        results_data.append({
            'question_id': question.id,
            'question_content': question.content,
            'question_obj': question, 
            'submitted_answer': submitted_ans, 
            'correct_answer_num': question.answer, 
            'is_correct': is_cor
        })
        if is_cor:
            num_correct_from_history += 1
    score_text = f"{num_correct_from_history} / {len(all_questions_in_concept) if all_questions_in_concept else 0}"
    return render_template('student/test_results.html',
                           concept=concept,
                           results=results_data,
                           score=score_text)

@bp.route('/generate-similar-question/<int:original_question_id>', methods=['GET', 'POST'])
@login_required
def generate_similar_question_page(original_question_id):
    original_question = Question.query.get_or_404(original_question_id)
    if request.method == 'GET':
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            prompt = dedent(f"""
            당신은 대한민국 초등학생을 위한 창의적인 '{original_question.concept.subject.name}' 과목 문제 출제 전문가입니다.
            다음은 '{original_question.concept.name}' 개념에 대한 원본 문제입니다.
            원본 문제 내용: "{original_question.content}"
            (참고-원본 문제 보기1: {original_question.option1}, 보기2: {original_question.option2}, 보기3: {original_question.option3}, 보기4: {original_question.option4}, 원본 정답 번호: {original_question.answer})
            이 문제의 핵심 학습 원리와 전반적인 난이도는 유지하되, 아래 조건 중 **최소 두 가지 이상**을 만족하도록 완전히 새로운 **객관식 유사 문제**를 한국어로 1개 만들어주세요.
            새로운 문제는 4개의 보기를 가져야 하며, 정답은 그 중 하나여야 합니다.
            1. 문제에 사용된 모든 주요 숫자나 핵심 용어들을 원래 문제와 다른 것으로 변경해주세요. (예: 수학이면 숫자, 국어면 등장인물이나 배경)
            2. 문제의 배경 이야기, 등장인물, 또는 구체적인 상황 설정을 원래 문제와 다르게 흥미롭게 각색해주세요.
            3. 질문하는 방식을 원래 문제와 약간 다르게 변형하여 표현해주세요.
            4. 절대로 원래 문제와 내용, 보기, 정답이 완전히 동일해서는 안 됩니다.
            새로운 문제와 보기, 그리고 정답 번호를 다음 지정된 형식으로만 제공해야 합니다:
            [NEW_QUESTION]
            Q: <여기에 새로운 문제 내용을 작성해주세요.>
            O1: <새로운 문제의 1번 보기>
            O2: <새로운 문제의 2번 보기>
            O3: <새로운 문제의 3번 보기>
            O4: <새로운 문제의 4번 보기>
            A: <새로운 문제의 정답 보기 번호 (1, 2, 3, 4 중 하나)>
            """)
            response = model.generate_content(prompt)
            content = response.text
            new_q_text = "AI가 유사 문제를 생성하지 못했습니다. 잠시 후 다시 시도해주세요."
            new_options = {"O1": "N/A", "O2": "N/A", "O3": "N/A", "O4": "N/A"}
            new_a_text = "N/A"
            if "[NEW_QUESTION]" in content:
                try:
                    main_part = content.split("[NEW_QUESTION]")[1].strip()
                    q_match = re.search(r"Q:\s*(.*?)(?=\n\s*O1:)", main_part, re.DOTALL)
                    o1_match = re.search(r"O1:\s*(.*?)(?=\n\s*O2:)", main_part, re.DOTALL)
                    o2_match = re.search(r"O2:\s*(.*?)(?=\n\s*O3:)", main_part, re.DOTALL)
                    o3_match = re.search(r"O3:\s*(.*?)(?=\n\s*O4:)", main_part, re.DOTALL)
                    o4_match = re.search(r"O4:\s*(.*?)(?=\n\s*A:)", main_part, re.DOTALL)
                    a_match = re.search(r"A:\s*([1-4])", main_part)
                    if q_match and o1_match and o2_match and o3_match and o4_match and a_match:
                        new_q_text = q_match.group(1).strip()
                        new_options['O1'] = o1_match.group(1).strip()
                        new_options['O2'] = o2_match.group(1).strip()
                        new_options['O3'] = o3_match.group(1).strip()
                        new_options['O4'] = o4_match.group(1).strip()
                        new_a_text = a_match.group(1).strip()
                        session['similar_question_text'] = new_q_text
                        session['similar_question_options'] = new_options
                        session['similar_Youtube_num'] = new_a_text 
                        session['original_question_id_for_similar'] = original_question.id
                    else:
                        flash("AI 응답에서 문제 형식을 제대로 파싱할 수 없습니다.", "warning")
                        return redirect(url_for('student.view_test_results', concept_id=original_question.concept_id))
                except Exception as e_parse:
                    print(f"AI 응답 파싱 오류: {e_parse} --- 내용: {content}")
                    flash("AI 응답 형식이 올바르지 않아 문제를 가져올 수 없습니다.", "warning")
                    return redirect(url_for('student.view_test_results', concept_id=original_question.concept_id))
            else:
                flash("AI가 유효한 형식으로 문제를 생성하지 못했습니다.", "warning")
                return redirect(url_for('student.view_test_results', concept_id=original_question.concept_id))
            return render_template('student/similar_question_display.html',
                                   original_question=original_question,
                                   new_question_text=new_q_text,
                                   new_question_options=new_options,
                                   feedback_result=None)
        except Exception as e:
            flash(f"유사 문제 생성 중 AI 오류: {e}", "danger")
            return redirect(url_for('student.view_test_results', concept_id=original_question.concept_id))

    if request.method == 'POST':
        submitted_answer_num = request.form.get('submitted_answer')
        correct_answer_num = session.pop('similar_Youtube_num', None)
        question_text = session.pop('similar_question_text', 'N/A')
        question_options = session.pop('similar_question_options', {"O1": "N/A", "O2": "N/A", "O3": "N/A", "O4": "N/A"})
        original_q_id = session.pop('original_question_id_for_similar', original_question.id)
        current_original_question = Question.query.get(original_q_id if original_q_id else original_question_id)
        if correct_answer_num is None:
            flash("오류: 채점 정보를 찾을 수 없습니다. 다시 시도해주세요.", "danger")
            if current_original_question:
                return redirect(url_for('student.view_test_results', concept_id=current_original_question.concept_id))
            else:
                return redirect(url_for('student.dashboard'))
        is_correct = (submitted_answer_num is not None and submitted_answer_num == correct_answer_num)
        feedback = {'submitted_choice_num': submitted_answer_num, 'correct_choice_num': correct_answer_num, 'is_correct': is_correct}
        if current_original_question:
            log_daily_activity(current_user.id)
            if is_correct:
                original_mistakes = StudyHistory.query.filter_by(
                    user_id=current_user.id,
                    question_id=current_original_question.id,
                    is_correct=False,
                    mistake_status='active'
                ).all()
                for mistake_history_entry in original_mistakes: # 변수명 변경
                    mistake_history_entry.mistake_status = 'mastered_via_similar'
                award_trophy(current_user, 20, commit_now=False)
                award_trophy(current_user, 23, commit_now=False)
            check_all_trophies(current_user)
        if is_correct:
            flash("정답입니다! 잘하셨어요. 👍", "success")
        else:
            flash("아쉽지만 틀렸어요. 정답을 확인해보세요. 😟", "warning")
        return render_template('student/similar_question_display.html',
                               original_question=current_original_question,
                               new_question_text=question_text,
                               new_question_options=question_options,
                               feedback_result=feedback)
    return redirect(url_for('student.view_test_results', concept_id=original_question.concept_id))

@bp.route('/my-page')
@login_required
def my_page():
    earned_user_trophies = UserTrophy.query.filter_by(user_id=current_user.id).order_by(UserTrophy.earned_at.desc()).all()
    return render_template('student/my_page.html', user=current_user, earned_user_trophies=earned_user_trophies, available_mascots=AVAILABLE_MASCOTS)

@bp.route('/my-stats')
@login_required
def my_stats():
    stats_query = db.session.query(
        Concept.id.label('concept_id'),
        Concept.name.label('concept_name'),
        Subject.name.label('subject_name'),
        func.count(StudyHistory.id).label('total_attempted'),
        func.sum(case((StudyHistory.is_correct == True, 1), else_=0)).label('total_correct')
    ).join(Question, Concept.id == Question.concept_id)\
     .join(StudyHistory, Question.id == StudyHistory.question_id)\
     .join(Subject, Concept.subject_id == Subject.id)\
     .filter(StudyHistory.user_id == current_user.id)\
     .group_by(Concept.id, Concept.name, Subject.name)\
     .order_by( (func.sum(case((StudyHistory.is_correct == True, 1), else_=0)) * 1.0 / func.count(StudyHistory.id) ).asc() )\
     .all()
    
    concept_stats = []
    for row in stats_query:
        accuracy = (row.total_correct / row.total_attempted * 100) if row.total_attempted > 0 else 0
        concept_stats.append({
            'concept_id': row.concept_id,
            'concept_name': row.concept_name,
            'subject_name': row.subject_name,
            'total_attempted': row.total_attempted,
            'total_correct': row.total_correct,
            'accuracy': round(accuracy, 1)
        })
    return render_template('student/my_stats.html', concept_stats=concept_stats)

@bp.route('/use-points', methods=['POST'])
@login_required
def use_points():
    try:
        points_to_use = int(request.form.get('points_to_use', 0))
    except ValueError:
        flash('사용할 포인트를 숫자로 정확히 입력해주세요.', 'danger')
        return redirect(url_for('student.my_page'))
    if points_to_use <= 0:
        flash('사용할 포인트는 0보다 커야 합니다.', 'danger')
        return redirect(url_for('student.my_page'))
    user = User.query.get(current_user.id)
    if not user:
        flash('사용자 정보를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('auth.login'))
    if user.total_earned_points >= points_to_use:
        user.total_earned_points -= points_to_use
        check_all_trophies(user)
        flash(f'{points_to_use} 포인트를 사용했습니다! 남은 포인트: {user.total_earned_points}P', 'success')
    else:
        flash(f'포인트가 부족합니다. (현재 보유: {user.total_earned_points}P, 사용 요청: {points_to_use}P)', 'danger')
    return redirect(url_for('student.my_page'))

@bp.route('/my-calendar')
@login_required
def my_calendar():
    return render_template('student/my_calendar.html')

@bp.route('/get-calendar-events')
@login_required
def get_calendar_events():
    activities = DailyActivity.query.filter_by(user_id=current_user.id).all()
    events = []
    for activity in activities:
        events.append({
            'title': f'{activity.actions_count}개 활동',
            'start': activity.date.isoformat(),
            'allDay': True
        })
    return jsonify(events)

@bp.route('/set-theme/<theme_name>')
@login_required
def set_theme(theme_name):
    user = User.query.get(current_user.id)
    if not user:
        flash("사용자 정보를 찾을 수 없습니다.", "danger")
        return redirect(url_for('auth.login'))
    valid_themes = ['theme-light-blue', 'theme-fresh-green', 'theme-warm-orange']
    if theme_name in valid_themes:
        user.selected_theme = theme_name
        session['user_theme'] = theme_name
        db.session.commit()
        readable_theme_name = theme_name.replace('theme-', '').replace('-', ' ').title()
        flash(f"테마가 '{readable_theme_name}' (으)로 변경되었습니다.", "success")
    else:
        flash("유효하지 않은 테마입니다.", "danger")
    return redirect(request.referrer or url_for('student.my_page'))

@bp.route('/set-mascot', methods=['POST'])
@login_required
def set_mascot():
    selected_mascot = request.form.get('mascot_filename')
    user = User.query.get(current_user.id)
    if not user:
        flash('사용자 정보를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('auth.login'))
    if selected_mascot in AVAILABLE_MASCOTS:
        user.selected_mascot_filename = selected_mascot
        session['user_mascot'] = selected_mascot
        db.session.commit()
        flash('마스코트가 변경되었습니다!', 'success')
    else:
        flash('유효하지 않은 마스코트입니다.', 'danger')
    return redirect(url_for('student.my_page'))

# --- ★★★ 오답 노트 관련 신규/수정된 함수 ★★★ ---
@bp.route('/my-mistake-notebook')
@login_required
def mistake_notebook():
    """오답 노트를 개념별로 그룹화하여 보여줍니다."""
    active_mistakes_query = StudyHistory.query.join(Question).join(Concept).join(Subject).filter(
        StudyHistory.user_id == current_user.id,
        StudyHistory.is_correct == False,
        StudyHistory.mistake_status == 'active'
    ).order_by(Subject.name, Concept.name, StudyHistory.timestamp.desc()).all()
    
    mistakes_by_concept = {}
    processed_question_ids_for_concept = {}

    for sh in active_mistakes_query:
        concept_key = (sh.question.concept.id, sh.question.concept.name, sh.question.concept.subject.name)
        
        if concept_key not in mistakes_by_concept:
            mistakes_by_concept[concept_key] = []
            processed_question_ids_for_concept[concept_key] = set()

        if sh.question_id not in processed_question_ids_for_concept[concept_key]:
            mistakes_by_concept[concept_key].append(sh.question)
            processed_question_ids_for_concept[concept_key].add(sh.question_id)
            
    grouped_mistakes = []
    for (concept_id, concept_name, subject_name), questions in mistakes_by_concept.items():
        if questions:
            grouped_mistakes.append({
                'concept_id': concept_id,
                'concept_name': concept_name,
                'subject_name': subject_name,
                'question_count': len(questions),
                'questions_sample': questions[:3]
            })
    
    grouped_mistakes.sort(key=lambda x: (x['subject_name'], x['concept_name']))

    return render_template('student/mistake_notebook.html', grouped_mistakes=grouped_mistakes)

@bp.route('/concept/<int:concept_id>/reattempt-mistakes', methods=['GET', 'POST'])
@login_required
def reattempt_mistakes_by_concept(concept_id):
    """특정 개념에서 틀렸던 문제들을 모아서 다시 풀어보게 합니다."""
    concept = Concept.query.get_or_404(concept_id)

    if request.method == 'POST':
        # --- ★★★ POST 요청 처리 로직 추가 ★★★ ---
        num_correct = 0
        # 템플릿에서 전달된 문제 ID들을 가져와 해당 Question 객체들을 조회 (순서 유지를 위해)
        # form에서 'question_id_order' 같은 hidden input으로 문제 ID 순서를 받는 것이 더 정확할 수 있습니다.
        # 여기서는 GET 요청 시 전달했던 questions 리스트를 다시 조회합니다. (단순화)
        
        # GET 요청 시 사용했던 쿼리를 다시 사용하여 reattempt 대상 문제들을 가져옴
        active_mistake_questions_query = db.session.query(Question)\
            .join(StudyHistory)\
            .filter(
                StudyHistory.user_id == current_user.id,
                StudyHistory.is_correct == False,
                StudyHistory.mistake_status == 'active',
                Question.concept_id == concept_id
            )\
            .distinct(Question.id)\
            .order_by(Question.id)
        questions_to_reattempt = active_mistake_questions_query.all()

        for question in questions_to_reattempt:
            submitted_answer = request.form.get(f'answer_{question.id}')
            is_correct_reattempt = False
            if submitted_answer is not None:
                if question.question_type == 'multiple_choice':
                    is_correct_reattempt = (submitted_answer == str(question.answer))
                else:
                    is_correct_reattempt = (submitted_answer.strip().lower() == str(question.answer).strip().lower())
                
                # 재시도에 대한 새로운 StudyHistory 기록 생성
                new_history_entry = StudyHistory(
                    user_id=current_user.id,
                    question_id=question.id,
                    submitted_answer=submitted_answer,
                    is_correct=is_correct_reattempt,
                    mistake_status='n/a' # 재시도 기록은 'active' 오답이 아님
                )
                db.session.add(new_history_entry)

                if is_correct_reattempt:
                    num_correct += 1
                    # 이전에 'active' 상태였던 이 문제에 대한 모든 오답 기록을 'mastered'로 변경
                    StudyHistory.query.filter_by(
                        user_id=current_user.id,
                        question_id=question.id,
                        is_correct=False, # 사실 is_correct=False 조건은 없어도 될 수 있음 (mistake_status로 충분)
                        mistake_status='active'
                    ).update({'mistake_status': 'mastered_after_reattempt'})
            
        log_daily_activity(current_user.id) # 전체 재시도 세트에 대한 활동 기록
        
        # 트로피 조건 확인 (예: 약점 극복 관련 트로피 등)
        # award_trophy(current_user, TROPHY_ID_FOR_MASTERING_MISTAKES, commit_now=False)
        check_all_trophies(current_user) # DB 커밋 포함

        flash(f"'{concept.name}' 개념 오답 재시도 완료! 총 {len(questions_to_reattempt)}문제 중 {num_correct}문제를 맞혔습니다.", "success")
        return redirect(url_for('student.mistake_notebook'))
        # --- ★★★ POST 요청 처리 로직 끝 ★★★ ---

    # GET 요청
    active_mistake_questions_query = db.session.query(Question)\
        .join(StudyHistory)\
        .filter(
            StudyHistory.user_id == current_user.id,
            StudyHistory.is_correct == False,
            StudyHistory.mistake_status == 'active',
            Question.concept_id == concept_id
        )\
        .distinct(Question.id)\
        .order_by(Question.id)
    
    questions_to_reattempt = active_mistake_questions_query.all()

    if not questions_to_reattempt:
        flash(f"'{concept.name}' 개념에 대해 다시 풀어볼 오답이 없습니다. 축하합니다!", "success")
        return redirect(url_for('student.mistake_notebook'))

    return render_template('student/reattempt_mistake_set.html',
                           concept=concept,
                           questions=questions_to_reattempt)