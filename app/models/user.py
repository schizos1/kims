from .. import db
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

class DailyActivity(db.Model):
    __tablename__ = 'daily_activity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    study_minutes = db.Column(db.Integer, default=0)
    actions_count = db.Column(db.Integer, default=0)
