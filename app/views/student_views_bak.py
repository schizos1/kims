from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta # 표준 라이브러리는 상단에 유지
from sqlalchemy import func, case, distinct, and_ # SQLAlchemy 관련도 상단 유지 가능
import re # 표준 라이브러리는 상단에 유지
from textwrap import dedent # 표준 라이브러리는 상단에 유지
import google.generativeai as genai # 외부 라이브러리는 상단에 유지

from app import db # db 객체는 상단에 유지
AVAILABLE_THEME_CLASSES = {
    "blue": "theme-blue.css",
    "pink": "theme-pink.css",
    "dark": "theme-dark.css"
}
# --- ★★★ 블루프린트 정의에 url_prefix 추가 ★★★ ---
bp = Blueprint('student', __name__, url_prefix='/student')

AVAILABLE_MASCOTS = ['lion.png', 'robot.png', 'bunny.png', 'cat.png', 'dog.png'] # 이 목록은 DB에서 Mascot 객체를 가져와 동적으로 생성하는 것이 더 좋습니다.

# --- Helper Functions ---
def log_daily_activity(user_id):
    from app.models import DailyActivity # 함수 내 지역 임포트
    today = date.today()
    activity = DailyActivity.query.filter_by(user_id=user_id, date=today).first()
    if activity:
        activity.actions_count += 1
    else:
        activity = DailyActivity(user_id=user_id, date=today, actions_count=1)
        db.session.add(activity)
    # 참고: 이 함수는 호출하는 쪽에서 db.session.commit()을 해줘야 DB에 반영됩니다.

def award_trophy(user, trophy_id, commit_now=True):
    from app.models import UserTrophy, Trophy, User # User 모델도 필요할 수 있음 (user 객체 타입 힌팅 및 직접 조회 시)
    if not user: return False
    
    trophy_to_award = Trophy.query.get(trophy_id)
    if not trophy_to_award or not trophy_to_award.is_active: # 트로피가 없거나 비활성 상태면 중단
        return False

    already_has_trophy = UserTrophy.query.filter_by(user_id=user.id, trophy_id=trophy_id).first()
    if not already_has_trophy:
        current_user_trophy_count_before_this = UserTrophy.query.filter_by(user_id=user.id).count()
        
        new_user_trophy = UserTrophy(user_id=user.id, trophy_id=trophy_id)
        db.session.add(new_user_trophy)
        user.total_earned_points = (user.total_earned_points or 0) + trophy_to_award.points
        flash(f"🎉 축하합니다! '{trophy_to_award.name}' 트로피 ({trophy_to_award.points}P)를 획득했습니다! 🎉", "success")
        
        if current_user_trophy_count_before_this == 0 and trophy_id != 1: # 첫 트로피인데 ID 1이 아닌 다른 트로피를 먼저 받은 경우
            FIRST_EVER_TROPHY_ID = 1 
            first_trophy_definition = Trophy.query.get(FIRST_EVER_TROPHY_ID)
            if first_trophy_definition and first_trophy_definition.is_active and \
               not UserTrophy.query.filter_by(user_id=user.id, trophy_id=FIRST_EVER_TROPHY_ID).first():
                first_ever_user_trophy_obj = UserTrophy(user_id=user.id, trophy_id=FIRST_EVER_TROPHY_ID)
                db.session.add(first_ever_user_trophy_obj)
                user.total_earned_points = (user.total_earned_points or 0) + first_trophy_definition.points
                flash(f"✨ 그리고... '{first_trophy_definition.name}' 트로피 ({first_trophy_definition.points}P)도 획득했습니다! ✨", "success")
        
        if commit_now: # commit_now 플래그는 check_all_trophies에서 일괄 커밋하기 위해 사용
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error during awarding trophy (id: {trophy_id}) commit: {e}")
                return False
        return True
    return False

def check_and_award_login_trophies(user):
    # User 모델은 인자로 받음, Trophy는 award_trophy 내부에서 처리
    # 특정 ID 값들은 상수로 정의하거나 DB에서 가져오는 것이 좋습니다.
    if user.consecutive_login_days >= 30: award_trophy(user, 13, commit_now=False) 
    elif user.consecutive_login_days >= 15: award_trophy(user, 12, commit_now=False)
    elif user.consecutive_login_days >= 7: award_trophy(user, 11, commit_now=False)
    elif user.consecutive_login_days >= 3: award_trophy(user, 10, commit_now=False)

