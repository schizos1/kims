# 📚 초등 학습 시스템 구조 문서 (Codex용)

## 1. 프로젝트 개요

- **목표**: 초등 검정고시 학습 시스템
- **주요 기능**: 문제 풀이, 개념 학습, 트로피 지급, 미니게임, 포인트 관리
- **백엔드**: Django + PostgreSQL (scram-sha-256 인증 사용)
- **프론트엔드**: Bootstrap, JS (미니게임 포함)
- **환경**: Ubuntu 22.04, Python 3.12, Intel N100

---

## 2. 주요 폴더 구조

```plaintext
├── core/
│   ├── models.py         # 주요 모델 정의
│   ├── views.py          # 기본 뷰
│   ├── views_quiz.py     # 퀴즈용 뷰
│   ├── views_learn.py    # 개념 학습용 뷰
│   ├── services/         # 서비스 계층
│   │   ├── quiz_service.py
│   │   └── trophy_service.py
│   └── utils.py          # 공통 유틸
├── users/
│   ├── models.py         # 사용자 프로필/역할
│   └── views.py
├── trophies/
│   ├── models.py         # 트로피 DB
│   ├── signals.py        # 로그인/활동 시 트로피 자동 지급
│   └── views.py
├── quiz/
│   ├── models.py         # 문제/기록/오답노트
│   └── views.py
├── minigame/
│   ├── static/js/fishing/
│   │   ├── main.js
│   │   └── scenes/
│   └── templates/minigame/
├── templates/
├── static/
├── manage.py
```

---

## 3. DB 주요 테이블

- **User (users_userprofile)**: 로그인, 연속 로그인, 포인트
- **Question (quiz_question)**: 객관식 4지선다, 이미지 포함
- **UserAnswerLog / WrongAnswer**: 정답/오답 기록
- **ConceptLesson**: 개념 설명 + 문제 자동 생성 대상
- **Trophy**: 조건, 포인트, 이미지, 설명 포함

---

## 4. 미니게임 연동 구조

- 경로: `/static/js/fishing/`
- 상태 저장 없이 실행 → 점수 기록 시 `UserAnswerLog` 또는 `Trophy`에 반영
- 미니게임 조건 해금, 포인트 소비, 트로피 지급 등은 DB에 연동

---

## 5. 필요한 라이브러리 (requirements.txt)

```plaintext
Django==5.2.1
psycopg[binary]==3.1.18
gunicorn
Pillow
python-dotenv
```

---

## 6. 기타 설정

- `.env`에 DB 접속정보, 비밀키 등 포함
- `settings.py`는 PostgreSQL 기준 설정 유지
- `cat <<EOF` 형식으로 서버 구성 자동화

---

✅ 이 구조 문서를 Codex 설명 문서로 저장하면, 모든 기능 설명/참조에 활용할 수 있습니다.
