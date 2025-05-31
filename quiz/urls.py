# 경로: /home/schizos/study_site/quiz/urls.py
"""퀴즈 앱의 URL 패턴을 정의합니다.

이 모듈은 퀴즈 관련 뷰(개념문제, 기출문제, 오답노트 등)에 대한 URL 매핑을 제공합니다.
"""
from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # 개념문제 선택 페이지
    path('concept_select/', views.concept_select, name='concept_select'),
    # 기출문제 선택 페이지
    path('past_select/', views.past_select, name='past_select'),
    # 개념문제 과목 목록
    path('concept/subject/', views.concept_subject_list, name='concept_subject_list'),
    # 개념문제 단원 목록
    path('concept/lesson/<int:subject_id>/', views.concept_lesson_list, name='concept_lesson_list'),
    # 개념문제 문제 목록
    path('concept/question/<int:subject_id>/<int:lesson_id>/', views.concept_question_list, name='concept_question_list'),
    # 기출문제 단원 목록
    path('past/lesson/<int:subject_id>/', views.past_lesson_list, name='past_lesson_list'),
    # 기출문제 문제 목록
    path('past/question/<int:subject_id>/<int:lesson_id>/', views.past_question_list, name='past_question_list'),
    # 답변 제출 처리
    path('submit/<int:subject_id>/<int:lesson_id>/', views.submit_answers, name='submit_answers'),
    # 오답노트 목록
    path('wrong_note_list/', views.wrong_note_list, name='wrong_note_list'),
    # 오답노트 문제풀이
    path('wrong_note/<int:subject_id>/<int:lesson_id>/', views.wrong_note_quiz, name='wrong_note_quiz'),
    # 오답노트 단일 문제 재도전
    path('retry/<int:question_id>/', views.retry_question, name='retry_question'),

    path('admin-bulk-upload/', views.admin_bulk_question_upload, name='admin_bulk_question_upload'),
]