def check_and_award_activity_time_trophies(user):
    # User 모델은 인자로 받음
    now_time_hour_utc = datetime.utcnow().hour
    now_hour_kst = (now_time_hour_utc + 9) % 24 
    if 0 <= now_hour_kst < 5 or 22 <= now_hour_kst < 24: 
        award_trophy(user, 17, commit_now=False) # 밤샘의 제왕
    
    today_weekday = date.today().weekday()
    if today_weekday == 5 or today_weekday == 6: 
        award_trophy(user, 14, commit_now=False) # 주말 열공러

def check_and_award_effort_trophies(user):
    from app.models import StudyHistory # 함수 내 지역 임포트
    total_questions_solved = StudyHistory.query.filter_by(user_id=user.id, is_correct=True).count() # 맞힌 문제 수 기준이 더 적절할 수 있음
    if total_questions_solved >= 100: award_trophy(user, 16, commit_now=False) 
    elif total_questions_solved >= 50: award_trophy(user, 15, commit_now=False) 

def check_and_award_concept_mastery_trophies(user):
    from app.models import Question, StudyHistory, Concept # 함수 내 지역 임포트
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
    all_concepts_attempted_by_user_ids = [cid[0] for cid in db.session.query(distinct(Question.concept_id))\
        .join(StudyHistory, Question.id == StudyHistory.question_id)\
        .filter(StudyHistory.user_id == user.id).all()]

    for concept_id_val in all_concepts_attempted_by_user_ids:
        total_questions_in_concept = Question.query.filter_by(concept_id=concept_id_val).count()
        if total_questions_in_concept == 0: continue

        correct_answers_for_concept = db.session.query(func.count(distinct(StudyHistory.question_id)))\
            .join(Question, StudyHistory.question_id == Question.id)\
            .filter(StudyHistory.user_id == user.id, Question.concept_id == concept_id_val, StudyHistory.is_correct == True)\
            .scalar()
        
        if correct_answers_for_concept == total_questions_in_concept:
            perfect_score_concepts_count += 1
            
    if perfect_score_concepts_count >= 3: award_trophy(user, 35, commit_now=False)

def check_and_award_collection_trophies(user):
    from app.models import UserTrophy # 함수 내 지역 임포트
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
        db.session.commit() # 헬퍼 함수들에서 commit_now=False로 설정 후 여기서 일괄 커밋
    except Exception as e:
        db.session.rollback()
        print(f"Error during check_all_trophies final commit: {e}")
        # flash("트로피 상태를 최종 업데이트하는 중 오류가 발생했습니다.", "danger") # 뷰 함수에서 flash 처리 권장

# --- Student Routes ---
@bp.route('/')
@login_required
def index():
    return redirect(url_for('student.dashboard'))

@bp.route('/dashboard')
@login_required
def dashboard():
    from app.models import Subject, User 
    if current_user.role == 'admin': # 관리자일 경우 관리자 대시보드로
        return redirect(url_for('admin.admin_dashboard'))
    
    user = User.query.get(current_user.id) # DB에서 최신 사용자 정보 로드
    if not user:
        flash("사용자 정보를 찾을 수 없습니다.", "danger")
        return redirect(url_for('auth.logout'))

    # 로그인 시 트로피 체크 (auth_views에서 이미 호출하지만, 대시보드 접근 시에도 호출 가능)
    # check_all_trophies(user) # 이 호출은 auth_views의 login 함수에서 이미 수행됨

    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('student/dashboard.html', subjects=subjects, user=user)

@bp.route('/subject/<int:subject_id>/concepts')
@login_required
def view_subject_concepts(subject_id):
    from app.models import Subject, Concept, Question, StudyHistory
    subject = Subject.query.get_or_404(subject_id)
    concepts_data = []
    if subject:
        for concept_item in subject.concepts: # 변수명 변경
            total_q = Question.query.filter_by(concept_id=concept_item.id).count()
            learned_q = 0
            if total_q > 0: # 해당 컨셉에 문제가 있을 때만 진행도 계산
                learned_q = db.session.query(func.count(distinct(StudyHistory.question_id)))\
                                .join(Question, StudyHistory.question_id == Question.id)\
                                .filter(Question.concept_id == concept_item.id, 
                                        StudyHistory.user_id == current_user.id, 
                                        StudyHistory.is_correct == True).scalar() or 0
            progress = (learned_q / total_q * 100) if total_q > 0 else 0
            concepts_data.append({
                'id': concept_item.id,
                'name': concept_item.name,
                'progress': round(progress)
            })
    return render_template('student/concepts_list.html', subject=subject, concepts_data=concepts_data)

