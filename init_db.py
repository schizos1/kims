# init_db.py

from app import create_app, db
from app.models import User, Trophy, PromptTemplate # ★★★ PromptTemplate 모델 임포트 추가 ★★★
from werkzeug.security import generate_password_hash
from textwrap import dedent # 프롬프트 작성을 위해 추가

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

# --- ★★★ 기본 프롬프트 템플릿 데이터 정의 ★★★ ---
DEFAULT_PROMPT_TEMPLATES_DATA = [
    {
        'name': '초등 수학 객관식 문제 생성 프롬프트',
        'subject_id': None, # None이면 특정 과목 전용이 아님, 또는 관리자가 나중에 지정
        'prompt_text': dedent("""
            당신은 대한민국 초등학생을 가르치는 친절하고 유능한 '{{ subject_name }}' 과목 선생님입니다.
            '{{ subject_name }}' 과목의 초등 교육과정 및 검정고시 준비에 맞춰, '{{ concept_name }}' 라는 개념에 대한 학습 콘텐츠를 생성해주세요.
            출력은 반드시 아래의 지정된 형식으로만 제공해야 합니다.

            [STEP]
            Title: <학습 단계의 소제목>
            Explanation: <해당 단계에 대한 상세하고 친절한 설명. 아이들이 이해하기 쉬운 말투로 작성해주세요. 줄바꿈이 필요하면 실제 줄바꿈을 사용하세요.>
            (위 [STEP] 블록을 개념 이해에 필요한 만큼 반복해주세요. 최소 2개 이상 생성해주세요.)

            [EXAMPLE_QUESTIONS]
            # 객관식 문제 10개를 만들어주세요. 각 문제는 질문(Q), 4개의 보기 (O1, O2, O3, O4), 그리고 정답 보기의 번호(A)를 포함해야 합니다.
            # 생성되는 모든 문제와 보기, 특히 정답은 문법적, 내용적으로 반드시 정확해야 합니다.
            # 문제와 문제 사이에는 빈 줄을 한 줄 넣어주세요.
            # 예시 형식 (실제 생성 시에는 이 예시를 그대로 사용하지 마세요):
            # Q: 2 + 3 = ?
            # O1: 4
            # O2: 5
            # O3: 6
            # O4: 7
            # A: 2
            
            (이런 식으로 Q/O1-O4/A 쌍을 총 10개 생성)
        """),
        'notes': '수학 또는 계산 관련 과목의 객관식 문제 생성에 사용됩니다.',
        'is_default_for_subject': False # 특정 과목의 기본값으로 사용하려면 True로 하고 subject_id 설정
    },
    {
        'name': '초등 일반 과목 문제 생성 프롬프트 (객관식/주관식 혼합)',
        'subject_id': None,
        'prompt_text': dedent("""
            당신은 대한민국 초등학생을 가르치는 친절하고 유능한 '{{ subject_name }}' 과목 선생님입니다.
            '{{ subject_name }}' 과목의 초등 교육과정 및 검정고시 준비에 맞춰, '{{ concept_name }}' 라는 개념에 대한 학습 콘텐츠를 생성해주세요.
            출력은 반드시 아래의 지정된 형식으로만 제공해야 합니다.

            [STEP]
            Title: <학습 단계의 소제목>
            Explanation: <해당 단계에 대한 상세하고 친절한 설명. 아이들이 이해하기 쉬운 말투로 작성해주세요. 줄바꿈이 필요하면 실제 줄바꿈을 사용하세요.>
            (위 [STEP] 블록을 개념 이해에 필요한 만큼 반복해주세요. 최소 2개 이상 생성해주세요.)

            [EXAMPLE_QUESTIONS]
            # 이 개념을 이해했는지 확인할 수 있는 다양한 유형의 총 10개 예제 문제와 그에 대한 정답 또는 모범 답안을 제공해주세요. 객관식 문제(Q, O1, O2, O3, O4, A 형식)와 단답형 주관식 문제(Q, A 형식)를 섞어도 좋습니다.
            # 생성되는 모든 문제와 보기, 특히 정답은 문법적, 내용적으로 반드시 정확해야 합니다.
            # 문제와 문제 사이에는 빈 줄을 한 줄 넣어주세요.
            # 예시 형식 (실제 생성 시에는 이 예시를 그대로 사용하지 마세요):
            # 예시 1 (객관식):
            # Q: 다음 중 식물의 광합성에 필요한 요소가 아닌 것은 무엇일까요?
            # O1: 햇빛
            # O2: 물
            # O3: 이산화탄소
            # O4: 바람
            # A: 4
            #
            # 예시 2 (단답형):
            # Q: 물이 얼음으로 변하는 현상을 무엇이라고 하나요?
            # A: 응고
            
            (이런 식으로 Q/A 또는 Q/O1-O4/A 쌍을 총 10개 생성)
        """),
        'notes': '국어, 과학, 사회 등 일반 과목의 문제 생성에 사용됩니다. 객관식과 주관식을 혼합하여 요청합니다.',
        'is_default_for_subject': False
    }
]
# --- 기본 프롬프트 템플릿 데이터 정의 끝 ---


