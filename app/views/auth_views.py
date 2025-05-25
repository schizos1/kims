from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import date, timedelta
from app import db

# student_views에 있는 헬퍼 함수들을 가져옵니다.
# (주의: 이 구조는 student_views와 auth_views간 순환 참조를 유발할 수 있으나, 현재는 그대로 둡니다.)
from .student_views import log_daily_activity, check_all_trophies

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # ★★★ User 모델이 필요한 이 함수 안에서 직접 임포트합니다. ★★★
    from app.models import User

    if request.method == 'POST':
        login_type = request.form.get('login_type')
        user = None
        login_success = False

        if login_type == 'button_login':
            username_from_button = request.form.get('student_username')
            if username_from_button:
                user = User.query.filter_by(username=username_from_button, role='student').first()
                if user:
                    login_success = True
        else: # Admin/Form login
            username = request.form.get('username')
            password_candidate = request.form.get('password')
            if username and password_candidate:
                user = User.query.filter_by(username=username).first()
                if user:
                    if check_password_hash(user.password, password_candidate):
                        login_success = True
                    else:
                        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
                else:
                    flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
            else:
                flash('아이디와 비밀번호를 모두 입력해주세요.', 'danger')

        if login_success and user:
            login_user(user) 

            session['username'] = user.username
            session['role'] = user.role
            
            if user.selected_mascot:
                session['user_mascot'] = user.selected_mascot.image_filename
            else:
                session['user_mascot'] = None 

            session['user_theme'] = 'theme-light-blue' # 기본 테마 CSS 클래스로 항상 설정 (또는 다른 로직)
            
            today = date.today()
            if user.last_login_date:
                if user.last_login_date == today - timedelta(days=1):
                    user.consecutive_login_days = (user.consecutive_login_days or 0) + 1
                elif user.last_login_date < today: 
                    user.consecutive_login_days = 1
            else: 
                user.consecutive_login_days = 1
            user.last_login_date = today

            log_daily_activity(user.id)
            check_all_trophies(user)
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"DB 세션 커밋 중 오류 발생: {e}")
                flash("로그인 처리 중 오류가 발생했습니다.", "danger")
                return render_template('login.html')

            flash(f'{user.username}님, 환영합니다!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('student.dashboard'))

        elif not login_success and login_type == 'button_login' and request.form.get('student_username'):
            student_username_attempt = request.form.get('student_username')
            flash(f"'{student_username_attempt}' 사용자를 찾을 수 없습니다. 관리자에게 문의하세요.", 'danger')
        
        # 폼 로그인 실패 시 (비밀번호 불일치 등)
        # 특별한 처리 없이 그냥 로그인 페이지를 다시 렌더링합니다. (flash 메시지는 위에서 이미 전달됨)

    # GET 요청이거나 로그인 실패 시 로그인 페이지를 보여줍니다.
    # 학생 목록을 조회하여 버튼 로그인에 사용하도록 전달합니다.
    from app.models import User
    students = User.query.filter_by(role='student').order_by(User.username).all()
    return render_template('login.html', students=students)

@bp.route('/logout')
def logout():
    logout_user() 
    session.clear() # 세션의 모든 데이터를 깔끔하게 삭제
    flash('성공적으로 로그아웃되었습니다.', 'info')
    return redirect(url_for('auth.login'))