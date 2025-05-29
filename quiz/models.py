"""
quiz/models.py
- 과목, 단원, 문제(개념/기출), 오답노트, 풀이로그 모델
"""

from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    """과목: 수학, 과학, 국어 등"""
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Lesson(models.Model):
    """
    단원 (개념문제용)
    - subject: 과목
    - unit_name: 단원명
    - grade: 학년(필요시)
    - concept: 개념설명(텍스트)
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    unit_name = models.CharField(max_length=100)
    grade = models.CharField(max_length=10, blank=True)
    concept = models.TextField(blank=True)

    def __str__(self):
        return f"{self.subject.name}-{self.unit_name}({self.grade})"

class Question(models.Model):
    """
    문제 (개념문제/기출문제 모두)
    - question_type: "concept" or "past"
    - lesson: 개념문제만 연결, 기출문제는 null
    - year, number: 기출문제만 사용
    - text/image: 문제 본문/이미지
    - choiceN_text/image: 4지선다 객관식(이미지 필드 포함)
    - answer: 정답(1~4)
    - explanation/explanation_image: 해설/해설이미지
    """
    QUESTION_TYPE_CHOICES = [
        ('concept', '개념문제'),
        ('past', '기출문제'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES)
    year = models.CharField(max_length=10, blank=True)
    number = models.CharField(max_length=10, blank=True)
    text = models.TextField()
    image = models.URLField(blank=True)
    choice1_text = models.CharField(max_length=200)
    choice1_image = models.URLField(blank=True)
    choice2_text = models.CharField(max_length=200)
    choice2_image = models.URLField(blank=True)
    choice3_text = models.CharField(max_length=200)
    choice3_image = models.URLField(blank=True)
    choice4_text = models.CharField(max_length=200)
    choice4_image = models.URLField(blank=True)
    answer = models.IntegerField()
    explanation = models.TextField(blank=True)
    explanation_image = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.subject}] {self.text[:20]}..."

class UserAnswerLog(models.Model):
    """
    학생 풀이 기록 (문제풀이 로그)
    - user: 학생
    - question: 문제
    - user_answer: 선택한 답(번호)
    - is_correct: 정답여부
    - timestamp: 제출시각
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_answer = models.IntegerField()
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class WrongAnswer(models.Model):
    """
    오답노트 기록 (틀린 문제)
    - user: 학생
    - question: 문제
    - created_at: 오답 등록 시각
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