@bp.route('/concept/<int:concept_id>/learn/step/<int:step_order>')
@login_required
def learn_concept_step(concept_id, step_order):
    from app.models import Concept, Step, User
    concept = Concept.query.get_or_404(concept_id)
    current_step_obj = Step.query.filter_by(concept_id=concept.id, step_order=step_order).first_or_404()
    total_steps = Step.query.filter_by(concept_id=concept.id).count()
    
    user = User.query.get(current_user.id)

    if step_order == total_steps and total_steps > 0:
        log_daily_activity(user.id) # user.id 대신 current_user.id 사용 가능
        award_trophy(user, 2, commit_now=False) # 첫 개념 학습 완료 트로피 (ID 2 가정)
        check_all_trophies(user) 

    return render_template('student/learn_step.html',
                           concept=concept,
                           current_step=current_step_obj,
                           current_step_order=step_order,
                           total_steps=total_steps)

@bp.route('/concept/<int:concept_id>/test', methods=['GET', 'POST'])
@login_required
def start_concept_test(concept_id):
    from app.models import Concept, Question, StudyHistory, User
    concept = Concept.query.get_or_404(concept_id)
    user = User.query.get(current_user.id)

    if request.method == 'POST':
        num_correct = 0
        questions_in_test = list(concept.questions) # concept.questions 관계 사용
        
        for question_item in questions_in_test: 
            submitted_answer = request.form.get(f'answer_{question_item.id}')
            is_correct = False
            if submitted_answer is not None: 
                if question_item.question_type == 'multiple_choice':
                    is_correct = (submitted_answer == str(question_item.answer))
                else: 
                    is_correct = (submitted_answer.strip().lower() == str(question_item.answer).strip().lower())
                
                history_entry = StudyHistory(
                    user_id=current_user.id,
                    question_id=question_item.id,
                    submitted_answer=submitted_answer,
                    is_correct=is_correct,
                    mistake_status='active' if not is_correct else 'reviewed' 
                )
                db.session.add(history_entry)
            
            if is_correct:
                num_correct += 1
        
        log_daily_activity(current_user.id)
        total_questions_in_test_count = len(questions_in_test)
        
        if total_questions_in_test_count > 0:
            if num_correct == total_questions_in_test_count: 
                award_trophy(user, 4, commit_now=False) 
            if (num_correct / total_questions_in_test_count) >= 0.6: 
                award_trophy(user, 3, commit_now=False)
        
        check_all_trophies(user) 

        flash(f"테스트 완료! 총 {total_questions_in_test_count}문제 중 {num_correct}문제를 맞혔습니다.", "info")
        return redirect(url_for('student.view_test_results', concept_id=concept.id))

    questions_to_display = list(concept.questions)
    if not questions_to_display:
        flash("이 개념에 대한 문제가 아직 준비되지 않았습니다.", "warning")
        return redirect(url_for('student.view_subject_concepts', subject_id=concept.subject_id))
    
    return render_template('student/take_test.html', concept=concept, questions=questions_to_display)

@bp.route('/concept/<int:concept_id>/results')
@login_required
def view_test_results(concept_id):
    from app.models import Concept, Question, StudyHistory
    concept = Concept.query.get_or_404(concept_id)
    results_data = []
    num_correct_from_history = 0
    all_questions_in_concept = Question.query.filter_by(concept_id=concept.id).order_by(Question.id).all()

    for question_item in all_questions_in_concept:
        latest_history = StudyHistory.query.filter_by(
            user_id=current_user.id,
            question_id=question_item.id
        ).order_by(StudyHistory.timestamp.desc()).first()
        
        submitted_ans = '미제출'
        is_cor = False
        if latest_history:
            submitted_ans = latest_history.submitted_answer if latest_history.submitted_answer is not None else '미제출'
            is_cor = latest_history.is_correct
            if is_cor:
                 num_correct_from_history +=1

        results_data.append({
            'question_id': question_item.id,
            'question_content': question_item.content,
            'question_obj': question_item, 
            'submitted_answer': submitted_ans, 
            'correct_answer_num': question_item.answer, 
            'is_correct': is_cor
        })
        
    score_text = f"{num_correct_from_history} / {len(all_questions_in_concept) if all_questions_in_concept else 0}"
    return render_template('student/test_results.html',
                           concept=concept,
                           results=results_data,
                           score=score_text)

