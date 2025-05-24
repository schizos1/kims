# init_db.py

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

# create_app()을 호출하여 Flask 애플리케이션 컨텍스트를 사용합니다.
app = create_app()

with app.app_context():
    # 데이터베이스 테이블이 없다면 모두 생성합니다.
    db.create_all()

    # 관리자 사용자 생성 (없을 경우에만)
    if not User.query.filter_by(username='admin').first():
        # 'admin'이라는 비밀번호를 암호화합니다.
        hashed_password = generate_password_hash('admin', method='pbkdf2:sha256')
        new_admin = User(username='admin', password=hashed_password, role='admin')
        db.session.add(new_admin)
        print("관리자 'admin' 사용자를 생성했습니다. (비밀번호: admin)")

    # 학생 'gimrin' 생성 (없을 경우에만)
    if not User.query.filter_by(username='gimrin').first():
        # 학생은 버튼 로그인을 하지만, 만약을 위해 간단한 비밀번호를 설정합니다.
        hashed_password = generate_password_hash('1234', method='pbkdf2:sha256')
        new_gimrin = User(username='gimrin', password=hashed_password, role='student')
        db.session.add(new_gimrin)
        print("학생 'gimrin' 사용자를 생성했습니다.")

    # 학생 'gimik' 생성 (없을 경우에만)
    if not User.query.filter_by(username='gimik').first():
        hashed_password = generate_password_hash('1234', method='pbkdf2:sha256')
        new_gimik = User(username='gimik', password=hashed_password, role='student')
        db.session.add(new_gimik)
        print("학생 'gimik' 사용자를 생성했습니다.")

    # 변경사항을 데이터베이스에 최종 저장합니다.
    db.session.commit()
    print("초기 사용자 데이터베이스 설정 완료.")