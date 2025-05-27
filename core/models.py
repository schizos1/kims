# ============================================
# 📄 FILE: core/models.py
# 📝 DESCRIPTION: 사용자, 문제, 학습 개념, 자동 생성용 모델 정의
# ============================================

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# ✅ 사용자 모델
class User(AbstractUser):
    role = models.CharField(max_length=10, default='student')
    total_point = models.IntegerField(default=0)


# ✅ 문제 모델
class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('past', '기출문제'),
        ('concept', '개념문제'),
    ]

    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES)
    subject = models.CharField(max_length=50)
    topic = models.CharField(max_length=100, blank=True)
    prompt_description = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    question_text = models.TextField()
    image_url = models.URLField(blank=True)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_answer = models.PositiveSmallIntegerField()
    answer_image_url = models.URLField(blank=True)
    is_editable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ ConceptLesson 연결 (Inline 기능용)
    concept = models.ForeignKey("ConceptLesson", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.subject} - {self.topic or 'No Topic'}"


# ✅ 오답 기록 모델
class WrongAnswer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answered_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - 오답: {self.question.id}"


# ✅ 문제 풀이 기록 모델
class UserAnswerLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.PositiveSmallIntegerField()
    is_correct = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    viewed_explanation = models.BooleanField(default=False)

    def __str__(self):
        result = "정답" if self.is_correct else "오답"
        return f"{self.user.username} - {result}: {self.question.id}"


# 🔽 [개념 학습 + 프롬프트 자동 생성용 모델] 🔽

class PromptTemplate(models.Model):
    subject = models.CharField(max_length=50)
    title = models.CharField(max_length=100)
    prompt_text = models.TextField(help_text="예: {{ concept_text }} 등을 포함한 템플릿")

    def __str__(self):
        return f"{self.subject} - {self.title}"


class ConceptLesson(models.Model):
    subject = models.CharField(max_length=50)
    grade = models.IntegerField()
    unit_title = models.CharField(max_length=100)
    concept_text = models.TextField()
    explanation = models.TextField()
    image_url = models.URLField(blank=True, null=True)

    prompt_template = models.ForeignKey(PromptTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    is_generated = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.subject}] {self.unit_title} (G{self.grade})"

# ============================================
# 📄 FILE: core/models.py (트로피 관련 추가)
# ============================================

from django.db import models
from django.conf import settings

class Trophy(models.Model):
    TROPHY_TYPE_CHOICES = [
        ('activity', '활동량'),
        ('correct', '정답수'),
        ('wrong', '오답정정'),
    ]

    name = models.CharField(max_length=100)
    trophy_type = models.CharField(max_length=20, choices=TROPHY_TYPE_CHOICES)
    goal_value = models.IntegerField()
    point = models.IntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_trophy_type_display()} - 목표 {self.goal_value})"


class UserTrophy(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trophy = models.ForeignKey(Trophy, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trophy')

    def __str__(self):
        return f"{self.user.username} - {self.trophy.name}"
