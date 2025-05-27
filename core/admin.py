# ============================================
# 📄 FILE: core/admin.py
# 📝 DESCRIPTION: 관리자 페이지 설정 (문제 자동 생성 포함 + 시각적 미리보기)
# ============================================

from django.contrib import admin
from .models import PromptTemplate, ConceptLesson, Question
from jinja2 import Template
from .models import Trophy, UserTrophy
import requests
import json

# ✅ 프롬프트 템플릿 관리
@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ['subject', 'title']
    search_fields = ['subject', 'title']


# ✅ 관련 문제 인라인 표시
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['question_text', 'correct_answer']
    readonly_fields = ['question_text', 'correct_answer']


# ✅ 개념 학습 관리 + 문제 생성 액션 + 프롬프트 미리보기
@admin.register(ConceptLesson)
class ConceptLessonAdmin(admin.ModelAdmin):
    list_display = ['unit_title', 'subject', 'grade', 'is_generated', 'is_published']
    list_filter = ['subject', 'grade', 'is_generated', 'is_published']
    search_fields = ['unit_title', 'concept_text', 'explanation']
    autocomplete_fields = ['prompt_template']
    actions = ['generate_questions']
    inlines = [QuestionInline]
    readonly_fields = ['preview_prompt']

    # 🔍 프롬프트 렌더링 미리보기
    def preview_prompt(self, obj):
        if obj.prompt_template:
            try:
                rendered = Template(obj.prompt_template.prompt_text).render(
                    concept_text=obj.concept_text,
                    unit_title=obj.unit_title,
                    grade=obj.grade,
                    subject=obj.subject,
                )
                return f"<pre style='white-space: pre-wrap'>{rendered}</pre>"
            except:
                return "⚠️ 렌더링 실패"
        return "❌ 프롬프트 미지정"
    preview_prompt.short_description = "🔍 렌더링된 프롬프트"

    # 🤖 문제 자동 생성 액션
    def generate_questions(self, request, queryset):
        for concept in queryset:
            if not concept.prompt_template:
                continue

            try:
                # 1. 프롬프트 렌더링
                template = Template(concept.prompt_template.prompt_text)
                rendered_prompt = template.render(
                    concept_text=concept.concept_text,
                    unit_title=concept.unit_title,
                    grade=concept.grade,
                    subject=concept.subject,
                )

                # 2. Google Generative API 호출
                api_key = "AIzaSyBJCaj-p95aNnAQWz0jr-cO4-dJTKLuSZg"
                url = f"https://generativelanguage.googleapis.com/v1beta3/models/text-bison-001:generateText?key={api_key}"
                headers = {"Content-Type": "application/json"}
                body = {
                    "prompt": {"text": rendered_prompt},
                    "temperature": 0.7
                }

                response = requests.post(url, headers=headers, json=body)
                content = response.json()['candidates'][0]['output']

                # 3. JSON 파싱 → Question 저장
                parsed = json.loads(content)

                Question.objects.create(
                    subject=concept.subject,
                    grade=concept.grade,
                    concept=concept,
                    question_text=parsed["question"],
                    option1=parsed["options"][0],
                    option2=parsed["options"][1],
                    option3=parsed["options"][2],
                    option4=parsed["options"][3],
                    correct_answer=int(parsed["answer"])
                )

                concept.is_generated = True
                concept.save()

            except Exception as e:
                self.message_user(request, f"[{concept.unit_title}] 문제 생성 실패: {e}", level="error")
                continue

        self.message_user(request, f"{queryset.count()}개의 개념에 대해 문제 생성 요청 완료.")
    generate_questions.short_description = "🤖 선택한 개념에 대해 문제 자동 생성"

@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    list_display = ['name', 'trophy_type', 'goal_value', 'point']
    list_filter = ['trophy_type']
    search_fields = ['name', 'description']


class UserTrophyAdmin(admin.ModelAdmin):
    list_display = ['user', 'trophy', 'awarded_at']
    list_filter = ['awarded_at']
    search_fields = ['user__username', 'trophy__name']
