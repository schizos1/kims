# app/models.py

from . import db
from flask_login import UserMixin
from datetime import datetime, date

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    selected_mascot_id = db.Column(db.Integer, db.ForeignKey('mascot.id'), nullable=True)
    total_earned_points = db.Column(db.Integer, nullable=False, default=0)
    last_login_date = db.Column(db.Date, nullable=True)
    consecutive_login_days = db.Column(db.Integer, default=0)
    selected_mascot = db.relationship('Mascot', foreign_keys=[selected_mascot_id])
    study_history = db.relationship('StudyHistory', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    user_trophies = db.relationship('UserTrophy', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    daily_activities = db.relationship('DailyActivity', backref='user', lazy='dynamic', cascade="all, delete-orphan")

class Subject(db.Model):
    __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    concepts = db.relationship('Concept', backref='subject', lazy=True, cascade="all, delete-orphan")

class Concept(db.Model):
    __tablename__ = 'concept'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    steps = db.relationship('Step', backref='concept', lazy=True, order_by="Step.step_order", cascade="all, delete-orphan")
    questions = db.relationship('Question', backref='concept', lazy=True, cascade="all, delete-orphan")

class Step(db.Model):
    __tablename__ = 'step'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    concept_id = db.Column(db.Integer, db.ForeignKey('concept.id'), nullable=False)

class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)
    question_type = db.Column(db.String(50), nullable=False, default='multiple_choice')
    option1 = db.Column(db.String(500), nullable=True)
    option2 = db.Column(db.String(500), nullable=True)
    option3 = db.Column(db.String(500), nullable=True)
    option4 = db.Column(db.String(500), nullable=True)
    option1_img = db.Column(db.String(100), nullable=True)
    option2_img = db.Column(db.String(100), nullable=True)
    option3_img = db.Column(db.String(100), nullable=True)
    option4_img = db.Column(db.String(100), nullable=True)
    answer = db.Column(db.String(200), nullable=True)
    source_type = db.Column(db.String(50), nullable=False, default='manual_admin')
    concept_id = db.Column(db.Integer, db.ForeignKey('concept.id'), nullable=False)
    answers = db.relationship('StudyHistory', backref='question', lazy='dynamic', cascade="all, delete-orphan")

class Trophy(db.Model):
    __tablename__ = 'trophy'
    id = db.Column(db.Integer, primary_key=True) # 기존 ID 체계를 유지 (예: 1, 2, ... 45)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    icon_class = db.Column(db.String(100), nullable=False, default='fas fa-question-circle')
    points = db.Column(db.Integer, nullable=False, default=1000)
    
    # --- ★★★ 트로피 조건 관련 필드 추가 ★★★ ---
    condition_type = db.Column(db.String(50), nullable=True) # 조건 유형, 초기 데이터는 null 허용 후 관리자가 설정
    condition_value_int = db.Column(db.Integer, nullable=True) # 조건에 필요한 숫자 값
    condition_value_str = db.Column(db.String(100), nullable=True) # 조건에 필요한 문자열 값 (예: 과목명, 개념 ID)
    is_active = db.Column(db.Boolean, default=True, nullable=False) # 이 트로피가 현재 활성화 상태인지
    # ------------------------------------

class UserTrophy(db.Model):
    __tablename__ = 'user_trophy'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trophy_id = db.Column(db.Integer, db.ForeignKey('trophy.id'), nullable=False)
    earned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    trophy = db.relationship('Trophy')

class StudyHistory(db.Model):
    __tablename__ = 'study_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    submitted_answer = db.Column(db.String(200), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    mistake_status = db.Column(db.String(50), default='active', nullable=False)

class DailyActivity(db.Model):
    __tablename__ = 'daily_activity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    study_minutes = db.Column(db.Integer, default=0)
    actions_count = db.Column(db.Integer, default=0)

class Mascot(db.Model):
    __tablename__ = 'mascot'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image_filename = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

class SoundEffect(db.Model):
    __tablename__ = 'sound_effect'
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(50), unique=True, nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=True)
# ... (기존 User, Subject, Concept, Step, Question, Trophy, UserTrophy, StudyHistory, DailyActivity, Theme, Mascot, SoundEffect 모델 정의는 그대로 둡니다) ...

# --- ★★★ 신규 모델: PromptTemplate 추가 ★★★ ---
class PromptTemplate(db.Model):
    __tablename__ = 'prompt_template'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False) # 프롬프트 템플릿 이름 (예: "초등 수학 객관식 v1")
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True) # 특정 과목 전용일 경우
    # concept_id = db.Column(db.Integer, db.ForeignKey('concept.id'), nullable=True) # 특정 개념 전용일 경우 (더 세분화 가능)
    
    # 프롬프트 내용. Jinja2처럼 변수 사용 가능 (예: {{ subject_name }}, {{ concept_name }})
    content = db.Column(db.Text, nullable=False) # prompt_text -> content 로 변경 
    
    notes = db.Column(db.Text, nullable=True) # 이 프롬프트에 대한 설명이나 사용법
    is_default_for_subject = db.Column(db.Boolean, default=False) # 해당 과목의 기본 프롬프트로 사용할지 여부
    # is_default_general = db.Column(db.Boolean, default=False) # 모든 과목에 대한 기본 프롬프트 (선택적)

    subject = db.relationship('Subject') 
    # concept = db.relationship('Concept') # concept_id를 사용한다면 필요

    def __repr__(self):
        return f'<PromptTemplate {self.name}>'
# --- ★★★ PromptTemplate 모델 추가 끝 ★★★ ---    