app = create_app()

with app.app_context():
    db.create_all()
    print("--- DEBUG: init_db.py - db.create_all() 호출됨 ---")

    # 사용자 생성 로직 (이전과 동일)
    if not User.query.filter_by(username='admin').first():
        hashed_password = generate_password_hash('admin', method='pbkdf2:sha256')
        new_admin = User(username='admin', password=hashed_password, role='admin')
        db.session.add(new_admin)
        print("관리자 'admin' 사용자를 생성했습니다.")
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
    
    # 트로피 데이터 생성 로직 (이전과 동일)
    print("\n기본 트로피 데이터 설정 시작...")
    for trophy_data in PRECONFIGURED_TROPHIES_DATA:
        trophy = Trophy.query.get(trophy_data['id'])
        if not trophy:
            new_trophy = Trophy(**trophy_data)
            db.session.add(new_trophy)
            print(f"Added trophy to DB: {new_trophy.name}")
        else:
            trophy.name = trophy_data['name']
            trophy.description = trophy_data['description']
            trophy.icon_class = trophy_data['icon_class']
            trophy.points = trophy_data['points']
            # Trophy 모델에 condition 필드들이 추가되었으므로, 기존 데이터 업데이트 시 에러 방지
            trophy.condition_type = trophy.condition_type # 기존 값 유지 또는 None
            trophy.condition_value_int = trophy.condition_value_int
            trophy.condition_value_str = trophy.condition_value_str
            trophy.is_active = trophy.is_active
            print(f"Updated trophy in DB: {trophy.name}")

    # --- ★★★ 기본 프롬프트 템플릿 데이터 추가 로직 ★★★ ---
    print("\n기본 프롬프트 템플릿 데이터 설정 시작...")
    for pt_data in DEFAULT_PROMPT_TEMPLATES_DATA:
        prompt_template = PromptTemplate.query.filter_by(name=pt_data['name']).first()
        if not prompt_template:
            new_pt = PromptTemplate(
                name=pt_data['name'],
                subject_id=pt_data.get('subject_id'), # subject_id가 없을 수 있으므로 .get() 사용
                prompt_text=pt_data['prompt_text'],
                notes=pt_data.get('notes'),
                is_default_for_subject=pt_data.get('is_default_for_subject', False)
            )
            db.session.add(new_pt)
            print(f"Added prompt template to DB: {new_pt.name}")
        else: # 이미 있으면 내용 업데이트 (선택적)
            prompt_template.prompt_text = pt_data['prompt_text']
            prompt_template.notes = pt_data.get('notes')
            prompt_template.is_default_for_subject = pt_data.get('is_default_for_subject', False)
            prompt_template.subject_id = pt_data.get('subject_id')
            print(f"Updated prompt template in DB: {prompt_template.name}")
    # --- 기본 프롬프트 템플릿 데이터 추가 로직 끝 ---

    try:
        db.session.commit()
        print("\n모든 사용자, 트로피, 및 기본 프롬프트 초기 데이터베이스 설정이 완료되었습니다.")
    except Exception as e:
        db.session.rollback()
        print(f"\n초기 데이터 설정 중 DB 커밋 오류: {e}")