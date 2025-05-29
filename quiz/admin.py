"""
경로: quiz/admin.py
설명: 문제, 과목, 단원, 오답노트 등 학습 관련 관리자 등록
"""

from django.contrib import admin
from .models import Subject, Lesson, Question

admin.site.register(Subject)
admin.site.register(Lesson)
admin.site.register(Question)
