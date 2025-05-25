from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta # 표준 라이브러리는 상단에 유지
from sqlalchemy import func, case, distinct, and_ # SQLAlchemy 관련도 상단 유지 가능
import re # 표준 라이브러리는 상단에 유지
from textwrap import dedent # 표준 라이브러리는 상단에 유지
import google.generativeai as genai # 외부 라이브러리는 상단에 유지

from app import db # db 객체는 상단에 유지

bp = Blueprint('student', __name__, url_prefix='/student') # url_prefix 추가

AVAILABLE_MASCOTS = ['lion.png', 'robot.png', 'bunny.png', 'cat.png', 'dog.png']

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

def award_trophy(user, trophy_id, commit_now=True):
    from app.models import UserTrophy, Trophy # 함수 내 지역 임포트
    if not user: return False
    
    # 특정 트로피 (예: ID 1)에 대한 특별한 중복 방지 로직 (필요시 확장)
    if trophy_id == 1 and UserTrophy.query.filter_by(user_id=user.id, trophy_id=1).first():
        return False

    already_has_trophy = UserTrophy.query.filter_by(user_id=user.id, trophy_id=trophy_id).first()
    if not already_has_trophy:
        trophy_to_award = Trophy.query.get(trophy_id)
        if trophy_to_award and trophy_to_award.is_active: # 활성화된 트로피만 수여
            current_user_trophy_count_before_this = UserTrophy.query.filter_by(user_id=user.id).count()
            
            new_user_trophy = UserTrophy(user_id=user.id, trophy_id=trophy_id)
            db.session.add(new_user_trophy)
            user.total_earned_points = (user.total_earned_points or 0) + trophy_to_award.points
            flash(f"🎉 축하합니다! '{trophy_to_award.name}' 트로피 ({trophy_to_award.points}P)를 획득했습니다! 🎉", "success")
            
            # 첫 트로피 획득 시 (단, 지금 받은 트로피가 ID 1번 '첫 트로피'가 아닐 경우)
            if current_user_trophy_count_before_this == 0 and trophy_id != 1:
                FIRST_EVER_TROPHY_ID = 1 
                first_trophy_definition = Trophy.query.get(FIRST_EVER_TROPHY_ID)
                if first_trophy_definition and first_trophy_definition.is_active and \
                   not UserTrophy.query.filter_by(user_id=user.id, trophy_id=FIRST_EVER_TROPHY_ID).first():
                    first_ever_user_trophy_obj = UserTrophy(user_id=user.id, trophy_id=FIRST_EVER_TROPHY_ID)
                    db.session.add(first_ever_user_trophy_obj)
                    user.total_earned_points = (user.total_earned_points or 0) + first_trophy_definition.points
                    flash(f"✨ 그리고... '{first_trophy_definition.name}' 트로피 ({first_trophy_definition.points}P)도 획득했습니다! ✨", "success")
            
            if commit_now:
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Error during awarding trophy (id: {trophy_id}) commit: {e}")
                    # flash("트로피 수여 중 오류가 발생했습니다.", "danger") # 중복 flash 방지
                    return False
            return True
    return False

def check_and_award_login_trophies(user):
    # User 모델은 인자로 받으므로 직접 임포트 불필요
    # Trophy 모델은 award_trophy 내부에서 임포트
    if user.consecutive_login_days >= 30: award_trophy(user, 13, commit_now=False) # 30일 연속
    elif user.consecutive_login_days >= 15: award_trophy(user, 12, commit_now=False) # 15일 연속
    elif user.consecutive_login_days >= 7: award_trophy(user, 11, commit_now=False)  # 7일 연속
    elif user.consecutive_login_days >= 3: award_trophy(user, 10, commit_now=False)  # 3일 연속

def check_and_award_activity_time_trophies(user):
    # User 모델은 인자로 받으므로 직접 임포트 불필요
    now_time_hour_utc = datetime.utcnow().hour
    now_hour_kst = (now_time_hour_utc + 9) % 24 
    if 0 <= now_hour_kst < 5 or 22 <= now_hour_kst < 24: # 밤샘의 제왕 (22시~05시)
        award_trophy(user, 17, commit_now=False)
    
    today_weekday = date.today().weekday() # 0: 월요일, 5: 토요일, 6: 일요일
    if today_weekday == 5 or today_weekday == 6: # 주말 열공러
        award_trophy(user, 14, commit_now=False)

def check_and_award_effort_trophies(user):
    from app.models import StudyHistory # 함수 내 지역 임포트
    total_questions_solved = StudyHistory.query.filter_by(user_id=user.id).count()
    if total_questions_solved >= 100: award_trophy(user, 16, commit_now=False) # 노력의 거인
    elif total_questions_solved >= 50: award_trophy(user, 15, commit_now=False) # 꾸준함의 증표