@bp.route('/generate-similar-question/<int:original_question_id>', methods=['GET', 'POST'])
@login_required
def generate_similar_question_page(original_question_id):
    from app.models import Question, StudyHistory, User
    original_question = Question.query.get_or_404(original_question_id)
    user = User.query.get(current_user.id)

    if request.method == 'GET':
        try:
            # genai.configure는 app/__init__.py 에서 이미 호출됨
            model = genai.GenerativeModel('gemini-1.5-flash-latest') # 모델명 확인 필요
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
            content = response.text # 변수명 content가 이미 사용중이므로 ai_response_text 등으로 변경 권장
            new_q_text = "AI가 유사 문제를 생성하지 못했습니다. 잠시 후 다시 시도해주세요."
            new_options = {"O1": "N/A", "O2": "N/A", "O3": "N/A", "O4": "N/A"}
            new_a_text = "N/A" # 정답은 숫자로 처리하는 것이 좋음 (예: int)
            if "[NEW_QUESTION]" in content: # 변수명 변경한 ai_response_text 사용
                try:
                    main_part = content.split("[NEW_QUESTION]")[1].strip() # 변수명 변경한 ai_response_text 사용
                    q_match = re.search(r"Q:\s*(.*?)(?=\n\s*O1:)", main_part, re.DOTALL)
                    o1_match = re.search(r"O1:\s*(.*?)(?=\n\s*O2:)", main_part, re.DOTALL)
                    o2_match = re.search(r"O2:\s*(.*?)(?=\n\s*O3:)", main_part, re.DOTALL)
                    o3_match = re.search(r"O3:\s*(.*?)(?=\n\s*O4:)", main_part, re.DOTALL)
                    o4_match = re.search(r"O4:\s*(.*?)(?=\n\s*A:)", main_part, re.DOTALL)
                    a_match = re.search(r"A:\s*([1-4])", main_part) # 정답은 1,2,3,4 중 하나로 가정
                    if q_match and o1_match and o2_match and o3_match and o4_match and a_match:
                        new_q_text = q_match.group(1).strip()
                        new_options['O1'] = o1_match.group(1).strip()
                        new_options['O2'] = o2_match.group(1).strip()
                        new_options['O3'] = o3_match.group(1).strip()
                        new_options['O4'] = o4_match.group(1).strip()
                        new_a_text = a_match.group(1).strip() # 문자열 형태의 숫자 '1', '2', ...
                        session['similar_question_text'] = new_q_text
                        session['similar_question_options'] = new_options
                        session['similar_Youtube_num'] = new_a_text # 세션 키 이름 일관성
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
            print(f"유사 문제 생성 중 AI API 오류: {e}")
            flash(f"유사 문제 생성 중 AI API 호출에 실패했습니다. 관리자에게 문의하세요.", "danger")
            return redirect(url_for('student.view_test_results', concept_id=original_question.concept_id))

    if request.method == 'POST':
        submitted_answer_num = request.form.get('submitted_answer') # '1', '2', '3', '4' 중 하나
        correct_answer_num = session.pop('similar_Youtube_num', None) # 세션 키 이름 일관성
        question_text = session.pop('similar_question_text', 'N/A')
        question_options = session.pop('similar_question_options', {"O1": "N/A", "O2": "N/A", "O3": "N/A", "O4": "N/A"})
        original_q_id = session.pop('original_question_id_for_similar', original_question.id) # 이 시점 original_question은 GET 요청 시의 것일 수 있음
        
        current_original_question = Question.query.get(original_q_id) # POST 요청 시에는 항상 ID로 다시 조회
        
        if correct_answer_num is None or not current_original_question:
            flash("오류: 채점 정보를 찾을 수 없거나 원본 문제를 찾을 수 없습니다. 다시 시도해주세요.", "danger")
            # original_question_id가 없을 경우를 대비해 dashboard로 리디렉션
            return redirect(url_for('student.dashboard') if not current_original_question else url_for('student.view_test_results', concept_id=current_original_question.concept_id))

        is_correct = (submitted_answer_num is not None and submitted_answer_num == correct_answer_num)
        feedback = {'submitted_choice_num': submitted_answer_num, 'correct_choice_num': correct_answer_num, 'is_correct': is_correct}
        
        log_daily_activity(current_user.id)
        if is_correct:
            original_mistakes = StudyHistory.query.filter_by(
                user_id=current_user.id,
                question_id=current_original_question.id,
                is_correct=False,
                mistake_status='active'
            ).all()
            for mistake_entry in original_mistakes: # 변수명 변경
                mistake_entry.mistake_status = 'mastered_via_similar'
            
            award_trophy(user, 20, commit_now=False) 
            award_trophy(user, 23, commit_now=False) 
        
        check_all_trophies(user)

        if is_correct:
            flash("정답입니다! 잘하셨어요. 👍", "success")
        else:
            flash("아쉽지만 틀렸어요. 정답을 확인해보세요. 😟", "warning")

        return render_template('student/similar_question_display.html',
                               original_question=current_original_question,
                               new_question_text=question_text,
                               new_question_options=question_options,
                               feedback_result=feedback)
                               
    # GET 요청도 아니고 POST 요청도 아닌 경우 (정상적이지 않은 접근)
    return redirect(url_for('student.view_test_results', concept_id=original_question.concept_id))

