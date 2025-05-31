# 경로: /home/schizos/study_site/quiz/admin.py
"""퀴즈 앱의 관리자 모듈로, 모델을 Django 관리자에 등록합니다."""
from django.contrib import admin
from .models import Subject, Lesson, Question, UserAnswerLog, WrongAnswer

admin.site.register(Subject)
admin.site.register(Lesson)
admin.site.register(Question)
admin.site.register(UserAnswerLog)
admin.site.register(WrongAnswer)