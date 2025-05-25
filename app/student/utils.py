# app/student/utils.py
from app.models import DailyActivity
from app.extensions import db
from datetime import date

def log_daily_activity(user_id):
    today = date.today()
    existing = DailyActivity.query.filter_by(user_id=user_id, date=today).first()
    if not existing:
        activity = DailyActivity(user_id=user_id, date=today, study_minutes=0, actions_count=0)
        db.session.add(activity)
        db.session.commit()
from app.models import Trophy, UserTrophy
from app.extensions import db
from datetime import datetime

def check_all_trophies(user):
    # 이미 받은 트로피 ID 목록
    earned_ids = {ut.trophy_id for ut in user.user_trophies}
    
    # 활성화된 모든 트로피 중 아직 받지 않은 것만 필터링
    active_trophies = Trophy.query.filter_by(is_active=True).all()
    for trophy in active_trophies:
        if trophy.id in earned_ids:
            continue  # 이미 받은 트로피는 제외

        if trophy.condition_type == "consecutive_login_days":
            if user.consecutive_login_days >= (trophy.condition_value_int or 0):
                _grant_trophy(user, trophy)

        elif trophy.condition_type == "total_points":
            if user.total_earned_points >= (trophy.condition_value_int or 0):
                _grant_trophy(user, trophy)

    db.session.commit()

def _grant_trophy(user, trophy):
    new_award = UserTrophy(
        user_id=user.id,
        trophy_id=trophy.id,
        earned_at=datetime.utcnow()
    )
    db.session.add(new_award)
    user.total_earned_points += trophy.points
