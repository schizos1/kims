# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import google.generativeai as genai
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

PRECONFIGURED_TROPHIES = [
    {'id': 1, 'name': '첫 트로피!', 'description': '축하합니다! 첫 번째 트로피를 획득했습니다.', 'icon_class': 'fas fa-award', 'points': 500},
    {'id': 2, 'name': '새싹 탐험가', 'description': '첫 개념 학습을 모두 완료했어요! (모든 단계 통과)', 'icon_class': 'fas fa-seedling', 'points': 1000},
    {'id': 3, 'name': '첫 테스트 통과!', 'description': '첫 개념 테스트를 성공적으로 통과했어요! (60점 이상)', 'icon_class': 'fas fa-check-circle', 'points': 1200},
    {'id': 4, 'name': '만점의 별!', 'description': '개념 테스트에서 처음으로 만점을 받았어요!', 'icon_class': 'fas fa-star', 'points': 3000},
    {'id': 10, 'name': '출석 도장 (3일)', 'description': '3일 연속으로 학습에 참여했어요.', 'icon_class': 'fas fa-calendar-day', 'points': 1000},
    {'id': 11, 'name': '성실한 학습자 (7일)', 'description': '7일 연속으로 학습에 참여했어요.', 'icon_class': 'fas fa-calendar-check', 'points': 2000},
    {'id': 12, 'name': '꾸준함의 달인 (15일)', 'description': '15일 연속으로 학습에 참여했어요.', 'icon_class': 'fas fa-calendar-week', 'points': 3500},
    {'id': 13, 'name': '개근상 (30일)', 'description': '30일 연속으로 학습에 참여했어요! 정말 대단해요!', 'icon_class': 'fas fa-calendar-days', 'points': 5000},
    {'id': 14, 'name': '주말에도 열공!', 'description': '주말에도 학습을 완료했어요.', 'icon_class': 'fas fa-book-reader', 'points': 1200},
    {'id': 15, 'name': '노력의 땀방울 (50문제)', 'description': '총 50문제를 풀었어요.', 'icon_class': 'fas fa-tint', 'points': 1500},
    {'id': 16, 'name': '끈기의 승리자 (100문제)', 'description': '총 100문제를 풀었어요.', 'icon_class': 'fas fa-dumbbell', 'points': 2500},
    {'id': 17, 'name': '새벽의 학구열', 'description': '새벽 시간에 학습했어요. 부지런한데요!', 'icon_class': 'fas fa-moon', 'points': 1100},
    {'id': 20, 'name': '오뚝이 정신', 'description': '테스트 실패 후 재도전하여 통과했어요!', 'icon_class': 'fas fa-redo-alt', 'points': 1500},
    {'id': 21, 'name': '불굴의 도전자', 'description': '3번 이상 재도전하여 개념을 통과했어요.', 'icon_class': 'fas fa-user-astronaut', 'points': 2000},
    {'id': 22, 'name': '약점 극복의 용사', 'description': '정답률이 낮았던 개념을 재도전하여 만점을 받았어요!', 'icon_class': 'fas fa-shield-alt', 'points': 3000},
    {'id': 23, 'name': '깨달음 획득!', 'description': '유사 문제를 5번 이상 풀어보고 개념을 마스터했어요!', 'icon_class': 'fas fa-lightbulb', 'points': 1800},
    {'id': 30, 'name': '개념 이해자 (3개념 완료)', 'description': '총 3개의 개념 학습을 완료했어요. (테스트 통과 기준)', 'icon_class': 'fas fa-user-graduate', 'points': 1500},
    {'id': 31, 'name': '지식 탐험가 (10개념 완료)', 'description': '총 10개의 개념 학습을 완료했어요. (테스트 통과 기준)', 'icon_class': 'fas fa-map-signs', 'points': 2500},
    {'id': 32, 'name': '지혜의 샘물 (20개념 완료)', 'description': '총 20개의 개념 학습을 완료했어요. (테스트 통과 기준)', 'icon_class': 'fas fa-book-open', 'points': 4000},
    {'id': 33, 'name': '수학 정복자', 'description': '수학 과목의 모든 개념을 마스터했어요!', 'icon_class': 'fas fa-calculator', 'points': 5000},
    {'id': 34, 'name': '국어 정복자', 'description': '국어 과목의 모든 개념을 마스터했어요!', 'icon_class': 'fas fa-feather-alt', 'points': 5000},
    {'id': 35, 'name': '만점 컬렉터 (3회)', 'description': '서로 다른 3개의 개념 테스트에서 만점을 받았어요!', 'icon_class': 'fas fa-trophy', 'points': 4500},
    {'id': 36, 'name': '빛의 속도', 'description': '개념 테스트를 평균 시간보다 빠르게 완료하고 통과했어요!', 'icon_class': 'fas fa-bolt', 'points': 1800},
    {'id': 40, 'name': '초보 수집가 (트로피 5개)', 'description': '트로피를 5개 모았어요!', 'icon_class': 'fas fa-box', 'points': 1000},
    {'id': 41, 'name': '열성 수집가 (트로피 10개)', 'description': '트로피를 10개 모았어요!', 'icon_class': 'fas fa-boxes-stacked', 'points': 2000},
    {'id': 42, 'name': '트로피 마스터 (트로피 20개)', 'description': '트로피를 20개 이상 모았어요! 당신은 진정한 챔피언!', 'icon_class': 'fas fa-crown', 'points': 5000},
    {'id': 43, 'name': '플랫폼 탐험가', 'description': '플랫폼의 주요 기능들을 모두 사용해봤어요!', 'icon_class': 'fas fa-compass', 'points': 1000},
    {'id': 44, 'name': '리뷰의 달인', 'description': '학습 후 유용한 리뷰를 3회 이상 작성했어요.', 'icon_class': 'fas fa-comments', 'points': 1300},
    {'id': 45, 'name': '명예의 전당 입성', 'description': '누적 포인트 10000점을 달성했어요!', 'icon_class': 'fas fa-university', 'points': 2000}
]

def create_app():
    print("--- DEBUG: create_app() 함수 시작 ---")
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')

    basedir = os.path.abspath(os.path.dirname(__file__))
    dotenv_path = os.path.join(basedir, '../.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print("--- DEBUG: .env 파일 로드됨 ---")
    else:
        print("경고: .env 파일을 찾을 수 없습니다.")
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("경고: GOOGLE_API_KEY가 설정되지 않았습니다.")
        else:
            genai.configure(api_key=api_key)
            print("--- DEBUG: Google AI 설정 완료 ---")
    except Exception as e:
        print(f"Google AI 설정 오류: {e}")

    app.config['UPLOAD_FOLDER_TROPHIES'] = os.path.join(app.root_path, 'static/uploads/trophies')
    # --- ★★★ 문제 이미지 업로드 폴더 설정 추가 ★★★ ---
    app.config['UPLOAD_FOLDER_QUESTIONS'] = os.path.join(app.root_path, 'static/uploads/questions')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    # --- ★★★ 설정 추가 끝 ★★★ ---

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'

    from .models import User 
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all() 
        print("--- DEBUG: db.create_all() 호출됨 (테이블 구조 확인/생성) ---")
        # 트로피 초기화 로직은 init_db.py로 완전히 이전했으므로 여기서 호출 안 함

    from .views import auth_views, admin_views, student_views
    app.register_blueprint(auth_views.bp)
    app.register_blueprint(admin_views.bp)
    app.register_blueprint(student_views.bp)

    print("--- DEBUG: create_app() 함수 종료, 앱 인스턴스 반환 ---")
    return app