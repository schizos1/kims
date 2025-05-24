from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# 전역 SQLAlchemy 및 LoginManager 객체 생성
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """
    애플리케이션 팩토리 함수.
    Flask 앱 인스턴스를 생성하고 설정합니다.
    """
    app = Flask(__name__)

    # 1. config.py 파일로부터 설정 불러오기
    app.config.from_pyfile('../config.py')

    # 2. 확장(extensions) 초기화
    db.init_app(app)
    login_manager.init_app(app)
    
    # 3. 로그인 뷰 지정 (로그인이 필요한 페이지 접근 시 리디렉션될 경로)
    # 블루프린트 이름 'auth'와 그 안의 'login' 함수를 가리킵니다.
    login_manager.login_view = 'auth.login'

    # 4. 팩토리 함수 내에서 모델 임포트
    from . import models

    # 애플리케이션 컨텍스트 내에서 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
    
    # 5. 블루프린트 등록 (아직은 비어있지만 곧 채워나갈 것입니다)
    from .views import auth_views, admin_views, student_views
    # app.register_blueprint(auth_views.bp)
    # app.register_blueprint(admin_views.bp)
    # app.register_blueprint(student_views.bp)

    return app