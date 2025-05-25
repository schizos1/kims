import os
from flask import Flask
from dotenv import load_dotenv
import google.generativeai as genai

from app.extensions import db, migrate, login_manager, bootstrap, moment

def create_app(config_class_string='config.Config'):
    print("--- DEBUG: create_app() 함수 시작 ---")
    app = Flask(__name__)

    # 설정 로드
    app.config.from_object(config_class_string)

    # .env 파일 로드
    dotenv_path = os.path.join(os.path.dirname(app.root_path), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print("--- DEBUG: .env 파일 로드됨 ---")
    else:
        print(f"--- WARNING: .env 파일 경로를 찾을 수 없음: {dotenv_path} ---")

    # Flask 확장 초기화
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)

    # 로그인 설정
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "로그인이 필요한 페이지입니다."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            print(f"Error loading user {user_id}: {e}")
            return None

    # Google AI 키 설정
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            print("--- DEBUG: Google AI 설정 완료 ---")
        else:
            print("--- WARNING: GOOGLE_API_KEY가 .env 파일에 없습니다. ---")
    except Exception as e:
        print(f"--- ERROR: Google AI 설정 중 오류 발생: {e} ---")

    # 블루프린트 등록
    from app.views import auth_views
    from app.student import student_bp
    from app.admin import admin_bp  # 새로운 admin 블루프린트

    app.register_blueprint(auth_views.bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        print("--- DEBUG: db.create_all() 관련 로직 확인 지점 ---")
        if app.debug and not app.config.get('TESTING', False):
            pass  # 필요 시 db.create_all() 수동 실행

    print("--- DEBUG: create_app() 함수 종료 ---")
    return app
