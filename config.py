import os

# 데이터베이스 파일의 경로를 설정하기 위해 현재 파일의 디렉토리 경로를 가져옵니다.
BASE_DIR = os.path.dirname(__file__)

SECRET_KEY = 'your_secret_key'  # 나중에 더 복잡한 키로 변경하세요.
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'kims.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
GEMINI_API_KEY = 'YOUR_API_KEY' # 실제 Gemini API 키를 입력하세요.