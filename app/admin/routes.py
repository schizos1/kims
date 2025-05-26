from flask import render_template
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from pytz import timezone

from app.models import Trophy
from app.admin import admin_bp  # ✅ 이건 괜찮음 (admin_bp만 import)

# 관리자 전용 라우팅 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return "관리자 전용 페이지입니다.", 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route("/")
@login_required
@admin_required
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
# 임시 라우트: 개념 관리
@admin_bp.route("/subjects")
@login_required
@admin_required
def manage_subjects():
    return "과목 관리 (준비 중)"

@admin_bp.route("/concepts")
@login_required
@admin_required
def manage_concepts():
    return "개념 관리 (준비 중)"

@admin_bp.route("/questions")
@login_required
@admin_required
def manage_questions():
    return "문제 관리 (준비 중)"

@admin_bp.route("/trophies")
@login_required
@admin_required
def manage_trophies():
    return "트로피 관리 (준비 중)"

@admin_bp.route("/mascots")
@login_required
@admin_required
def manage_mascots():
    return "마스코트 관리 (준비 중)"

@admin_bp.route("/prompt-templates")
@login_required
@admin_required
def manage_prompt_templates():
    return "프롬프트 템플릿 관리 (준비 중)"
