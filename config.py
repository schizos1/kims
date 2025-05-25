import os

# 데이터베이스 파일의 경로를 설정하기 위해 현재 파일의 디렉토리 경로를 가져옵니다.
BASE_DIR = os.path.dirname(__file__)

# --- ★★★ PostgreSQL 연결 정보로 수정 ★★★ ---
# postgresql://사용자이름:비밀번호@호스트:포트/데이터베이스이름
# 우리가 만든 사용자: kims_user
# 우리가 설정한 비밀번호: YOUR_PASSWORD (실제 설정하신 비밀번호로 변경)
# 호스트: localhost (라즈베리파이에서 직접 실행하므로)
# 포트: 5432 (PostgreSQL 기본 포트)
# 데이터베이스이름: kims_db
SQLALCHEMY_DATABASE_URI = 'postgresql://kims_user:YOUR_PASSWORD@localhost:5432/kims_db'
# --- ★★★ YOUR_PASSWORD 부분을 실제 비밀번호로 꼭 변경해주세요! ★★★ ---

SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "your-very-secret-key" # 실제 운영 시에는 복잡한 키로 변경하세요.
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY') # .env 파일에서 로드되도록 유지