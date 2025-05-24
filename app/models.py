from . import db
from flask_login import UserMixin
from datetime import datetime, date

# --- 데이터베이스 모델 정의 ---
class User(db.Model, UserMixin): # UserMixin을 여기에 꼭 추가해야 합니다.
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