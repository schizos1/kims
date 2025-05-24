# app.py - 테스트 문제 전체 표시 및 결과 페이지 수정
from app import create_app, db
app = create_app()
import os 
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, date, timedelta 
from dotenv import load_dotenv
import google.generativeai as genai
import random
from sqlalchemy import func, case, distinct
import re 
from textwrap import dedent

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("경고: .env 파일을 찾을 수 없습니다. API 키가 로드되지 않았을 수 있습니다.")

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads/trophies')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
AVAILABLE_MASCOTS = ['lion.png', 'robot.png', 'bunny.png', 'cat.png', 'dog.png'] 

try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Google AI 설정 오류: {e}")

# --- 데이터베이스 모델 정의 (이전과 동일) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) 
    role = db.Column(db.String(20), nullable=False, default='student')
    study_history = db.relationship('StudyHistory', backref='user', lazy='dynamic')
    user_trophies = db.relationship('UserTrophy', backref='user', lazy='dynamic') 
    daily_activities = db.relationship('DailyActivity', backref='user', lazy='dynamic')
    total_earned_points = db.Column(db.Integer, nullable=False, default=0)
    last_login_date = db.Column(db.Date, nullable=True)
    consecutive_login_days = db.Column(db.Integer, default=0)
    selected_theme = db.Column(db.String(50), nullable=True, default='theme-light-blue')
    selected_mascot_filename = db.Column(db.String(100), nullable=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    concepts = db.relationship('Concept', backref='subject', lazy=True, cascade="all, delete-orphan")

class Concept(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    steps = db.relationship('Step', backref='concept', lazy=True, order_by="Step.step_order", cascade="all, delete-orphan")
    questions = db.relationship('Question', backref='concept', lazy=True, cascade="all, delete-orphan")

class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    concept_id = db.Column(db.Integer, db.ForeignKey('concept.id'), nullable=False)
    
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False) 
    question_type = db.Column(db.String(50), nullable=False, default='multiple_choice') 
    option1 = db.Column(db.String(500), nullable=True)
    option2 = db.Column(db.String(500), nullable=True)
    option3 = db.Column(db.String(500), nullable=True)
    option4 = db.Column(db.String(500), nullable=True)
    answer = db.Column(db.String(200), nullable=True) 
    concept_id = db.Column(db.Integer, db.ForeignKey('concept.id'), nullable=False)
    answers = db.relationship('StudyHistory', backref='question', lazy='dynamic')

class Trophy(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    icon_class = db.Column(db.String(100), nullable=False, default='fas fa-question-circle')
    points = db.Column(db.Integer, nullable=False, default=1000)

class UserTrophy(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trophy_id = db.Column(db.Integer, db.ForeignKey('trophy.id'), nullable=False)
    earned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    trophy = db.relationship('Trophy') 

class StudyHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    submitted_answer = db.Column(db.String(200), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class DailyActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    study_minutes = db.Column(db.Integer, default=0) 
    actions_count = db.Column(db.Integer, default=0) 

# (PRECONFIGURED_TROPHIES 목록 및 init_trophies 함수는 이전과 동일)
PRECONFIGURED_TROPHIES = [
    {'id': 1, 'name': '첫 트로피!', 'description': '축하합니다! 첫 번째 트로피를 획득했습니다.', 'icon_class': 'fas fa-award', 'points': 500},
    {'id': 2, 'name': '새싹 탐험가', 'description': '첫 개념 학습을 모두 완료했어요! (모든 단계 통과)', 'icon_class': 'fas fa-seedling', 'points': 1000},
    {'id': 3, 'name': '첫 테스트 통과!', 'description': '첫 개념 테스트를 성공적으로 통과했어요! (60점 이상)', 'icon_class': 'fas fa-check-circle', 'points': 1200},
    {'id': 4, 'name': '만점의 별!', 'description': '개념 테스트에서 처음으로 만점을 받았어요!', 'icon_class': 'fas fa-star', 'points': 3000},
    {'id': 10, 'name': '출석 도장 (3일)', 'description': '3일 연속으로 학습에 참여했어요.', 'icon_class': 'fas fa-calendar-day', 'points': 1000},
    {'id': 11, 'name': '성실한 학습자 (7일)', 'description': '7일 연속으로 학습에 참여했어요.', 'icon_class': 'fas fa-calendar-check', 'points': 2000},
    {'id': 12, 'name': '꾸준함의 달인 (15일)', 'description': '15일 연속으로 학습에 참여했어요.', 'icon_class': 'fas fa-calendar-week', 'points': 3500},
    {'id': 13, 'name': '개근상 (30일)', 'description': '30일 연속으로 학습에 참여했어요! 정말 대단해요!', 'icon_class': 'fas fa-calendar-days', 'points': 5000},
    {'id': 14, 'name': '주말에도 열공!', 'description': '주말에도 학습을 완료했어요.', 'icon_class': 'fas fa-book-reader', 'points': 1200},
    {'id': 15, 'name': '노력의 땀방울 (50문제)', 'description': '총 50문제를 풀었어요.', 'icon_class': 'fas fa-tint', 'points': 1500},
    {'id': 16, 'name': '끈기의 승리자 (100문제)', 'description': '총 100문제를 풀었어요.', 'icon_class': 'fas fa-dumbbell', 'points': 2500},
    {'id': 17, 'name': '새벽의 학구열', 'description': '새벽 시간에 학습했어요. 부지런한데요!', 'icon_class': 'fas fa-moon', 'points': 1100},
    {'id': 20, 'name': '오뚝이 정신', 'description': '테스트 실패 후 재도전하여 통과했어요!', 'icon_class': 'fas fa-redo-alt', 'points': 1500},
    {'id': 21, 'name': '불굴의 도전자', 'description': '3번 이상 재도전하여 개념을 통과했어요.', 'icon_class': 'fas fa-user-astronaut', 'points': 2000},
    {'id': 22, 'name': '약점 극복의 용사', 'description': '정답률이 낮았던 개념을 재도전하여 만점을 받았어요!', 'icon_class': 'fas fa-shield-alt', 'points': 3000},
    {'id': 23, 'name': '깨달음 획득!', 'description': '유사 문제를 5번 이상 풀어보고 개념을 마스터했어요!', 'icon_class': 'fas fa-lightbulb', 'points': 1800},
    {'id': 30, 'name': '개념 이해자 (3개념 완료)', 'description': '총 3개의 개념 학습을 완료했어요. (테스트 통과 기준)', 'icon_class': 'fas fa-user-graduate', 'points': 1500},
    {'id': 31, 'name': '지식 탐험가 (10개념 완료)', 'description': '총 10개의 개념 학습을 완료했어요. (테스트 통과 기준)', 'icon_class': 'fas fa-map-signs', 'points': 2500},
    {'id': 32, 'name': '지혜의 샘물 (20개념 완료)', 'description': '총 20개의 개념 학습을 완료했어요. (테스트 통과 기준)', 'icon_class': 'fas fa-book-open', 'points': 4000},
    {'id': 33, 'name': '수학 정복자', 'description': '수학 과목의 모든 개념을 마스터했어요!', 'icon_class': 'fas fa-calculator', 'points': 5000},
    {'id': 34, 'name': '국어 정복자', 'description': '국어 과목의 모든 개념을 마스터했어요!', 'icon_class': 'fas fa-feather-alt', 'points': 5000},
    {'id': 35, 'name': '만점 컬렉터 (3회)', 'description': '서로 다른 3개의 개념 테스트에서 만점을 받았어요!', 'icon_class': 'fas fa-trophy', 'points': 4500},
    {'id': 36, 'name': '빛의 속도', 'description': '개념 테스트를 평균 시간보다 빠르게 완료하고 통과했어요!', 'icon_class': 'fas fa-bolt', 'points': 1800},
    {'id': 40, 'name': '초보 수집가 (트로피 5개)', 'description': '트로피를 5개 모았어요!', 'icon_class': 'fas fa-box', 'points': 1000},
    {'id': 41, 'name': '열성 수집가 (트로피 10개)', 'description': '트로피를 10개 모았어요!', 'icon_class': 'fas fa-boxes-stacked', 'points': 2000},
    {'id': 42, 'name': '트로피 마스터 (트로피 20개)', 'description': '트로피를 20개 이상 모았어요! 당신은 진정한 챔피언!', 'icon_class': 'fas fa-crown', 'points': 5000},
    {'id': 43, 'name': '플랫폼 탐험가', 'description': '플랫폼의 주요 기능들을 모두 사용해봤어요!', 'icon_class': 'fas fa-compass', 'points': 1000},
    {'id': 44, 'name': '리뷰의 달인', 'description': '학습 후 유용한 리뷰를 3회 이상 작성했어요.', 'icon_class': 'fas fa-comments', 'points': 1300},
    {'id': 45, 'name': '명예의 전당 입성', 'description': '누적 포인트 10000점을 달성했어요!', 'icon_class': 'fas fa-university', 'points': 2000}
]

def init_trophies():
    with app.app_context():
        for trophy_data in PRECONFIGURED_TROPHIES:
            trophy = Trophy.query.get(trophy_data['id'])
            if not trophy:
                trophy = Trophy(id=trophy_data['id'], name=trophy_data['name'], description=trophy_data['description'], icon_class=trophy_data['icon_class'], points=trophy_data['points'])
                db.session.add(trophy)
            else: 
                trophy.name = trophy_data['name']
                trophy.description = trophy_data['description']
                trophy.icon_class = trophy_data['icon_class']
                trophy.points = trophy_data['points']
        db.session.commit()
        print(f"{len(PRECONFIGURED_TROPHIES)} pre-configured trophies checked and initialized with points.")

# --- 헬퍼 함수 및 데코레이터 (이전과 동일) ---
def allowed_file(filename): return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
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
            if current_user_trophy_count_before_this == 0:
                FIRST_EVER_TROPHY_ID = 1
                if trophy_id != FIRST_EVER_TROPHY_ID: 
                    first_trophy_def = Trophy.query.get(FIRST_EVER_TROPHY_ID)
                    if first_trophy_def:
                        already_has_first_ever_explicit = UserTrophy.query.filter_by(user_id=user.id, trophy_id=FIRST_EVER_TROPHY_ID).first()
                        if not already_has_first_ever_explicit:
                            first_ever_user_trophy = UserTrophy(user_id=user.id, trophy_id=FIRST_EVER_TROPHY_ID)
                            db.session.add(first_ever_user_trophy)
                            user.total_earned_points += first_trophy_def.points
                            flash(f"✨ 그리고... '{first_trophy_def.name}' 트로피 ({first_trophy_def.points}P)도 획득했습니다! ✨", "success")
            if commit_now:
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"Error during awarding trophy commit: {e}")
                    flash("트로피 수여 중 오류가 발생했습니다. 다시 시도해주세요.", "danger")
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
    passed_concepts_query = db.session.query(Question.concept_id, func.count(StudyHistory.id).label('attempts'), func.sum(case((StudyHistory.is_correct == True, 1), else_=0)).label('corrects'))\
        .join(StudyHistory, Question.id == StudyHistory.question_id)\
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
    
    subquery = db.session.query(
        Question.concept_id,
        (func.sum(case((StudyHistory.is_correct == True, 1), else_=0)) == func.count(Question.id)).label('is_perfect')
    ).join(StudyHistory, StudyHistory.question_id == Question.id)\
    .filter(StudyHistory.user_id == user.id)\
    .group_by(Question.concept_id).subquery()
    count_perfect_concepts = db.session.query(func.count(subquery.c.concept_id)).filter(subquery.c.is_perfect == True).scalar()
    if count_perfect_concepts is not None and count_perfect_concepts >= 3:
        award_trophy(user, 35, commit_now=False)
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
    db.session.commit() 
    check_and_award_collection_trophies(user) 
    check_and_award_points_trophies(user)
    db.session.commit() 

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('이 페이지에 접근할 권한이 없습니다.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- 일반 사용자 라우트 ---
@app.route('/')
def home():
    return redirect(url_for('login')) if 'user_id' not in session else redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        user = None
        login_success = False
        if login_type == 'button_login':
            username_from_button = request.form.get('student_username')
            if username_from_button:
                user = User.query.filter_by(username=username_from_button, role='student').first()
                if user: login_success = True
        else: 
            username = request.form.get('username')
            password_candidate = request.form.get('password')
            if username and password_candidate:
                user = User.query.filter_by(username=username).first()
                if user and check_password_hash(user.password, password_candidate): login_success = True
                else: flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
            else: flash('아이디와 비밀번호를 모두 입력해주세요.', 'danger')
        if login_success and user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['user_theme'] = user.selected_theme or 'theme-light-blue'
            session['user_mascot'] = user.selected_mascot_filename
            today = date.today()
            if user.last_login_date:
                if user.last_login_date == today - timedelta(days=1): user.consecutive_login_days = (user.consecutive_login_days or 0) + 1
                elif user.last_login_date < today - timedelta(days=1): user.consecutive_login_days = 1
            else: user.consecutive_login_days = 1
            user.last_login_date = today
            log_daily_activity(user.id) 
            check_all_trophies(user)
            flash(f'{user.username}님, 환영합니다!', 'success')
            return redirect(url_for('admin_dashboard' if user.role == 'admin' else 'dashboard'))
        elif not login_success and login_type == 'button_login' and request.form.get('student_username'):
             flash(f"'{request.form.get('student_username')}' 사용자를 찾을 수 없습니다. 관리자에게 문의하세요.", 'danger')
    return render_template('login.html')

@app.route('/set-theme/<theme_name>')
def set_theme(theme_name):
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user:
        valid_themes = ['theme-light-blue', 'theme-fresh-green', 'theme-warm-orange']
        if theme_name in valid_themes:
            user.selected_theme = theme_name
            session['user_theme'] = theme_name 
            db.session.commit()
            readable_theme_name = theme_name.replace('theme-', '').replace('-', ' ').title()
            flash(f"테마가 '{readable_theme_name}' (으)로 변경되었습니다.", "success")
        else: flash("유효하지 않은 테마입니다.", "danger")
    else: 
        flash("사용자 정보를 찾을 수 없습니다.", "danger")
        return redirect(url_for('login'))
    return redirect(request.referrer or url_for('my_page'))

@app.route('/set-mascot', methods=['POST'])
def set_mascot():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'danger')
        return redirect(url_for('login'))
    selected_mascot = request.form.get('mascot_filename')
    if selected_mascot in AVAILABLE_MASCOTS:
        user = User.query.get(session['user_id'])
        if user:
            user.selected_mascot_filename = selected_mascot
            session['user_mascot'] = selected_mascot 
            db.session.commit()
            flash('마스코트가 변경되었습니다!', 'success')
        else: flash('사용자 정보를 찾을 수 없습니다.', 'danger')
    else: flash('유효하지 않은 마스코트입니다.', 'danger')
    return redirect(url_for('my_page'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('dashboard.html', subjects=subjects)

@app.route('/logout')
def logout():
    session.clear()
    flash('성공적으로 로그아웃되었습니다.', 'info')
    return redirect(url_for('login'))

@app.route('/subject/<int:subject_id>/concepts')
def view_subject_concepts(subject_id):
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    subject = Subject.query.get_or_404(subject_id)
    return render_template('student/concepts_list.html', subject=subject)

@app.route('/concept/<int:concept_id>/learn/step/<int:step_order>')
def learn_concept_step(concept_id, step_order):
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    concept = Concept.query.get_or_404(concept_id)
    current_step_obj = Step.query.filter_by(concept_id=concept.id, step_order=step_order).first_or_404()
    total_steps = Step.query.filter_by(concept_id=concept.id).count()
    if step_order == total_steps and total_steps > 0: 
        user = User.query.get(session['user_id'])
        if user:
            log_daily_activity(user.id)
            award_trophy(user, 2, commit_now=False)
            check_all_trophies(user)
    return render_template('student/learn_step.html', 
                           concept=concept, 
                           current_step=current_step_obj,
                           current_step_order=step_order,
                           total_steps=total_steps)

# ★★★ start_concept_test 함수 수정: GET 요청 시 모든 문제 전달, POST 채점 로직은 객관식 기준 ★★★
@app.route('/concept/<int:concept_id>/test', methods=['GET', 'POST'])
def start_concept_test(concept_id):
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    concept = Concept.query.get_or_404(concept_id)
    user_to_update = User.query.get(session['user_id'])
    if not user_to_update:
        flash("사용자 정보를 찾을 수 없습니다. 다시 로그인 해주세요.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        num_correct = 0
        # POST 요청에서는 실제로 렌더링된 문제들(questions_in_test)만 채점해야 함.
        # GET에서 전달한 문제 ID 목록을 세션에 저장했다가 POST에서 사용하는 것이 더 정확하나,
        # 여기서는 편의상 컨셉의 모든 문제를 기준으로 답을 받고, 있는 것만 채점.
        # 또는, form 에서 문제 ID 목록을 hidden input으로 전달받을 수도 있음.
        questions_in_test = list(concept.questions) # 현재는 해당 컨셉의 모든 문제를 대상으로 함

        for question in questions_in_test:
            submitted_answer = request.form.get(f'answer_{question.id}')
            
            is_correct = False
            if question.question_type == 'multiple_choice' and submitted_answer:
                is_correct = (submitted_answer == str(question.answer))
            else: # 주관식 또는 답안 미제출
                # 주관식 채점 로직 (필요시 여기에 추가, 현재는 객관식만 주로 다룸)
                # 만약 submitted_answer가 None이 아니고 question.answer도 None이 아니면 이전처럼 비교
                if submitted_answer is not None and question.answer is not None:
                    is_correct = (submitted_answer.strip().lower() == question.answer.strip().lower())

            if submitted_answer is not None: # 답을 제출한 경우에만 기록 (선택 안한 라디오는 None)
                history_entry = StudyHistory(user_id=session['user_id'], 
                                             question_id=question.id,
                                             submitted_answer=submitted_answer,
                                             is_correct=is_correct)
                db.session.add(history_entry)
            
            if is_correct:
                num_correct += 1
        
        log_daily_activity(session['user_id']) 
        total_questions_in_test_count = len(questions_in_test) # 실제 테스트에 나온 문제 수로 변경 가능성 있음
        
        if total_questions_in_test_count > 0 and num_correct == total_questions_in_test_count: 
            award_trophy(user_to_update, 4, commit_now=False) 
        if total_questions_in_test_count > 0 and (num_correct / total_questions_in_test_count) >= 0.6:
            award_trophy(user_to_update, 3, commit_now=False)
        check_all_trophies(user_to_update) 
        
        flash(f"테스트 완료! 총 {total_questions_in_test_count}문제 중 {num_correct}문제를 맞혔습니다.", "info")
        return redirect(url_for('view_test_results', concept_id=concept.id))

    # GET 요청 시: ★★★ 해당 개념의 모든 문제를 전달 ★★★
    questions_to_display = list(concept.questions) 
    if not questions_to_display:
        flash("이 개념에 대한 문제가 아직 준비되지 않았습니다. 관리자가 AI로 문제를 생성했는지 확인해주세요.", "warning")
        return redirect(url_for('view_subject_concepts', subject_id=concept.subject_id))
    
    return render_template('student/take_test.html', concept=concept, questions=questions_to_display)

@app.route('/concept/<int:concept_id>/results')
def view_test_results(concept_id):
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    concept = Concept.query.get_or_404(concept_id)
    user_id = session['user_id']
    results_data = []
    num_correct_from_history = 0
    
    # 해당 컨셉의 모든 질문을 가져옵니다.
    all_questions_in_concept = Question.query.filter_by(concept_id=concept.id).order_by(Question.id).all()

    for question in all_questions_in_concept:
        # 각 질문에 대한 가장 최근의 학습 기록을 찾습니다.
        latest_history = StudyHistory.query.filter_by(
            user_id=user_id,
            question_id=question.id
        ).order_by(StudyHistory.timestamp.desc()).first()
        
        submitted_ans = '선택 안 함' # 기본값
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

@app.route('/generate-similar-question/<int:original_question_id>', methods=['GET', 'POST'])
def generate_similar_question_page(original_question_id):
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    original_question = Question.query.get_or_404(original_question_id)
    user_to_update = User.query.get(session['user_id']) 
    if not user_to_update:
        flash("사용자 정보를 찾을 수 없습니다. 다시 로그인 해주세요.", "danger")
        return redirect(url_for('login'))
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
                        session['similar_Youtube'] = new_a_text 
                        session['original_question_id_for_similar'] = original_question.id
                    else:
                        flash("AI 응답에서 객관식 문제 형식을 제대로 파싱할 수 없습니다.", "warning")
                        return redirect(url_for('view_test_results', concept_id=original_question.concept_id))
                except Exception as e_parse:
                    print(f"AI Response Parsing Error: {e_parse} --- Content: {content}")
                    flash("AI 응답 형식이 올바르지 않아 문제를 가져올 수 없습니다.", "warning")
                    return redirect(url_for('view_test_results', concept_id=original_question.concept_id))
            else:
                 flash("AI가 유효한 형식으로 문제를 생성하지 못했습니다.", "warning")
                 return redirect(url_for('view_test_results', concept_id=original_question.concept_id))
            return render_template('student/similar_question_display.html', 
                                   original_question=original_question, 
                                   new_question_text=new_q_text,
                                   new_question_options=new_options,
                                   feedback_result=None) 
        except Exception as e:
            flash(f"유사 문제 생성 중 AI 오류: {e}", "danger")
            return redirect(url_for('view_test_results', concept_id=original_question.concept_id))
    if request.method == 'POST':
        submitted_answer = request.form.get('submitted_answer')
        correct_answer = session.pop('similar_Youtube', None) 
        question_text = session.pop('similar_question_text', 'N/A') 
        question_options = session.pop('similar_question_options', {"O1": "N/A", "O2": "N/A", "O3": "N/A", "O4": "N/A"})
        original_q_id = session.pop('original_question_id_for_similar', original_question.id) 
        current_original_question = Question.query.get(original_q_id if original_q_id else original_question_id)
        if correct_answer is None:
            flash("오류: 채점 정보를 찾을 수 없습니다. 다시 시도해주세요.", "danger")
            if current_original_question:
                 return redirect(url_for('view_test_results', concept_id=current_original_question.concept_id))
            else:
                 return redirect(url_for('dashboard'))
        is_correct = (submitted_answer is not None and submitted_answer == correct_answer) 
        feedback = {'submitted_choice_num': submitted_answer, 'correct_choice_num': correct_answer, 'is_correct': is_correct}
        if current_original_question: 
            log_daily_activity(user_to_update.id)
            if is_correct:
                award_trophy(user_to_update, 20, commit_now=False) 
                award_trophy(user_to_update, 23, commit_now=False) 
            check_all_trophies(user_to_update)
        if is_correct:
            flash("정답입니다! 잘하셨어요. 👍", "success")
        else:
            flash("아쉽지만 틀렸어요. 정답을 확인해보세요. 😟", "warning")
        return render_template('student/similar_question_display.html',
                               original_question=current_original_question,
                               new_question_text=question_text,
                               new_question_options=question_options,
                               feedback_result=feedback)

@app.route('/my-page')
def my_page():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    user = User.query.get_or_404(session['user_id'])
    earned_user_trophies = user.user_trophies.order_by(UserTrophy.earned_at.desc()).all()
    return render_template('student/my_page.html', user=user, earned_user_trophies=earned_user_trophies, available_mascots=AVAILABLE_MASCOTS)

@app.route('/my-stats')
def my_stats():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    user_id = session['user_id']
    stats_query = db.session.query(
        Concept.id.label('concept_id'),
        Concept.name.label('concept_name'),
        Subject.name.label('subject_name'),
        func.count(StudyHistory.id).label('total_attempted'),
        func.sum(case((StudyHistory.is_correct == True, 1), else_=0)).label('total_correct')
    ).join(Question, Concept.id == Question.concept_id)\
     .join(StudyHistory, Question.id == StudyHistory.question_id)\
     .join(Subject, Concept.subject_id == Subject.id)\
     .filter(StudyHistory.user_id == user_id)\
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

@app.route('/use-points', methods=['POST'])
def use_points():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    try:
        points_to_use = int(request.form.get('points_to_use', 0))
    except ValueError:
        flash('사용할 포인트를 숫자로 정확히 입력해주세요.', 'danger')
        return redirect(url_for('my_page'))
    if points_to_use <= 0:
        flash('사용할 포인트는 0보다 커야 합니다.', 'danger')
        return redirect(url_for('my_page'))
    user = User.query.get(session['user_id'])
    if not user: 
        flash('사용자 정보를 찾을 수 없습니다. 다시 로그인해주세요.', 'danger')
        return redirect(url_for('login'))
    if user.total_earned_points >= points_to_use:
        user.total_earned_points -= points_to_use
        check_all_trophies(user) 
        flash(f'{points_to_use} 포인트를 사용했습니다! 남은 포인트: {user.total_earned_points}P', 'success')
    else:
        flash(f'포인트가 부족합니다. (현재 보유: {user.total_earned_points}P, 사용 요청: {points_to_use}P)', 'danger')
    return redirect(url_for('my_page'))

@app.route('/my-calendar') 
def my_calendar():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login'))
    return render_template('student/my_calendar.html')

@app.route('/get-calendar-events')
def get_calendar_events():
    if 'user_id' not in session:
        return jsonify([]) 
    user_id = session['user_id']
    activities = DailyActivity.query.filter_by(user_id=user_id).all()
    events = []
    for activity in activities:
        events.append({
            'title': f'{activity.actions_count}개 활동', 
            'start': activity.date.isoformat(),    
            'allDay': True                          
        })
    return jsonify(events)

# --- 관리자 라우트 ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/subjects', methods=['GET', 'POST'])
@admin_required
def manage_subjects():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        if not Subject.query.filter_by(name=subject_name).first():
            db.session.add(Subject(name=subject_name))
            db.session.commit()
            flash('새 과목이 추가되었습니다.', 'success')
        else:
            flash('이미 존재하는 과목입니다.', 'warning')
        return redirect(url_for('manage_subjects'))
    return render_template('admin/subjects.html', subjects=Subject.query.all())

@app.route('/admin/subject/delete/<int:subject_id>', methods=['POST'])
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('과목이 삭제되었습니다.', 'success')
    return redirect(url_for('manage_subjects'))

@app.route('/admin/trophies')
@admin_required
def manage_trophies():
    trophies = Trophy.query.order_by(Trophy.id).all()
    return render_template('admin/trophies.html', trophies=trophies)

@app.route('/admin/subject/<int:subject_id>/concepts', methods=['GET', 'POST'])
@admin_required
def manage_concepts(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        concept_name = request.form['concept_name']
        if not Concept.query.filter_by(name=concept_name, subject_id=subject.id).first():
            new_concept = Concept(name=concept_name, subject_id=subject.id)
            db.session.add(new_concept)
            db.session.commit()
            flash(f"'{subject.name}' 과목에 새 개념이 추가되었습니다.", "success")
        else:
            flash("이미 존재하는 개념입니다.", "warning")
        return redirect(url_for('manage_concepts', subject_id=subject.id))
    return render_template('admin/concepts.html', subject=subject)

@app.route('/admin/concept/<int:concept_id>/questions')
@admin_required
def manage_questions(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    questions = Question.query.filter_by(concept_id=concept.id).order_by(Question.id).all()
    return render_template('admin/manage_questions.html', concept=concept, questions=questions)

@app.route('/admin/question/<int:question_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    question_to_edit = Question.query.get_or_404(question_id)
    if request.method == 'POST':
        question_to_edit.content = request.form['content']
        question_to_edit.option1 = request.form.get('option1')
        question_to_edit.option2 = request.form.get('option2')
        question_to_edit.option3 = request.form.get('option3')
        question_to_edit.option4 = request.form.get('option4')
        question_to_edit.answer = request.form['answer'] 
        question_to_edit.question_type = request.form.get('question_type', 'multiple_choice')
        db.session.commit()
        flash(f"문제(ID: {question_to_edit.id})가 성공적으로 수정되었습니다.", "success")
        return redirect(url_for('manage_questions', concept_id=question_to_edit.concept_id))
    return render_template('admin/edit_question.html', question=question_to_edit)

@app.route('/admin/concept/delete/<int:concept_id>', methods=['POST']) 
@admin_required
def delete_concept(concept_id): 
    concept = Concept.query.get_or_404(concept_id)
    subject_id = concept.subject_id 
    db.session.delete(concept)
    db.session.commit()
    flash('개념이 삭제되었습니다.', 'success')
    return redirect(url_for('manage_concepts', subject_id=subject_id))

@app.route('/admin/question/<int:question_id>/delete', methods=['POST']) 
@admin_required
def delete_question(question_id): 
    question_to_delete = Question.query.get_or_404(question_id)
    concept_id = question_to_delete.concept_id 
    db.session.delete(question_to_delete)
    db.session.commit()
    flash(f"문제(ID: {question_to_delete.id})가 삭제되었습니다.", "success")
    return redirect(url_for('manage_questions', concept_id=concept_id))

@app.route('/admin/concept/<int:concept_id>/generate', methods=['POST'])
@admin_required
def generate_ai_content(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    subject_name_for_prompt = concept.subject.name 
    Step.query.filter_by(concept_id=concept.id).delete()
    Question.query.filter_by(concept_id=concept.id).delete()
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        answer_format_instruction = "정답 또는 모범 답안을 작성해주세요."
        question_type_instruction = "다양한 유형의 예제 문제와 그에 대한 정답 또는 모범 답안을 제공해주세요."
        example_qa_format = dedent(f"""
        Q: <여기에 첫 번째 예제 문제 내용을 작성해주세요.>
        A: <여기에 첫 번째 예제 문제의 {answer_format_instruction}>""") 
        if "수학" in subject_name_for_prompt or "산수" in subject_name_for_prompt or "계산" in subject_name_for_prompt:
            question_type_instruction = "객관식 문제 10개를 만들어주세요. 각 문제는 질문(Q), 4개의 보기 (O1, O2, O3, O4), 그리고 정답 보기의 번호(A)를 포함해야 합니다."
            example_qa_format = dedent("""
            Q: 대한민국의 수도는 어디일까요?
            O1: 부산
            O2: 서울
            O3: 인천
            O4: 대구
            A: 2""")
        prompt = dedent(f"""
        당신은 대한민국 초등학생을 가르치는 친절하고 유능한 '{subject_name_for_prompt}' 과목 선생님입니다.
        '{subject_name_for_prompt}' 과목의 초등 교육과정 및 검정고시 준비에 맞춰, '{concept.name}' 라는 개념에 대한 학습 콘텐츠를 생성해주세요.
        출력은 반드시 아래의 지정된 형식으로만 제공해야 합니다.

        [STEP]
        Title: <학습 단계의 소제목>
        Explanation: <해당 단계에 대한 상세하고 친절한 설명. 아이들이 이해하기 쉬운 말투로 작성해주세요. 줄바꿈이 필요하면 실제 줄바꿈을 사용하세요.>
        (위 [STEP] 블록을 개념 이해에 필요한 만큼 반복해주세요. 최소 2개 이상 생성해주세요.)

        [EXAMPLE_QUESTIONS]
        # '{subject_name_for_prompt}' 과목의 특성을 반영하여, 이 개념을 이해했는지 확인할 수 있는 {question_type_instruction}
        # 생성되는 모든 문제와 보기, 특히 정답은 문법적, 내용적으로 반드시 정확해야 합니다.
        # 예시 (실제 생성 시에는 이 예시를 그대로 사용하지 마세요):
        # {example_qa_format}
        
        (이런 식으로 Q/A 또는 Q/O1-O4/A 쌍을 총 10개 생성)
        """)
        response = model.generate_content(prompt)
        content = response.text
        steps_data = []
        step_pattern = re.compile(r"\[STEP\]\s*Title:(.*?)\s*Explanation:(.*?)(?=\[STEP\]|\[EXAMPLE_QUESTIONS\]|$)", re.DOTALL | re.IGNORECASE)
        for match in step_pattern.finditer(content):
            steps_data.append({'title': match.group(1).strip(), 'explanation': match.group(2).strip()})
        questions_data = []
        example_questions_match = re.search(r"\[EXAMPLE_QUESTIONS\](.*)", content, re.DOTALL | re.IGNORECASE)
        if example_questions_match:
            questions_block_text = example_questions_match.group(1).strip()
            individual_question_blocks = re.split(r"\s*Q:", questions_block_text)
            for block in individual_question_blocks:
                block = block.strip()
                if not block: continue
                q_match = re.match(r"^(.*?)(?=\n\s*O1:|\n\s*A:)", block, re.DOTALL)
                question_text = q_match.group(1).strip() if q_match else None
                if not question_text: continue
                o1_match = re.search(r"\n\s*O1:\s*(.*?)(?=\n\s*O2:)", block, re.DOTALL)
                o2_match = re.search(r"\n\s*O2:\s*(.*?)(?=\n\s*O3:)", block, re.DOTALL)
                o3_match = re.search(r"\n\s*O3:\s*(.*?)(?=\n\s*O4:)", block, re.DOTALL)
                o4_match = re.search(r"\n\s*O4:\s*(.*?)(?=\n\s*A:)", block, re.DOTALL)
                a_mc_match = re.search(r"\n\s*A:\s*([1-4])(?!\S)", block) 
                a_short_match = re.search(r"\n\s*A:\s*(.*)", block, re.DOTALL)
                if o1_match and o2_match and o3_match and o4_match and a_mc_match:
                    questions_data.append({
                        'content': question_text,
                        'option1': o1_match.group(1).strip(),
                        'option2': o2_match.group(1).strip(),
                        'option3': o3_match.group(1).strip(),
                        'option4': o4_match.group(1).strip(),
                        'answer': a_mc_match.group(1).strip(),
                        'type': 'multiple_choice'
                    })
                elif a_short_match: 
                    questions_data.append({
                        'content': question_text, 
                        'answer': a_short_match.group(1).strip(),
                        'type': 'short_answer'
                    })
        step_order = 1
        for step_info in steps_data:
            new_step = Step(title=step_info['title'], explanation=step_info['explanation'], step_order=step_order, concept_id=concept.id)
            db.session.add(new_step)
            step_order += 1
        for q_info in questions_data:
            new_question = Question(
                content=q_info['content'], 
                option1=q_info.get('option1'),
                option2=q_info.get('option2'),
                option3=q_info.get('option3'),
                option4=q_info.get('option4'),
                answer=q_info['answer'], 
                question_type=q_info['type'],
                concept_id=concept.id
            )
            db.session.add(new_question)
        db.session.commit()
        flash(f"'{concept.name}' ({concept.subject.name})에 대한 학습 내용이 AI에 의해 성공적으로 생성되었습니다! ({len(steps_data)}개 단계, {len(questions_data)}개 문제)", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"AI 콘텐츠 생성 중 오류가 발생했습니다 ({concept.name}): {e}", 'danger')
        print(f"AI Error in generate_ai_content: {e}") 
        if 'content' in locals(): print(f"AI Response Content: {content}")
    return redirect(url_for('manage_concepts', subject_id=concept.subject_id))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')