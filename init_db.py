# init_db.py

from app import create_app, db
from app.models import User, Trophy # Trophy 모델 임포트 추가
from werkzeug.security import generate_password_hash

# 사용할 트로피 데이터 리스트
PRECONFIGURED_TROPHIES_DATA = [
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

app = create_app()

with app.app_context():
    # 데이터베이스 테이블이 없다면 모두 생성
    db.create_all()
    print("--- DEBUG: init_db.py - db.create_all() 호출됨 ---")

    # 관리자 사용자 생성
    if not User.query.filter_by(username='admin').first():
        hashed_password = generate_password_hash('admin', method='pbkdf2:sha256')
        new_admin = User(username='admin', password=hashed_password, role='admin')
        db.session.add(new_admin)
        print("관리자 'admin' 사용자를 생성했습니다.")

    # 학생 사용자 생성
    if not User.query.filter_by(username='gimrin').first():
        hashed_password = generate_password_hash('1234', method='pbkdf2:sha256')
        new_gimrin = User(username='gimrin', password=hashed_password, role='student')
        db.session.add(new_gimrin)
        print("학생 'gimrin' 사용자를 생성했습니다.")

    if not User.query.filter_by(username='gimik').first():
        hashed_password = generate_password_hash('1234', method='pbkdf2:sha256')
        new_gimik = User(username='gimik', password=hashed_password, role='student')
        db.session.add(new_gimik)
        print("학생 'gimik' 사용자를 생성했습니다.")
    
    # 초기 트로피 데이터 생성
    print("\n기본 트로피 데이터 설정 시작...")
    for trophy_data in PRECONFIGURED_TROPHIES_DATA:
        trophy = Trophy.query.get(trophy_data['id'])
        if not trophy:
            new_trophy = Trophy(**trophy_data)
            db.session.add(new_trophy)
            print(f"Added trophy to DB: {new_trophy.name}")
        else: # 이미 있으면 정보 업데이트 (선택적)
            trophy.name = trophy_data['name']
            trophy.description = trophy_data['description']
            trophy.icon_class = trophy_data['icon_class']
            trophy.points = trophy_data['points']
            print(f"Updated trophy in DB: {trophy.name}")

    try:
        db.session.commit()
        print("\n모든 사용자 및 트로피 초기 데이터베이스 설정이 완료되었습니다.")
    except Exception as e:
        db.session.rollback()
        print(f"\n초기 데이터 설정 중 DB 커밋 오류: {e}")