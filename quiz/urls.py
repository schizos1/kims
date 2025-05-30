"""
quiz/urls.py
- 퀴즈(문제풀이) 관련 URL 라우팅
- 개념/기출문제, 과목/단원/문제 등 핵심 흐름 연결
"""
from django.urls import path
from . import views

urlpatterns = [
    # 문제유형 선택(개념/기출)
    path('concept_select/', views.concept_select, name='concept_select'),

    # 개념문제: 과목 선택
    path('concept/subject/', views.concept_subject_list, name='concept_subject_list'),

    # 개념문제: 단원 선택
    path('concept/subject/<int:subject_id>/lessons/', views.concept_lesson_list, name='concept_lesson_list'),

    # 개념문제: 문제 리스트
    path('concept/subject/<int:subject_id>/lesson/<int:lesson_id>/', views.concept_question_list, name='concept_question_list'),

    # 제출 처리 (POST) - 답안 제출 후 채점용
    path('submit_answers/<int:subject_id>/<int:lesson_id>/', views.submit_answers, name='submit_answers'),

    # 오답노트 메인 리스트
    path('wrong_note/', views.wrong_note_list, name='wrong_note_list'),

    # 오답노트 문제풀이
    path('wrong_note/subject/<int:subject_id>/lesson/<int:lesson_id>/', views.wrong_note_quiz, name='wrong_note_quiz'),

    # 기출문제도 동일한 패턴으로 확장 가능
    # path('past/subject/', ...),
]