def check_and_award_concept_mastery_trophies(user):
    from app.models import Question, StudyHistory, Concept # 함수 내 지역 임포트
    
    # 60% 이상 정답률로 통과한 개념 수 기준 트로피
    passed_concepts_query = db.session.query(
        Question.concept_id,
        func.count(StudyHistory.id).label('attempts'),
        func.sum(case((StudyHistory.is_correct == True, 1), else_=0)).label('corrects')
    ).join(StudyHistory, Question.id == StudyHistory.question_id)\
    .filter(StudyHistory.user_id == user.id)\
    .group_by(Question.concept_id).all()

    passed_concept_ids = set()
    for concept_result in passed_concepts_query:
        # 0으로 나누기 방지
        if concept_result.attempts > 0 and (concept_result.corrects / concept_result.attempts) >= 0.6:
            passed_concept_ids.add(concept_result.concept_id)
    
    num_passed_concepts = len(passed_concept_ids)
    if num_passed_concepts >= 20: award_trophy(user, 32, commit_now=False) # 개념의 지배자
    elif num_passed_concepts >= 10: award_trophy(user, 31, commit_now=False) # 개념 마스터
    elif num_passed_concepts >= 3: award_trophy(user, 30, commit_now=False) # 첫 개념 정복자 (테스트 통과와 별개)

    # 만점(100%)으로 통과한 개념 수 기준 트로피
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
            
    if perfect_score_concepts_count >= 3: award_trophy(user, 35, commit_now=False) # 완벽주의자

def check_and_award_collection_trophies(user):
    from app.models import UserTrophy # 함수 내 지역 임포트
    num_user_trophies = UserTrophy.query.filter_by(user_id=user.id).count()
    if num_user_trophies >= 20: award_trophy(user, 42, commit_now=False) # 컬렉션 마스터
    elif num_user_trophies >= 10: award_trophy(user, 41, commit_now=False) # 트로피 수집가
    elif num_user_trophies >= 5: award_trophy(user, 40, commit_now=False) # 트로피 사냥꾼

def check_and_award_points_trophies(user):
    # User 모델은 인자로 받음
    if user.total_earned_points >= 10000:
        award_trophy(user, 45, commit_now=False) # 포인트 거상

def check_all_trophies(user):
    # User 모델은 인자로 받음
    if not user: return
    
    # 개별 트로피 조건 함수 호출
    check_and_award_login_trophies(user)
    check_and_award_activity_time_trophies(user)
    check_and_award_effort_trophies(user)
    check_and_award_concept_mastery_trophies(user)
    check_and_award_collection_trophies(user)
    check_and_award_points_trophies(user)
    
    # 모든 변경사항 일괄 커밋
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error during check_all_trophies final commit: {e}")
        flash("트로피 상태를 최종 업데이트하는 중 오류가 발생했습니다.", "danger")

# --- Student Routes ---
@bp.route('/')
@login_required
def index():
    # 모델 사용 안 함
    return redirect(url_for('student.dashboard'))

@bp.route('/dashboard')
@login_required
def dashboard():
    from app.models import Subject, User # 함수 내 지역 임포트
    if current_user.role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    
    # current_user 프록시 객체 대신 DB에서 최신 User 객체 정보를 가져옴
    user = User.query.get(current_user.id)
    if not user: # 혹시 모를 경우 대비
        flash("사용자 정보를 불러올 수 없습니다.", "danger")
        return redirect(url_for('auth.logout'))

    check_all_trophies(user) # 변경사항은 이 함수 내부에서 커밋됨

    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('student/dashboard.html', subjects=subjects, user=user) # user 객체 전달

@bp.route('/subject/<int:subject_id>/concepts')
@login_required
def view_subject_concepts(subject_id):
    from app.models import Subject, Concept, Question, StudyHistory # 함수 내 지역 임포트
    subject = Subject.query.get_or_404(subject_id)
    concepts_data = []
    for concept in subject.concepts: # subject.concepts 관계 사용
        total_q = Question.query.filter_by(concept_id=concept.id).count()
        learned_q = db.session.query(func.count(distinct(StudyHistory.question_id)))\
                        .join(Question).filter(Question.concept_id == concept.id, 
                                               StudyHistory.user_id == current_user.id, 
                                               StudyHistory.is_correct == True).scalar()
        progress = (learned_q / total_q * 100) if total_q > 0 else 0
        concepts_data.append({
            'id': concept.id,
            'name': concept.name,
            'progress': round(progress)
        })
    return render_template('student/concepts_list.html', subject=subject, concepts_data=concepts_data)

