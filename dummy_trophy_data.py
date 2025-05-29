# dummy_trophy_data.py
# 실행: python manage.py shell < dummy_trophy_data.py

from trophies.models import Trophy

trophies = [
    # [트로피명, 설명, 조건 dict, 점수]
    ("첫발 내딛기", "처음으로 문제를 풀었을 때 주어지는 트로피", {"required_total_quiz": 1}, 100),
    ("문제풀이 달인", "문제풀이 10회를 달성했어요!", {"required_total_quiz": 10}, 150),
    ("백전백승!", "문제풀이 100회 달성!", {"required_total_quiz": 100}, 700),
    ("수학 첫걸음", "수학 문제를 처음 풀었을 때!", {"required_subject": "수학", "required_subject_quiz": 1}, 100),
    ("수학 10연승", "수학 문제를 10개 풀었어요!", {"required_subject": "수학", "required_subject_quiz": 10}, 250),
    ("수학 챌린저", "수학 문제 50개 풀기!", {"required_subject": "수학", "required_subject_quiz": 50}, 500),
    ("국어 첫사랑", "국어 문제를 처음 풀었어요!", {"required_subject": "국어", "required_subject_quiz": 1}, 100),
    ("국어 10점 만점", "국어 문제 10개 풀이 달성!", {"required_subject": "국어", "required_subject_quiz": 10}, 250),
    ("국어 달인", "국어 문제 100개 풀이 달성!", {"required_subject": "국어", "required_subject_quiz": 100}, 700),
    ("과학 탐험가", "과학 문제 풀이 첫 도전!", {"required_subject": "과학", "required_subject_quiz": 1}, 100),
    ("과학 덕후", "과학 문제 50개 풀었어요!", {"required_subject": "과학", "required_subject_quiz": 50}, 600),
    ("과학 만점왕", "과학 정답률 100%를 기록!", {"required_subject": "과학", "required_right_rate": 100}, 1200),
    ("사회 새싹", "사회 문제 첫 풀이!", {"required_subject": "사회", "required_subject_quiz": 1}, 100),
    ("사회 10연속!", "사회 문제 10개 풀이!", {"required_subject": "사회", "required_subject_quiz": 10}, 250),
    ("사회 마스터", "사회 문제 100개 풀이!", {"required_subject": "사회", "required_subject_quiz": 100}, 800),
    ("오답도 친구", "오답노트 10번 도전!", {"required_total_wrong": 10}, 250),
    ("오답 정복자", "오답노트 50개 극복!", {"required_total_wrong": 50}, 700),
    ("오답마스터", "오답노트 100개 극복!", {"required_total_wrong": 100}, 1300),
    ("연속출석 새싹", "3일 연속 출석!", {"required_streak": 3}, 150),
    ("출석 도전자", "7일 연속 출석!", {"required_streak": 7}, 300),
    ("출석의 달인", "30일 연속 출석!", {"required_streak": 30}, 1000),
    ("출석 신화", "100일 연속 출석!", {"required_streak": 100}, 3000),
    ("포인트 모으기", "누적 포인트 1000점 사용!", {"required_point_used": 1000}, 350),
    ("포인트 대부자", "누적 포인트 5000점 사용!", {"required_point_used": 5000}, 2000),
    ("트로피 헌터", "트로피 5개 모으기!", {"required_total_quiz": 15}, 300),
    ("문제풀기 열정맨", "문제풀이 300회 달성!", {"required_total_quiz": 300}, 1500),
    ("만렙 학습왕", "문제풀이 500회 달성!", {"required_total_quiz": 500}, 3000),
    ("학습 마라토너", "총 1000회 문제풀이 달성!", {"required_total_quiz": 1000}, 5000),
    ("하루 5분", "하루에 5분만 학습해도 쌓이는 트로피!", {"required_login_days": 5}, 100),
    ("주간 출석왕", "한 주(7일) 출석 성공!", {"required_login_days": 7}, 200),
    ("초코맛 포인트", "포인트 200 사용하면 초코맛 트로피!", {"required_point_used": 200}, 150),
    ("수학의 전설", "수학 문제 200개 풀기!", {"required_subject": "수학", "required_subject_quiz": 200}, 2000),
    ("국어 마에스트로", "국어 문제 200개 풀기!", {"required_subject": "국어", "required_subject_quiz": 200}, 2000),
    ("과학 영재", "과학 문제 200개 풀기!", {"required_subject": "과학", "required_subject_quiz": 200}, 2000),
    ("사회 탐험왕", "사회 문제 200개 풀기!", {"required_subject": "사회", "required_subject_quiz": 200}, 2000),
    ("공부의 신", "모든 과목 정답률 80% 이상 달성!", {"required_right_rate": 80}, 4000),
    ("작은 성취의 기쁨", "처음으로 트로피를 획득했다면!", {"required_total_quiz": 2}, 120),
    ("큰 성공의 기쁨", "트로피 20개 모으기!", {"required_total_quiz": 50}, 2000),
    ("최고의 노력상", "총 문제풀이 700회!", {"required_total_quiz": 700}, 4000),
    ("어드벤처 학습러", "학습기간 1개월 경과!", {"required_login_days": 30}, 900),
    ("미니게임 루키", "미니게임 첫 참가!", {"required_total_quiz": 3}, 120),
    ("미니게임 챔피언", "미니게임 50회 참가!", {"required_total_quiz": 50}, 900),
    ("정답왕", "정답률 90% 달성!", {"required_right_rate": 90}, 2500),
    ("열공 1등!", "하루 10문제 이상 풀이!", {"required_total_quiz": 10}, 160),
    ("친구와 함께", "학습 사이트 첫 친구 추가!", {"required_total_quiz": 1}, 120),
    ("100점 만점!", "문제풀이 100점 달성!", {"required_right_rate": 100}, 800),
    ("스페셜 포인트", "특별 보너스 포인트 300 사용!", {"required_point_used": 300}, 160),
    ("오답노트 챔피언", "오답노트 200개 극복!", {"required_total_wrong": 200}, 2500),
    ("트로피 대마왕", "트로피 30개 모으기!", {"required_total_quiz": 80}, 5000),
]

for idx, (name, description, cond, points) in enumerate(trophies, start=1):
    Trophy.objects.create(
        name=name,
        description=description,
        icon=f"https://cdn.jsdelivr.net/gh/schizos1/icons/trophy{idx}.png",
        grade="gold" if points >= 2000 else "silver" if points >= 1000 else "bronze",
        required_login_days=cond.get("required_login_days", 0),
        required_total_quiz=cond.get("required_total_quiz", 0),
        required_subject=cond.get("required_subject", ""),
        required_subject_quiz=cond.get("required_subject_quiz", 0),
        required_right_rate=cond.get("required_right_rate", 0),
        required_total_wrong=cond.get("required_total_wrong", 0),
        required_streak=cond.get("required_streak", 0),
        required_point_used=cond.get("required_point_used", 0),
        points=points
    )

print("🎉 50개 트로피 더미 데이터 입력 완료!")
