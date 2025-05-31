"""퀴즈 앱의 모델 모듈로, 질문과 사용자 답변 로그를 정의합니다.

이 모듈은 퀴즈 콘텐츠와 사용자 답변, 오답 기록을 관리합니다.
"""
from django.db import models
from django.conf import settings

class Subject(models.Model):
    """과목 모델, 수학, 과학, 국어 등을 정의합니다.

    Attributes:
        name: 과목 이름, 최대 50자
    """
    name = models.CharField(max_length=50, verbose_name="과목 이름")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'quiz_subject'
        verbose_name = "과목"
        verbose_name_plural = "과목 목록"

class Lesson(models.Model):
    """단원 모델, 개념문제 및 기출문제 단원을 정의합니다.

    Attributes:
        subject: 연결된 과목 (ForeignKey)
        unit_name: 단원 이름, 최대 100자
        grade: 학년, 선택적
        concept: 개념 설명 텍스트, 선택적
    """
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name="과목"
    )
    unit_name = models.CharField(max_length=100, verbose_name="단원 이름")
    grade = models.CharField(max_length=10, blank=True, verbose_name="학년")
    concept = models.TextField(blank=True, verbose_name="개념 설명")

    def __str__(self):
        return f"{self.subject.name}-{self.unit_name}({self.grade})"

    class Meta:
        db_table = 'quiz_lesson'
        verbose_name = "단원"
        verbose_name_plural = "단원 목록"

class Question(models.Model):
    """문제 모델, 개념문제와 기출문제를 모두 포함합니다.

    Attributes:
        question_type: 'concept' 또는 'past'
        lesson: 개념 또는 기출 단원 연결, null 가능
        year: 기출문제 연도, 선택적
        number: 기출문제 번호, 선택적
        text: 문제 본문
        image: 문제 이미지 URL, 선택적
        choiceN_text: 4지선다 텍스트
        choiceN_image: 4지선다 이미지 URL, 선택적
        answer: 정답 번호(1~4)
        explanation: 해설 텍스트, 선택적
        explanation_image: 해설 이미지 URL, 선택적
    """
    QUESTION_TYPE_CHOICES = [
        ('concept', '개념문제'),
        ('past', '기출문제'),
    ]
    subject = models.ForeignKey( # Question 모델에 Subject 직접 연결
        'Subject',
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="과목"
    )
    lesson = models.ForeignKey(
        'Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        verbose_name="단원"
    )
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPE_CHOICES,
        verbose_name="문제 유형"
    )
    year = models.CharField(max_length=10, blank=True, verbose_name="기출 연도")
    number = models.CharField(max_length=10, blank=True, verbose_name="문제 번호")
    text = models.TextField(verbose_name="문제 본문")
    image = models.URLField(null=True, blank=True, default='', verbose_name="문제 이미지 URL")
    choice1_text = models.CharField(max_length=200, verbose_name="선택지 1 텍스트")
    choice1_image = models.URLField(null=True, blank=True, default='', verbose_name="선택지 1 이미지 URL")
    choice2_text = models.CharField(max_length=200, verbose_name="선택지 2 텍스트")
    choice2_image = models.URLField(null=True, blank=True, default='', verbose_name="선택지 2 이미지 URL")
    choice3_text = models.CharField(max_length=200, verbose_name="선택지 3 텍스트")
    choice3_image = models.URLField(null=True, blank=True, default='', verbose_name="선택지 3 이미지 URL")
    choice4_text = models.CharField(max_length=200, verbose_name="선택지 4 텍스트")
    choice4_image = models.URLField(null=True, blank=True, default='', verbose_name="선택지 4 이미지 URL")
    answer = models.IntegerField(verbose_name="정답 번호")
    explanation = models.TextField(null=True, blank=True, default='', verbose_name="해설")
    explanation_image = models.URLField(null=True, blank=True, default='', verbose_name="해설 이미지 URL")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    def __str__(self):
        return f"[{self.subject.name if self.subject else 'N/A'}] {self.text[:20]}..."

    class Meta:
        db_table = 'quiz_question'
        verbose_name = "문제"
        verbose_name_plural = "문제 목록"

class UserAnswerLog(models.Model):
    """학생 풀이 기록 모델, 문제풀이 로그를 저장합니다.

    Attributes:
        user: 학생 (ForeignKey)
        question: 문제 (ForeignKey)
        user_answer: 선택한 답 번호
        is_correct: 정답 여부
        timestamp: 제출 시각
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answer_logs',
        verbose_name="사용자"
    )
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        related_name='answer_logs',
        verbose_name="문제"
    )
    user_answer = models.IntegerField(verbose_name="선택한 답 번호")
    is_correct = models.BooleanField(default=False, verbose_name="정답 여부")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="제출 시간")

    class Meta:
        db_table = 'quiz_useranswerlog'
        # unique_together = ('user', 'question') # 복습 기능 시 여러 번 풀이 기록을 남기려면 이 줄을 주석 처리하거나 삭제해야 합니다.
        verbose_name = "사용자 답변 로그"
        verbose_name_plural = "사용자 답변 로그 목록"

    def __str__(self):
        return f"{self.user.username} - Q{self.question.id if self.question else 'N/A'} - {self.is_correct}"

class WrongAnswer(models.Model):
    """오답노트 기록 모델, 틀린 문제를 저장합니다.

    Attributes:
        user: 학생 (ForeignKey)
        question: 문제 (ForeignKey)
        created_at: 오답 등록 시각
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wrong_answers',
        verbose_name="사용자"
    )
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        related_name='wrong_answers',
        verbose_name="문제"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="등록 시간")

    class Meta:
        db_table = 'quiz_wronganswer'
        unique_together = ('user', 'question')
        verbose_name = "오답 기록"
        verbose_name_plural = "오답 기록 목록"

    def __str__(self):
        return f"{self.user.username} - Q{self.question.id if self.question else 'N/A'}"