@bp.route('/concept/<int:concept_id>/learn/step/<int:step_order>')
@login_required
def learn_concept_step(concept_id, step_order):
    from app.models import Concept, Step, User # 함수 내 지역 임포트
    concept = Concept.query.get_or_404(concept_id)
    current_step_obj = Step.query.filter_by(concept_id=concept.id, step_order=step_order).first_or_404()
    total_steps = Step.query.filter_by(concept_id=concept.id).count()
    
    user = User.query.get(current_user.id) # 트로피 수여를 위해 User 객체 로드

    if step_order == total_steps and total_steps > 0: # 마지막 스텝 학습 완료 시
        log_daily_activity(current_user.id)
        award_trophy(user, 2, commit_now=False) # '첫걸음' 트로피 (첫 개념 학습 완료)
        check_all_trophies(user) # 변경사항 커밋 포함

    return render_template('student/learn_step.html',
                           concept=concept,
                           current_step=current_step_obj,
                           current_step_order=step_order,
                           total_steps=total_steps)

@bp.route('/concept/<int:concept_id>/test', methods=['GET', 'POST'])
@login_required
def start_concept_test(concept_id):
    from app.models import Concept, Question, StudyHistory, User # 함수 내 지역 임포트
    concept = Concept.query.get_or_404(concept_id)
    user = User.query.get(current_user.id) # 트로피 수여를 위해 User 객체 로드

    if request.method == 'POST':
        num_correct = 0
        questions_in_test = list(concept.questions) 
        
        for question_obj in questions_in_test: # 변수명 변경
            submitted_answer = request.form.get(f'answer_{question_obj.id}')
            is_correct = False
            if submitted_answer is not None: 
                if question_obj.question_type == 'multiple_choice':
                    is_correct = (submitted_answer == str(question_obj.answer))
                else: 
                    is_correct = (submitted_answer.strip().lower() == str(question_obj.answer).strip().lower())
                
                history_entry = StudyHistory(
                    user_id=current_user.id,
                    question_id=question_obj.id,
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
                award_trophy(user, 4, commit_now=False) # "만점의 별!"
            if (num_correct / total_questions_in_test_count) >= 0.6: 
                award_trophy(user, 3, commit_now=False) # "첫 테스트 통과!"
        
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
    from app.models import Concept, Question, StudyHistory # 함수 내 지역 임포트
    concept = Concept.query.get_or_404(concept_id)
    results_data = []
    num_correct_from_history = 0
    all_questions_in_concept = Question.query.filter_by(concept_id=concept.id).order_by(Question.id).all()

    for question_item in all_questions_in_concept: # 변수명 변경
        latest_history = StudyHistory.query.filter_by(
            user_id=current_user.id,
            question_id=question_item.id
        ).order_by(StudyHistory.timestamp.desc()).first()
        
        submitted_ans = '미제출' # 기본값을 '미제출'로
        is_cor = False
        if latest_history:
            submitted_ans = latest_history.submitted_answer if latest_history.submitted_answer is not None else '미제출'
            is_cor = latest_history.is_correct
            if is_cor: # 정확히 맞춘 경우에만 카운트
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
    from app.models import Question, StudyHistory, User # 함수 내 지역 임포트
    original_question = Question.query.get_or_404(original_question_id)
    user = User.query.get(current_user.id) # User 객체 로드

    if request.method == 'GET':
        try:
            # genai.configure(api_key=os.getenv('GOOGLE_API_KEY')) # 앱 시작 시 한 번만 호출
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
                        session['similar_Youtube_num'] = new_a_text # 세션 키 이름 변경 
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
        submitted_answer_num = request.form.get('submitted_answer')
        correct_answer_num = session.pop('similar_Youtube_num', None) # 세션 키 이름 변경
        question_text = session.pop('similar_question_text', 'N/A')
        question_options = session.pop('similar_question_options', {"O1": "N/A", "O2": "N/A", "O3": "N/A", "O4": "N/A"})
        original_q_id = session.pop('original_question_id_for_similar', original_question.id)
        
        current_original_question = Question.query.get(original_q_id if original_q_id else original_question_id)
        
        if correct_answer_num is None:
            flash("오류: 채점 정보를 찾을 수 없습니다. 다시 시도해주세요.", "danger")
            if current_original_question:
                return redirect(url_for('student.view_test_results', concept_id=current_original_question.concept_id))
            else: # 정말 드문 경우지만, original_question_id도 없는 경우
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
                for mistake_history_entry in original_mistakes: 
                    mistake_history_entry.mistake_status = 'mastered_via_similar'
                
                award_trophy(user, 20, commit_now=False) # '오답 극복의 달인'
                award_trophy(user, 23, commit_now=False) # 'AI 조련사' (유사문제 정답)
            
            check_all_trophies(user) # 변경사항 커밋 포함

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
    from app.models import UserTrophy, User, Theme, Mascot # Theme, Mascot 추가
    user = User.query.get(current_user.id)
    earned_user_trophies = UserTrophy.query.filter_by(user_id=current_user.id).order_by(UserTrophy.earned_at.desc()).all()
    all_themes = Theme.query.order_by(Theme.name).all()
    all_mascots = Mascot.query.order_by(Mascot.name).all()
    
    return render_template('student/my_page.html', 
                           user=user, 
                           earned_user_trophies=earned_user_trophies, 
                           available_mascots=all_mascots, # 모델에서 가져온 전체 마스코트
                           available_themes=all_themes)   # 모델에서 가져온 전체 테마

@bp.route('/my-stats')
@login_required
def my_stats():
    from app.models import Concept, Subject, StudyHistory, Question # 함수 내 지역 임포트
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
    from app.models import User # 함수 내 지역 임포트
    try:
        points_to_use = int(request.form.get('points_to_use', 0))
    except ValueError:
        flash('사용할 포인트를 숫자로 정확히 입력해주세요.', 'danger')
        return redirect(url_for('student.my_page'))

    if points_to_use <= 0:
        flash('사용할 포인트는 0보다 커야 합니다.', 'danger')
        return redirect(url_for('student.my_page'))

    user = User.query.get(current_user.id)
    if not user: # 이 경우는 거의 없겠지만, 방어 코드
        flash('사용자 정보를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('auth.login'))

    if user.total_earned_points >= points_to_use:
        user.total_earned_points -= points_to_use
        check_all_trophies(user) # 포인트 사용 후 트로피 조건이 변경될 수 있으므로 확인
        flash(f'{points_to_use} 포인트를 사용했습니다! 남은 포인트: {user.total_earned_points}P', 'success')
    else:
        flash(f'포인트가 부족합니다. (현재 보유: {user.total_earned_points}P, 사용 요청: {points_to_use}P)', 'danger')
    return redirect(url_for('student.my_page'))

@bp.route('/my-calendar')
@login_required
def my_calendar():
    # 모델 사용 안 함 (단, 캘린더에 특정 정보를 표시하려면 필요할 수 있음)
    return render_template('student/my_calendar.html')

@bp.route('/get-calendar-events')
@login_required
def get_calendar_events():
    from app.models import DailyActivity # 함수 내 지역 임포트
    activities = DailyActivity.query.filter_by(user_id=current_user.id).all()
    events = []
    for activity in activities:
        events.append({
            'title': f'{activity.actions_count}개 활동', # 예시 타이틀
            'start': activity.date.isoformat(),
            'allDay': True
            # 'url': url_for('student.view_activity_on_date', date_str=activity.date.isoformat()) # 클릭 시 해당 날짜 활동 보기 (구현 필요)
        })
    return jsonify(events)

@bp.route('/set-theme', methods=['POST']) # POST로 변경, 폼에서 theme_id를 받도록 수정
@login_required
def set_theme():
    from app.models import User, Theme # 함수 내 지역 임포트
    selected_theme_id = request.form.get('theme_id')
    user = User.query.get(current_user.id)
    
    if not user:
        flash("사용자 정보를 찾을 수 없습니다.", "danger")
        return redirect(url_for('auth.login'))

    if selected_theme_id:
        theme_to_set = Theme.query.get(selected_theme_id)
        if theme_to_set:
            user.selected_theme_id = theme_to_set.id
            session['user_theme'] = theme_to_set.css_class # 세션에는 css_class 저장
            db.session.commit()
            flash(f"테마가 '{theme_to_set.name}' (으)로 변경되었습니다.", "success")
        else:
            flash("유효하지 않은 테마입니다.", "danger")
    else:
        flash("테마를 선택해주세요.", "warning")
        
    return redirect(request.referrer or url_for('student.my_page'))

@bp.route('/set-mascot', methods=['POST'])
@login_required
def set_mascot():
    from app.models import User, Mascot # 함수 내 지역 임포트
    selected_mascot_id = request.form.get('mascot_id') # mascot_id를 받도록 변경
    user = User.query.get(current_user.id)

    if not user:
        flash('사용자 정보를 찾을 수 없습니다.', 'danger')
        return redirect(url_for('auth.login'))

    if selected_mascot_id:
        mascot_to_set = Mascot.query.get(selected_mascot_id)
        if mascot_to_set:
            user.selected_mascot_id = mascot_to_set.id # User 모델의 selected_mascot_id 필드 사용
            session['user_mascot'] = mascot_to_set.image_filename # 세션에는 파일명 저장
            db.session.commit()
            flash('마스코트가 변경되었습니다!', 'success')
        else:
            flash('유효하지 않은 마스코트입니다.', 'danger')
    else:
        flash('마스코트를 선택해주세요.', 'warning')
        
    return redirect(request.referrer or url_for('student.my_page'))

# --- ★★★ 오답 노트 관련 신규/수정된 함수 ★★★ ---
@bp.route('/my-mistake-notebook')
@login_required
def mistake_notebook():
    from app.models import StudyHistory, Question, Concept, Subject # 함수 내 지역 임포트
    active_mistakes_query = StudyHistory.query.join(Question).join(Concept).join(Subject).filter(
        StudyHistory.user_id == current_user.id,
        StudyHistory.is_correct == False,
        StudyHistory.mistake_status == 'active'
    ).order_by(Subject.name, Concept.name, StudyHistory.timestamp.desc()).all()
    
    mistakes_by_concept = {}
    processed_question_ids_for_concept = {}

    for sh in active_mistakes_query:
        # sh.question.concept 이 None이 아님을 가정 (정상적인 데이터라면 항상 존재)
        if sh.question and sh.question.concept and sh.question.concept.subject:
            concept_key = (sh.question.concept.id, sh.question.concept.name, sh.question.concept.subject.name)
            
            if concept_key not in mistakes_by_concept:
                mistakes_by_concept[concept_key] = []
                processed_question_ids_for_concept[concept_key] = set()

            if sh.question_id not in processed_question_ids_for_concept[concept_key]:
                mistakes_by_concept[concept_key].append(sh.question)
                processed_question_ids_for_concept[concept_key].add(sh.question_id)
        else:
            # 관련 데이터가 없는 경우 로그 (개발 중 디버깅에 유용)
            print(f"Warning: StudyHistory ID {sh.id} has missing related question/concept/subject data.")
            
    grouped_mistakes = []
    for (concept_id, concept_name, subject_name), questions_list in mistakes_by_concept.items(): # 변수명 변경
        if questions_list:
            grouped_mistakes.append({
                'concept_id': concept_id,
                'concept_name': concept_name,
                'subject_name': subject_name,
                'question_count': len(questions_list),
                'questions_sample': questions_list[:3] 
            })
    
    grouped_mistakes.sort(key=lambda x: (x['subject_name'], x['concept_name']))

    return render_template('student/mistake_notebook.html', grouped_mistakes=grouped_mistakes)

@bp.route('/concept/<int:concept_id>/reattempt-mistakes', methods=['GET', 'POST'])
@login_required
def reattempt_mistakes_by_concept(concept_id):
    from app.models import Concept, Question, StudyHistory, User # 함수 내 지역 임포트
    concept = Concept.query.get_or_404(concept_id)
    user = User.query.get(current_user.id) # User 객체 로드

    if request.method == 'POST':
        num_correct = 0
        
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

        for question_obj in questions_to_reattempt: # 변수명 변경
            submitted_answer = request.form.get(f'answer_{question_obj.id}')
            is_correct_reattempt = False
            if submitted_answer is not None:
                if question_obj.question_type == 'multiple_choice':
                    is_correct_reattempt = (submitted_answer == str(question_obj.answer))
                else:
                    is_correct_reattempt = (submitted_answer.strip().lower() == str(question_obj.answer).strip().lower())
                
                new_history_entry = StudyHistory(
                    user_id=current_user.id,
                    question_id=question_obj.id,
                    submitted_answer=submitted_answer,
                    is_correct=is_correct_reattempt,
                    mistake_status='reviewed' # 재시도 기록은 'reviewed' (또는 다른 상태)로
                )
                db.session.add(new_history_entry)

                if is_correct_reattempt:
                    num_correct += 1
                    StudyHistory.query.filter_by(
                        user_id=current_user.id,
                        question_id=question_obj.id,
                        mistake_status='active'
                    ).update({'mistake_status': 'mastered_after_reattempt'})
            
        log_daily_activity(current_user.id)
        check_all_trophies(user)

        flash(f"'{concept.name}' 개념 오답 재시도 완료! 총 {len(questions_to_reattempt)}문제 중 {num_correct}문제를 맞혔습니다.", "success")
        return redirect(url_for('student.mistake_notebook'))

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