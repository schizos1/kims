# 경로: /home/schizos/study_site/dummy_trophy_data.py
# 실행: python manage.py shell < dummy_trophy_data.py

from trophies.models import Trophy
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
# import sys
# logging.basicConfig(stream=sys.stdout, level=logging.INFO) # 필요시 주석 해제

with transaction.atomic():
    logger.info("기존 트로피 데이터를 삭제합니다...")
    count_deleted, _ = Trophy.objects.all().delete()
    logger.info(f"기존 트로피 데이터 {count_deleted}개 삭제 완료.")

    # 각 트로피 데이터: [이름, 설명, 조건 dict, 포인트, 아이콘 URL]
    trophies_data_list = [
        ("첫발 내딛기", "처음으로 문제를 풀었을 때 주어지는 트로피", {"required_total_quiz": 1}, 100, "https://placehold.co/50x50/82E0AA/FFFFFF?text=Q1"),
        ("문제풀이 달인", "문제풀이 10회를 달성했어요!", {"required_total_quiz": 10}, 150, "https://placehold.co/50x50/76D7C4/FFFFFF?text=Q10"),
        ("백전백승!", "문제풀이 100회 달성!", {"required_total_quiz": 100}, 700, "https://placehold.co/50x50/5DADE2/FFFFFF?text=Q100"),
        ("수학 첫걸음", "수학 문제를 처음 풀었을 때!", {"required_subject": "수학", "required_subject_quiz": 1}, 100, "https://placehold.co/50x50/F7DC6F/000000?text=M1"),
        ("수학 10연승", "수학 문제를 10개 풀었어요!", {"required_subject": "수학", "required_subject_quiz": 10}, 250, "https://placehold.co/50x50/F5B041/FFFFFF?text=M10"),
        ("수학 챌린저", "수학 문제 50개 풀기!", {"required_subject": "수학", "required_subject_quiz": 50}, 500, "https://placehold.co/50x50/E67E22/FFFFFF?text=M50"),
        ("국어 첫사랑", "국어 문제를 처음 풀었어요!", {"required_subject": "국어", "required_subject_quiz": 1}, 100, "https://placehold.co/50x50/D2B48C/000000?text=K1"),
        ("국어 10점 만점", "국어 문제 10개 풀이 달성!", {"required_subject": "국어", "required_subject_quiz": 10}, 250, "https://placehold.co/50x50/CA6F1E/FFFFFF?text=K10"),
        ("국어 달인", "국어 문제 100개 풀이 달성!", {"required_subject": "국어", "required_subject_quiz": 100}, 700, "https://placehold.co/50x50/A0522D/FFFFFF?text=K100"),
        ("과학 탐험가", "과학 문제 풀이 첫 도전!", {"required_subject": "과학", "required_subject_quiz": 1}, 100, "https://placehold.co/50x50/AED6F1/000000?text=S1"),
        ("과학 덕후", "과학 문제 50개 풀었어요!", {"required_subject": "과학", "required_subject_quiz": 50}, 600, "https://placehold.co/50x50/85C1E9/FFFFFF?text=S50"),
        ("과학 만점왕", "과학 정답률 100%를 기록!", {"required_subject": "과학", "required_right_rate": 100}, 1200, "https://placehold.co/50x50/D2B4DE/000000?text=S%25"), # %25는 % 기호
        ("사회 새싹", "사회 문제 첫 풀이!", {"required_subject": "사회", "required_subject_quiz": 1}, 100, "https://placehold.co/50x50/A9DFBF/000000?text=SS1"),
        ("사회 10연속!", "사회 문제 10개 풀이!", {"required_subject": "사회", "required_subject_quiz": 10}, 250, "https://placehold.co/50x50/ABEBC6/000000?text=SS10"),
        ("사회 마스터", "사회 문제 100개 풀이!", {"required_subject": "사회", "required_subject_quiz": 100}, 800, "https://placehold.co/50x50/48C9B0/FFFFFF?text=SS100"),
        ("오답도 친구", "오답노트 10번 도전!", {"required_total_wrong": 10}, 250, "https://placehold.co/50x50/F1948A/FFFFFF?text=W10"),
        ("오답 정복자", "오답노트 50개 극복!", {"required_total_wrong": 50}, 700, "https://placehold.co/50x50/EC7063/FFFFFF?text=W50"),
        ("오답마스터", "오답노트 100개 극복!", {"required_total_wrong": 100}, 1300, "https://placehold.co/50x50/E74C3C/FFFFFF?text=W100"),
        ("연속출석 새싹", "3일 연속 출석!", {"required_streak": 3}, 150, "https://placehold.co/50x50/A9CCE3/000000?text=A3"),
        ("출석 도전자", "7일 연속 출석!", {"required_streak": 7}, 300, "https://placehold.co/50x50/AAB7B8/FFFFFF?text=A7"),
        ("출석의 달인", "30일 연속 출석!", {"required_streak": 30}, 1000, "https://placehold.co/50x50/909497/FFFFFF?text=A30"),
        ("출석 신화", "100일 연속 출석!", {"required_streak": 100}, 3000, "https://placehold.co/50x50/C0C0C0/000000?text=A100"),
        ("포인트 모으기", "누적 포인트 1000점 사용!", {"required_point_used": 1000}, 350, "https://placehold.co/50x50/F8C471/000000?text=P1k"),
        ("포인트 대부자", "누적 포인트 5000점 사용!", {"required_point_used": 5000}, 2000, "https://placehold.co/50x50/FFD700/000000?text=P5k"),
        ("트로피 헌터", "트로피 5개 모으기!", {"required_total_quiz": 15}, 300, "https://placehold.co/50x50/1ABC9C/FFFFFF?text=T5"), # 조건은 퀴즈15, 이름은 트로피5개
        ("문제풀기 열정맨", "문제풀이 300회 달성!", {"required_total_quiz": 300}, 1500, "https://placehold.co/50x50/2ECC71/FFFFFF?text=Q300"),
        ("만렙 학습왕", "문제풀이 500회 달성!", {"required_total_quiz": 500}, 3000, "https://placehold.co/50x50/27AE60/FFFFFF?text=Q500"),
        ("학습 마라토너", "총 1000회 문제풀이 달성!", {"required_total_quiz": 1000}, 5000, "https://placehold.co/50x50/1E8449/FFFFFF?text=Q1k"),
        ("하루 5분", "하루에 5분만 학습해도 쌓이는 트로피!", {"required_login_days": 5}, 100, "https://placehold.co/50x50/8E44AD/FFFFFF?text=D5"),
        ("주간 출석왕", "한 주(7일) 출석 성공!", {"required_login_days": 7}, 200, "https://placehold.co/50x50/9B59B6/FFFFFF?text=D7"),
        ("초코맛 포인트", "포인트 200 사용하면 초코맛 트로피!", {"required_point_used": 200}, 150, "https://placehold.co/50x50/7B5107/FFFFFF?text=ChocoP"),
        ("수학의 전설", "수학 문제 200개 풀기!", {"required_subject": "수학", "required_subject_quiz": 200}, 2000, "https://placehold.co/50x50/D35400/FFFFFF?text=M200"),
        ("국어 마에스트로", "국어 문제 200개 풀기!", {"required_subject": "국어", "required_subject_quiz": 200}, 2000, "https://placehold.co/50x50/873600/FFFFFF?text=K200"),
        ("과학 영재", "과학 문제 200개 풀기!", {"required_subject": "과학", "required_subject_quiz": 200}, 2000, "https://placehold.co/50x50/5B2C6F/FFFFFF?text=S200"),
        ("사회 탐험왕", "사회 문제 200개 풀기!", {"required_subject": "사회", "required_subject_quiz": 200}, 2000, "https://placehold.co/50x50/117A65/FFFFFF?text=SS200"),
        ("공부의 신", "모든 과목 정답률 80% 이상 달성!", {"required_right_rate": 80}, 4000, "https://placehold.co/50x50/F1C40F/000000?text=GOD"),
        ("작은 성취의 기쁨", "처음으로 트로피를 획득했다면!", {"required_total_quiz": 2}, 120, "https://placehold.co/50x50/7DCEA0/000000?text=JoyS"),
        ("큰 성공의 기쁨", "트로피 20개 모으기!", {"required_total_quiz": 50}, 2000, "https://placehold.co/50x50/F39C12/FFFFFF?text=JoyB"), # 조건은 퀴즈50
        ("최고의 노력상", "총 문제풀이 700회!", {"required_total_quiz": 700}, 4000, "https://placehold.co/50x50/16A085/FFFFFF?text=BestE"),
        ("어드벤처 학습러", "학습기간 1개월 경과!", {"required_login_days": 30}, 900, "https://placehold.co/50x50/2980B9/FFFFFF?text=AdvL"),
        ("미니게임 루키", "미니게임 첫 참가!", {"required_total_quiz": 3}, 120, "https://placehold.co/50x50/3498DB/FFFFFF?text=MGR"),
        ("미니게임 챔피언", "미니게임 50회 참가!", {"required_total_quiz": 50}, 900, "https://placehold.co/50x50/2471A3/FFFFFF?text=MGC"),
        ("정답왕", "정답률 90% 달성!", {"required_right_rate": 90}, 2500, "https://placehold.co/50x50/F9E79F/000000?text=AnsK"),
        ("열공 1등!", "하루 10문제 이상 풀이!", {"required_total_quiz": 10}, 160, "https://placehold.co/50x50/17A589/FFFFFF?text=TopS"),
        ("친구와 함께", "학습 사이트 첫 친구 추가!", {"required_total_quiz": 1}, 120, "https://placehold.co/50x50/5499C7/FFFFFF?text=Friend"),
        ("100점 만점!", "문제풀이 100점 달성!", {"required_right_rate": 100}, 800, "https://placehold.co/50x50/F8E258/000000?text=100%25"),
        ("스페셜 포인트", "특별 보너스 포인트 300 사용!", {"required_point_used": 300}, 160, "https://placehold.co/50x50/EB984E/FFFFFF?text=SPP"),
        ("오답노트 챔피언", "오답노트 200개 극복!", {"required_total_wrong": 200}, 2500, "https://placehold.co/50x50/CB4335/FFFFFF?text=W200C"),
        ("트로피 대마왕", "트로피 30개 모으기!", {"required_total_quiz": 80}, 5000, "https://placehold.co/50x50/000000/FFD700?text=Boss"), # 조건은 퀴즈80
    ]

    logger.info(f"{len(trophies_data_list)}개 트로피 데이터 생성을 시작합니다...")

    for idx, trophy_data_item in enumerate(trophies_data_list, start=1):
        name, description, cond_dict, points_val = trophy_data_item[0], trophy_data_item[1], trophy_data_item[2], trophy_data_item[3]
        # 아이콘 URL은 이제 리스트의 5번째 항목에서 가져옴
        icon_url = trophy_data_item[4] if len(trophy_data_item) > 4 and trophy_data_item[4] else f"https://placehold.co/50x50/EEEEEE/333333?text=T{idx}" # 기본값

        current_condition_type = None
        current_condition_value = 0
        current_required_subject = cond_dict.get("required_subject", "")

        if "required_login_days" in cond_dict:
            current_condition_type = "login_days"
            current_condition_value = cond_dict["required_login_days"]
        elif "required_total_quiz" in cond_dict:
            current_condition_type = "total_quiz"
            current_condition_value = cond_dict["required_total_quiz"]
        elif "required_subject_quiz" in cond_dict:
            current_condition_type = "subject_quiz"
            current_condition_value = cond_dict["required_subject_quiz"]
        elif "required_right_rate" in cond_dict:
            current_condition_type = "right_rate"
            current_condition_value = cond_dict["required_right_rate"]
        elif "required_total_wrong" in cond_dict:
            current_condition_type = "total_wrong"
            current_condition_value = cond_dict["required_total_wrong"]
        elif "required_streak" in cond_dict:
            current_condition_type = "streak"
            current_condition_value = cond_dict["required_streak"]
        elif "required_point_used" in cond_dict:
            current_condition_type = "point_used"
            current_condition_value = cond_dict["required_point_used"]
        
        if not current_condition_type:
            logger.warning(f"경고: '{name}' 트로피의 condition_type을 결정할 수 없습니다. cond_dict: {cond_dict}. 모델의 기본값을 사용합니다.")

        Trophy.objects.create(
            name=name,
            description=description,
            icon=icon_url, # 여기서 개별 아이콘 URL 사용
            sound_effect=f"placeholder_sound_effect_for_trophy_{idx}.mp3", # 임시 사운드 URL (필요시 실제 URL로 교체)
            condition_type=current_condition_type, 
            condition_value=current_condition_value,
            required_subject=current_required_subject,
            points=points_val
        )
        log_condition_type = current_condition_type if current_condition_type else Trophy._meta.get_field('condition_type').get_default()
        log_condition_value = current_condition_value if current_condition_type else Trophy._meta.get_field('condition_value').get_default()
        logger.info(f"  - '{name}' 트로피 생성 완료 (Icon: {icon_url}, Type: {log_condition_type}, Value: {log_condition_value}, Subject: '{current_required_subject if current_required_subject else 'N/A'}')")

    logger.info(f"🎉 {len(trophies_data_list)}개 트로피 더미 데이터 입력 완료!")

print("더미 데이터 스크립트 실행이 Django 셸로 전달되었습니다. 위 로그를 확인하세요.")