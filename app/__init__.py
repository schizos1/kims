# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import google.generativeai as genai

# 전역 확장 객체 생성
db = SQLAlchemy()
login_manager = LoginManager()

# --- ★★★ 중요: 여기에 사용자님의 PRECONFIGURED_TROPHIES 전체 리스트를 붙여넣으세요! ★★★ ---
# 이전에 app.py에 있었던 완전한 트로피 목록이 필요합니다.
# 아래는 예시일 뿐이며, 이대로 두면 트로피가 몇 개만 생성됩니다.
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
# --- END PRECONFIGURED_TROPHIES ---

def create_app():
    """Flask 애플리케이션 팩토리 함수"""
    print("--- DEBUG: create_app() 함수 시작 ---")
    app = Flask(__name__)

    # 1. 기본 설정 로드
    app.config.from_pyfile('../config.py')

    # 2. .env 파일 로드 및 AI 설정
    basedir = os.path.abspath(os.path.dirname(__file__))
    dotenv_path = os.path.join(basedir, '../.env')
    
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print("--- DEBUG: .env 파일 로드됨 ---")
    else:
        print("경고: .env 파일을 찾을 수 없습니다. API 키가 로드되지 않았을 수 있습니다.")

    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("경고: GOOGLE_API_KEY가 .env 파일에 설정되지 않았거나 로드되지 않았습니다.")
        else:
            genai.configure(api_key=api_key)
            print("--- DEBUG: Google AI 설정 완료 ---")
    except Exception as e:
        print(f"Google AI 설정 오류: {e}")

    # 3. 추가적인 앱 설정
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads/trophies')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    # 4. 확장 기능 초기화
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # 5. Flask-Login 사용자 로더 함수 등록
    from .models import User 
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 6. 애플리케이션 컨텍스트 내에서 데이터베이스 테이블 생성 및 초기 데이터 적재
    with app.app_context():
        db.create_all() 

        from .models import Trophy # Trophy 모델 임포트
        def init_trophies_on_startup():
            print("--- DEBUG: init_trophies_on_startup() 함수 시작 ---")
            if not PRECONFIGURED_TROPHIES or len(PRECONFIGURED_TROPHIES) < 3: # 예시 리스트가 아닌지 확인
                print("--- 경고: PRECONFIGURED_TROPHIES 리스트가 제대로 채워지지 않은 것 같습니다! 예시 데이터만 사용됩니다. ---")

            for trophy_data in PRECONFIGURED_TROPHIES:
                trophy = Trophy.query.get(trophy_data['id'])
                if not trophy: 
                    trophy = Trophy(id=trophy_data['id'],
                                    name=trophy_data['name'],
                                    description=trophy_data['description'],
                                    icon_class=trophy_data['icon_class'],
                                    points=trophy_data['points'])
                    db.session.add(trophy)
                    print(f"--- DEBUG: Added trophy: {trophy.name} (ID: {trophy.id}) ---")
                else: 
                    trophy.name = trophy_data['name']
                    trophy.description = trophy_data['description']
                    trophy.icon_class = trophy_data['icon_class']
                    trophy.points = trophy_data['points']
                    print(f"--- DEBUG: Updated trophy: {trophy.name} (ID: {trophy.id}) ---")
            try:
                db.session.commit()
                print(f"--- DEBUG: {len(PRECONFIGURED_TROPHIES)}개의 트로피 설정 확인 및 초기화 완료 ---")
            except Exception as e:
                db.session.rollback()
                print(f"트로피 초기화 중 DB 커밋 오류: {e}")
        
        init_trophies_on_startup()

    # 7. 블루프린트 등록
    from .views import auth_views, admin_views, student_views
    app.register_blueprint(auth_views.bp)
    app.register_blueprint(admin_views.bp)
    app.register_blueprint(student_views.bp)

    print("--- DEBUG: create_app() 함수 종료, 앱 인스턴스 반환 ---")
    return app