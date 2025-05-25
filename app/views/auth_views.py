# app/views/auth_views.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from datetime import date, timedelta
from flask_login import login_user, logout_user

from app import db
from app.models import User # Mascot, Theme 모델은 User 객체를 통해 접근하므로 직접 임포트 불필요

# student_views에 있는 헬퍼 함수들을 가져옵니다.
from .student_views import log_daily_activity, check_all_trophies

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        user = None
        login_success = False

        if login_type == 'button_login':
            username_from_button = request.form.get('student_username')
            # print(f"\n--- 학생 버튼 로그인 시도: '{username_from_button}' ---") # 디버깅용
            if username_from_button:
                user = User.query.filter_by(username=username_from_button, role='student').first()
                if user:
                    # print(f"DB에서 학생 '{user.username}' 찾음 (ID: {user.id}, 역할: {user.role})") # 디버깅용
                    login_success = True
                # else:
                    # print(f"DB에서 학생 '{username_from_button}' (역할 'student') 찾지 못함") # 디버깅용
        else: # Admin/Form login
            username = request.form.get('username')
            password_candidate = request.form.get('password')
            # print(f"\n--- 폼 로그인 시도: 사용자명='{username}' ---") # 디버깅용
            if username and password_candidate:
                user = User.query.filter_by(username=username).first()
                if user:
                    # print(f"DB에서 사용자 '{user.username}' 찾음 (ID: {user.id}, 역할: {user.role})") # 디버깅용
                    if check_password_hash(user.password, password_candidate):
                        # print("비밀번호 일치함.") # 디버깅용
                        login_success = True
                    else:
                        # print("비밀번호 불일치.") # 디버깅용
                        flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
                else:
                    # print(f"DB에서 사용자 '{username}' 찾지 못함.") # 디버깅용
                    flash('아이디 또는 비밀번호가 올바르지 않습니다.', 'danger')
            else:
                # print("사용자명 또는 비밀번호가 입력되지 않음.") # 디버깅용
                flash('아이디와 비밀번호를 모두 입력해주세요.', 'danger')

        if login_success and user:
            login_user(user) 
            # print(f"'{user.username}' Flask-Login으로 로그인 처리됨.") # 디버깅용

            session['username'] = user.username
            session['role'] = user.role
            
            # --- ★★★ 마스코트 및 테마 세션 저장 방식 최종 수정 ★★★ ---
            if user.selected_mascot: # User 모델의 selected_mascot 관계를 통해 Mascot 객체에 접근
                session['user_mascot'] = user.selected_mascot.image_filename
            else:
                session['user_mascot'] = None 

            if user.selected_theme: # User 모델의 selected_theme 관계를 통해 Theme 객체에 접근
                session['user_theme'] = user.selected_theme.css_class
            else:
                session['user_theme'] = 'theme-light-blue' # 기본 테마 CSS 클래스
            # --- ★★★ 수정 끝 ★★★ ---

            # print(f"세션 설정: username='{session.get('username')}', role='{session['role']}', theme='{session['user_theme']}', mascot='{session.get('user_mascot')}'") # 디버깅용
            
            today = date.today()
            if user.last_login_date:
                if user.last_login_date == today - timedelta(days=1):
                    user.consecutive_login_days = (user.consecutive_login_days or 0) + 1
                elif user.last_login_date < today: 
                    user.consecutive_login_days = 1
            else: 
                user.consecutive_login_days = 1
            user.last_login_date = today
            # print(f"'{user.username}' 연속 출석일: {user.consecutive_login_days}, 마지막 로그인 날짜: {user.last_login_date}") # 디버깅용

            log_daily_activity(user.id)
            check_all_trophies(user)
            
            try:
                db.session.commit()
                # print("DB 세션 커밋 성공 (로그인 관련 업데이트).") # 디버깅용
            except Exception as e:
                db.session.rollback()
                print(f"DB 세션 커밋 중 오류 발생: {e}")
                flash("로그인 처리 중 오류가 발생했습니다.", "danger")
                return render_template('login.html')

            flash(f'{user.username}님, 환영합니다!', 'success')
            # print(f"'{user.username}' 로그인 최종 성공. 역할: '{user.role}'. 리디렉션 준비...") # 디버깅용
            
            if user.role == 'admin':
                # print("관리자 대시보드로 리디렉션합니다: admin.admin_dashboard") # 디버깅용
                return redirect(url_for('admin.admin_dashboard'))
            else:
                # print("학생 대시보드로 리디렉션합니다: student.dashboard") # 디버깅용
                return redirect(url_for('student.dashboard'))

        elif not login_success and login_type == 'button_login' and request.form.get('student_username'):
            student_username_attempt = request.form.get('student_username')
            flash(f"'{student_username_attempt}' 사용자를 찾을 수 없습니다. 관리자에게 문의하세요.", 'danger')
            # print(f"'{student_username_attempt}' 학생 버튼 로그인 최종 실패.") # 디버깅용
        
        if not login_success:
            # print("로그인 최종 실패 (login_success가 True가 되지 못함). 로그인 페이지로 돌아감.") # 디버깅용
            pass # 이미 flash 메시지가 위에서 처리되었을 수 있음

    return render_template('login.html')

@bp.route('/logout')
def logout():
    # print(f"\n--- 로그아웃 시도: 사용자='{session.get('username', 'None')}' ---") # 디버깅용
    
    # Flask-Login이 관리하는 세션 정보 (예: _user_id)는 logout_user()가 처리
    logout_user() 
    
    # 직접 세션에 저장한 추가 정보들 삭제
    session.pop('role', None)
    session.pop('user_theme', None)
    session.pop('user_mascot', None)
    # session.pop('username', None) # current_user.username을 사용하는 것이 더 좋음

    # print("Flask-Login으로 로그아웃 처리됨. 추가 세션 정보 삭제됨.") # 디버깅용
    flash('성공적으로 로그아웃되었습니다.', 'info')
    return redirect(url_for('auth.login'))