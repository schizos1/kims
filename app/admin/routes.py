# app/admin/routes.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from pytz import timezone

from app.admin import admin_bp
from app.models import Trophy

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# 관리자 전용 라우팅 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return "관리자 전용 페이지입니다.", 403
        return f(*args, **kwargs)
    return decorated_function

# 관리자 대시보드 - 트로피 관리
@admin_bp.route("/")
@login_required
def admin_dashboard():
    now = datetime.now(timezone("Asia/Seoul"))
    weekday_map = {
        'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
        'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
    }
    weekday_ko = weekday_map[now.strftime('%A')]

    trophies = Trophy.query.order_by(Trophy.id).all()

    return render_template(
        "admin/dashboard.html",
        now=now,
        weekday_ko=weekday_ko,
        trophies=trophies
    )