@bp.route('/my-page')
@login_required
def my_page():
    from app.models import UserTrophy, User, Mascot # Theme 모델 임포트 제거
    user = User.query.get(current_user.id)
    earned_user_trophies = UserTrophy.query.filter_by(user_id=current_user.id).order_by(UserTrophy.earned_at.desc()).all()
    all_mascots = Mascot.query.order_by(Mascot.name).all()
    
    # 테마는 AVAILABLE_THEME_CLASSES 딕셔너리를 사용 (student_views.py 상단에 정의된 것)
    return render_template('student/my_page.html', 
                           user=user, 
                           earned_user_trophies=earned_user_trophies, 
                           available_mascots=all_mascots,
                           available_themes_dict=AVAILABLE_THEME_CLASSES) # 변경

@bp.route('/my-stats')
@login_required
def my_stats():
    from app.models import Concept, Subject, StudyHistory, Question
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
    from app.models import User
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
    from app.models import DailyActivity
    activities = DailyActivity.query.filter_by(user_id=current_user.id).all()
    events = []
    for activity in activities:
        events.append({
            'title': f'{activity.actions_count}개 학습 활동', # 타이틀 개선
            'start': activity.date.isoformat(),
            'allDay': True
        })
    return jsonify(events)

@bp.route('/set-theme', methods=['POST'])
@login_required
def set_theme():
    from app.models import User # Theme 모델은 더 이상 DB에서 사용 안 함
    selected_theme_css_class = request.form.get('theme_css_class') # 폼에서 css_class 값을 직접 받음
    user = User.query.get(current_user.id) # 현재 사용자 객체 가져오기
    
    if not user: # 방어 코드
        flash("사용자 정보를 찾을 수 없습니다.", "danger")
        return redirect(url_for('auth.login'))

    # AVAILABLE_THEME_CLASSES는 이 파일 상단에 정의된 딕셔너리라고 가정
    if selected_theme_css_class and selected_theme_css_class in AVAILABLE_THEME_CLASSES.values():
        # User 모델에 selected_theme_css_class 같은 필드를 만들어 DB에 저장할 수도 있으나,
        # 여기서는 세션에만 저장하는 것으로 단순화 (이전 테마 기능 제거 결정에 따라)
        session['user_theme'] = selected_theme_css_class
        # db.session.commit() # User 모델 자체를 변경하지 않으므로 커밋 불필요
        
        theme_display_name = "선택된"
        for name, css_class_val in AVAILABLE_THEME_CLASSES.items():
            if css_class_val == selected_theme_css_class:
                theme_display_name = name
                break
        flash(f"테마가 '{theme_display_name}'(으)로 변경되었습니다.", "success")
    else:
        flash("유효하지 않은 테마를 선택했거나, 테마가 선택되지 않았습니다.", "danger")
        
    # 이전 페이지 또는 마이페이지로 리디렉션
    return redirect(request.referrer or url_for('student.my_page'))


