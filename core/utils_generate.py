# ============================================
# 📄 FILE: core/utils_generate.py
# 📝 DESCRIPTION: 개념 기반 문제 자동 생성 유틸리티
# ============================================

import json
import requests
from jinja2 import Template
from .models import Question

def render_prompt(concept):
    template_str = concept.prompt_template.prompt_text
    context = {
        "concept_text": concept.concept_text,
        "unit_title": concept.unit_title,
        "grade": concept.grade,
        "subject": concept.subject,
    }
    return Template(template_str).render(context)

def generate_question_from_concept(concept, api_key=None):
    prompt = render_prompt(concept)

    # 👉 여기를 원하는 API 방식으로 바꾸면 됨
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        },
    )

    content = response.json()["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)  # JSON 형태로 문제 파싱
        question = Question.objects.create(
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
        return question

    except Exception as e:
        print("문제 생성 실패:", e)
        return None
