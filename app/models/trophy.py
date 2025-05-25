from .. import db
from datetime import datetime

class Trophy(db.Model):
    __tablename__ = 'trophy'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200))
    icon_class = db.Column(db.String(100), nullable=False, default='fas fa-question-circle')
    points = db.Column(db.Integer, nullable=False, default=1000)

    # 트로피 조건
    condition_type = db.Column(db.String(50), nullable=True)
    condition_value_int = db.Column(db.Integer, nullable=True)
    condition_value_str = db.Column(db.String(100), nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

class UserTrophy(db.Model):
    __tablename__ = 'user_trophy'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trophy_id = db.Column(db.Integer, db.ForeignKey('trophy.id'), nullable=False)
    earned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    trophy = db.relationship('Trophy')
