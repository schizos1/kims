import os

class Config:
    # 데이터베이스 파일의 경로를 설정하기 위해 현재 파일의 디렉토리 경로를 가져옵니다.
    BASE_DIR = os.path.dirname(__file__)

    # PostgreSQL 연결 정보
    SQLALCHEMY_DATABASE_URI = 'postgresql://kims_user:YOUR_PASSWORD@localhost:5432/kims_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 보안 키
    SECRET_KEY = "your-very-secret-key"  # 실제 운영 시 복잡한 키로 변경

    # Gemini API Key
    GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY')