@bp.route('/set-mascot', methods=['POST'])
@login_required
def set_mascot():
    from app.models import User, Mascot
    selected_mascot_id = request.form.get('mascot_id')
    user = User.query.get(current_user.id)

    if not user:
        flash('사용자 정보를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('auth.login'))

    if selected_mascot_id:
        try:
            mascot_id_int = int(selected_mascot_id)
            mascot_to_set = Mascot.query.get(mascot_id_int)
            if mascot_to_set:
                user.selected_mascot_id = mascot_to_set.id
                session['user_mascot'] = mascot_to_set.image_filename
                db.session.commit()
                flash(f"'{mascot_to_set.name}'(으)로 마스코트가 변경되었습니다!", 'success')
            else:
                flash('유효하지 않은 마스코트입니다.', 'danger')
        except ValueError:
            flash('잘못된 마스코트 ID 형식입니다.', 'danger')
    else:
        flash('마스코트를 선택해주세요.', 'warning')
        
    return redirect(request.referrer or url_for('student.my_page'))

# --- 오답 노트 관련 함수 ---
@bp.route('/my-mistake-notebook')
@login_required
def mistake_notebook():
    from app.models import StudyHistory, Question, Concept, Subject
    active_mistakes_query = StudyHistory.query.join(Question).join(Concept).join(Subject).filter(
        StudyHistory.user_id == current_user.id,
        StudyHistory.is_correct == False,
        StudyHistory.mistake_status == 'active'
    ).order_by(Subject.name, Concept.name, StudyHistory.timestamp.desc()).all()
    
    mistakes_by_concept = {}
    processed_question_ids_for_concept = {}

    for sh_item in active_mistakes_query: # 변수명 변경
        if sh_item.question and sh_item.question.concept and sh_item.question.concept.subject:
            concept_key = (sh_item.question.concept.id, sh_item.question.concept.name, sh_item.question.concept.subject.name)
            if concept_key not in mistakes_by_concept:
                mistakes_by_concept[concept_key] = []
                processed_question_ids_for_concept[concept_key] = set()

            if sh_item.question_id not in processed_question_ids_for_concept[concept_key]:
                mistakes_by_concept[concept_key].append(sh_item.question)
                processed_question_ids_for_concept[concept_key].add(sh_item.question_id)
        else:
            print(f"Warning: StudyHistory ID {sh_item.id} has missing related data.")
            
    grouped_mistakes = []
    for (concept_id_val, concept_name_val, subject_name_val), questions_list in mistakes_by_concept.items():
        if questions_list:
            grouped_mistakes.append({
                'concept_id': concept_id_val,
                'concept_name': concept_name_val,
                'subject_name': subject_name_val,
                'question_count': len(questions_list),
                'questions_sample': questions_list[:3] 
            })
    grouped_mistakes.sort(key=lambda x: (x['subject_name'], x['concept_name']))
    return render_template('student/mistake_notebook.html', grouped_mistakes=grouped_mistakes)

@bp.route('/concept/<int:concept_id>/reattempt-mistakes', methods=['GET', 'POST'])
@login_required
def reattempt_mistakes_by_concept(concept_id):
    from app.models import Concept, Question, StudyHistory, User
    concept = Concept.query.get_or_404(concept_id)
    user = User.query.get(current_user.id)

    # GET 요청 시 보여줄 오답 문제들 (POST에서도 사용 가능)
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

    if request.method == 'POST':
        num_correct = 0
        for question_item in questions_to_reattempt:
            submitted_answer = request.form.get(f'answer_{question_item.id}')
            is_correct_reattempt = False
            if submitted_answer is not None:
                if question_item.question_type == 'multiple_choice':
                    is_correct_reattempt = (submitted_answer == str(question_item.answer))
                else:
                    is_correct_reattempt = (submitted_answer.strip().lower() == str(question_item.answer).strip().lower())
                
                new_history_entry = StudyHistory(
                    user_id=current_user.id,
                    question_id=question_item.id,
                    submitted_answer=submitted_answer,
                    is_correct=is_correct_reattempt,
                    mistake_status='reviewed_after_reattempt' # 재시도 후 상태 변경
                )
                db.session.add(new_history_entry)

                if is_correct_reattempt:
                    num_correct += 1
                    StudyHistory.query.filter_by(
                        user_id=current_user.id,
                        question_id=question_item.id,
                        mistake_status='active' # 원래 'active'였던 오답을
                    ).update({'mistake_status': 'mastered_after_reattempt'}) # 정복 상태로 변경
            
        log_daily_activity(current_user.id)
        check_all_trophies(user) # db.session.commit() 포함

        flash(f"'{concept.name}' 개념 오답 재시도 완료! 총 {len(questions_to_reattempt)}문제 중 {num_correct}문제를 맞혔습니다.", "success")
        return redirect(url_for('student.mistake_notebook'))

    # GET 요청
    if not questions_to_reattempt:
        flash(f"'{concept.name}' 개념에 대해 다시 풀어볼 오답이 없습니다. 축하합니다!", "success")
        return redirect(url_for('student.mistake_notebook'))

    return render_template('student/reattempt_mistake_set.html',
                           concept=concept,
                           questions=questions_to_reattempt)