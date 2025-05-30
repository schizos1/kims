"""
과목 더미 데이터 자동 입력 스크립트
- 필수/선택 과목 총 10개 등록 (중복 체크)
- python manage.py shell < create_subjects.py 로 실행
"""

from quiz.models import Subject

subject_names = [
    "국어", "수학", "사회", "과학",      # 필수 4과목
    "도덕", "체육", "음악", "미술", "실과", "영어"   # 선택 6과목
]

for name in subject_names:
    subj, created = Subject.objects.get_or_create(name=name)
    print(f"{'생성됨' if created else '이미 있음'}: {name}")
