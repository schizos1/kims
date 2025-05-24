from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash # 비밀번호 해시 비교
from datetime import date, timedelta
from flask_login import login_user, logout_user # 로그인/로그아웃 기능

from app import db # db 객체
from app.models import User # User 모델

# student_views에 있는 헬퍼 함수들을 가져옵니다.
from .student_views import log_daily_activity, check_all_trophies

bp = Blueprint('auth', __name__)

# 임시로 정의했던 Helper function stubs는 삭제합니다 (위에서 import 하므로)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        user = None
        login_success = False

        # Student button login
        if login_type == 'button_login':
            username_from_button = request.form.get('student_username')
            print(f"\n--- 학생 버튼 로그인 시도: '{username_from_button}' ---")
            if username_from_button:
                user = User.query.filter_by(username=username_from_button, role='student').first()
                if user:
                    print(f"DB에서 학생 '{user.username}' 찾음 (ID: {user.id}, 역할: {user.role})")
                    login_success = True # For button login, finding the user is success
                else:
                    print(f"DB에서 학생 '{username_from_button}' (역할 'student') 찾지 못함")
        # Admin/Form login
        else:
            username = request.form.get('username')
            password_candidate = request.form.get('password')
            print(f"\n--- 폼 로그인 시도: 사용자명='{username}' ---")
            if username and password_candidate:
                user = User.query.filter_by(username=username).first()
                if user:
                    print(f"DB에서 사용자 '{user.username}' 찾음 (ID: {user.id}, 역할: {user.role})")
                    print(f"DB 저장된 해시: '{user.password}'")
                    if check_password_hash(user.password, password_candidate):
                        print("비밀번호 일치함.")
                        login_success = True
                    else:
                        print("비밀번호 불일치.")
                        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
                else:
                    print(f"DB에서 사용자 '{username}' 찾지 못함.")
                    flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
            else:
                print("사용자명 또는 비밀번호가 입력되지 않음.")
                flash('아이디와 비밀번호를 모두 입력해주세요.', 'danger')

        # Process successful login
        if login_success and user:
            login_user(user) # Use Flask-Login's function
            print(f"'{user.username}' Flask-Login으로 로그인 처리됨.")

            # --- ★★★ 사용자 이름 세션 설정 추가 ★★★ ---
            session['username'] = user.username
            # -----------------------------------------
            session['role'] = user.role
            session['user_theme'] = user.selected_theme or 'theme-light-blue'
            session['user_mascot'] = user.selected_mascot_filename
            print(f"세션 설정: username='{session.get('username')}', role='{session['role']}', theme='{session['user_theme']}', mascot='{session['user_mascot']}'")
            
            # Update consecutive login days
            today = date.today()
            if user.last_login_date:
                if user.last_login_date == today - timedelta(days=1):
                    user.consecutive_login_days = (user.consecutive_login_days or 0) + 1
                elif user.last_login_date < today: # If last login was before yesterday
                    user.consecutive_login_days = 1
            else: # First login
                user.consecutive_login_days = 1
            user.last_login_date = today
            print(f"'{user.username}' 연속 출석일: {user.consecutive_login_days}, 마지막 로그인 날짜: {user.last_login_date}")

            # Call helper functions (imported from student_views)
            log_daily_activity(user.id)
            check_all_trophies(user)
            
            try:
                db.session.commit()
                print("DB 세션 커밋 성공 (로그인 관련 업데이트).")
            except Exception as e:
                db.session.rollback()
                print(f"DB 세션 커밋 중 오류 발생: {e}")
                flash("로그인 처리 중 오류가 발생했습니다.", "danger")
                return render_template('login.html')


            flash(f'{user.username}님, 환영합니다!', 'success')
            print(f"'{user.username}' 로그인 최종 성공. 역할: '{user.role}'. 리디렉션 준비...")
            
            if user.role == 'admin':
                print("관리자 대시보드로 리디렉션합니다: admin.admin_dashboard")
                return redirect(url_for('admin.admin_dashboard'))
            else:
                print("학생 대시보드로 리디렉션합니다: student.dashboard")
                return redirect(url_for('student.dashboard'))

        # Handle student button login failure specifically if not caught by general form logic
        elif not login_success and login_type == 'button_login' and request.form.get('student_username'):
            student_username_attempt = request.form.get('student_username')
            flash(f"'{student_username_attempt}' 사용자를 찾을 수 없습니다. 관리자에게 문의하세요.", 'danger')
            print(f"'{student_username_attempt}' 학생 버튼 로그인 최종 실패.")
        
        if not login_success:
            print("로그인 최종 실패 (login_success가 True가 되지 못함). 로그인 페이지로 돌아감.")

    return render_template('login.html')


@bp.route('/logout')
def logout():
    print(f"\n--- 로그아웃 시도: 사용자='{session.get('username', 'None')}' ---")
    logout_user() # Use Flask-Login's function
    # session.clear() # username, role 등 특정 정보만 지우거나, logout_user()가 충분할 수 있음
    print("Flask-Login으로 로그아웃 처리됨.")
    flash('성공적으로 로그아웃되었습니다.', 'info')
    return redirect(url_for('auth.login'))