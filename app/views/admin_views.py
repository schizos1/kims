# app/views/admin_views.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from flask_login import current_user

import google.generativeai as genai
import re
from textwrap import dedent

from app import db
from app.models import Subject, Concept, Step, Question, Trophy

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('이 페이지에 접근할 권한이 없습니다.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@bp.route('/subjects', methods=['GET', 'POST'])
@admin_required
def manage_subjects():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        if not Subject.query.filter_by(name=subject_name).first():
            db.session.add(Subject(name=subject_name))
            db.session.commit()
            flash('새 과목이 추가되었습니다.', 'success')
        else:
            flash('이미 존재하는 과목입니다.', 'warning')
        return redirect(url_for('admin.manage_subjects'))
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('admin/subjects.html', subjects=subjects)

@bp.route('/subject/delete/<int:subject_id>', methods=['POST'])
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash(f"'{subject.name}' 과목이 삭제되었습니다.", 'success')
    return redirect(url_for('admin.manage_subjects'))

@bp.route('/trophies')
@admin_required
def manage_trophies():
    trophies = Trophy.query.order_by(Trophy.id).all()
    return render_template('admin/trophies.html', trophies=trophies)

@bp.route('/subject/<int:subject_id>/concepts', methods=['GET', 'POST'])
@admin_required
def manage_concepts(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        concept_name = request.form['concept_name']
        if not Concept.query.filter_by(name=concept_name, subject_id=subject.id).first():
            new_concept = Concept(name=concept_name, subject_id=subject.id)
            db.session.add(new_concept)
            db.session.commit()
            flash(f"'{subject.name}' 과목에 새 개념 '{concept_name}'이(가) 추가되었습니다.", "success")
        else:
            flash("이미 존재하는 개념입니다.", "warning")
        return redirect(url_for('admin.manage_concepts', subject_id=subject.id))
    concepts = Concept.query.filter_by(subject_id=subject.id).order_by(Concept.name).all()
    return render_template('admin/concepts.html', subject=subject, concepts=concepts) # concepts 전달 추가

@bp.route('/concept/delete/<int:concept_id>', methods=['POST'])
@admin_required
def delete_concept(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    subject_id = concept.subject_id
    db.session.delete(concept)
    db.session.commit()
    flash(f"'{concept.name}' 개념이 삭제되었습니다.", 'success')
    return redirect(url_for('admin.manage_concepts', subject_id=subject_id))

@bp.route('/concept/<int:concept_id>/questions')
@admin_required
def manage_questions(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    questions = Question.query.filter_by(concept_id=concept.id).order_by(Question.id).all()
    return render_template('admin/manage_questions.html', concept=concept, questions=questions)

@bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    question_to_edit = Question.query.get_or_404(question_id)
    if request.method == 'POST':
        question_to_edit.content = request.form['content']
        question_to_edit.option1 = request.form.get('option1')
        question_to_edit.option2 = request.form.get('option2')
        question_to_edit.option3 = request.form.get('option3')
        question_to_edit.option4 = request.form.get('option4')
        question_to_edit.answer = request.form['answer']
        question_to_edit.question_type = request.form.get('question_type', 'multiple_choice')
        db.session.commit()
        flash(f"문제(ID: {question_to_edit.id})가 성공적으로 수정되었습니다.", "success")
        return redirect(url_for('admin.manage_questions', concept_id=question_to_edit.concept_id))
    return render_template('admin/edit_question.html', question=question_to_edit)

@bp.route('/question/<int:question_id>/delete', methods=['POST'])
@admin_required
def delete_question(question_id):
    question_to_delete = Question.query.get_or_404(question_id)
    concept_id = question_to_delete.concept_id
    db.session.delete(question_to_delete)
    db.session.commit()
    flash(f"문제(ID: {question_to_delete.id})가 삭제되었습니다.", "success")
    return redirect(url_for('admin.manage_questions', concept_id=concept_id))

@bp.route('/concept/<int:concept_id>/generate', methods=['POST'])
@admin_required
def generate_ai_content(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    subject_name_for_prompt = concept.subject.name
    
    # 기존 단계와 문제 삭제
    Step.query.filter_by(concept_id=concept.id).delete()
    Question.query.filter_by(concept_id=concept.id).delete()
    # db.session.commit() # 삭제 후 즉시 커밋 또는 아래 생성 후 함께 커밋

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # --- ★★★ AI 프롬프트 과목별 분기 수정 ★★★ ---
        is_math_subject = "수학" in subject_name_for_prompt or \
                          "산수" in subject_name_for_prompt or \
                          "계산" in subject_name_for_prompt

        if is_math_subject:
            question_type_instruction = "객관식 문제 10개를 만들어주세요. 각 문제는 질문(Q), 4개의 보기 (O1, O2, O3, O4), 그리고 정답 보기의 번호(A)를 포함해야 합니다."
            example_qa_format = dedent("""
            Q: 2 + 3 = ?
            O1: 4
            O2: 5
            O3: 6
            O4: 7
            A: 2""")
        else: # 수학 외 과목 (국어, 과학 등)
            question_type_instruction = "이 개념을 이해했는지 확인할 수 있는 다양한 유형의 총 10개 예제 문제와 그에 대한 정답 또는 모범 답안을 제공해주세요. 객관식 문제(Q, O1, O2, O3, O4, A 형식)와 단답형 주관식 문제(Q, A 형식)를 섞어도 좋습니다."
            example_qa_format = dedent("""
            예시 1 (객관식):
            Q: 다음 중 식물의 광합성에 필요한 요소가 아닌 것은 무엇일까요?
            O1: 햇빛
            O2: 물
            O3: 이산화탄소
            O4: 바람
            A: 4

            예시 2 (단답형):
            Q: 물이 얼음으로 변하는 현상을 무엇이라고 하나요?
            A: 응고""")
        # --- END AI 프롬프트 과목별 분기 수정 ---

        prompt = dedent(f"""
        당신은 대한민국 초등학생을 가르치는 친절하고 유능한 '{subject_name_for_prompt}' 과목 선생님입니다.
        '{subject_name_for_prompt}' 과목의 초등 교육과정 및 검정고시 준비에 맞춰, '{concept.name}' 라는 개념에 대한 학습 콘텐츠를 생성해주세요.
        출력은 반드시 아래의 지정된 형식으로만 제공해야 합니다.

        [STEP]
        Title: <학습 단계의 소제목>
        Explanation: <해당 단계에 대한 상세하고 친절한 설명. 아이들이 이해하기 쉬운 말투로 작성해주세요. 줄바꿈이 필요하면 실제 줄바꿈을 사용하세요.>
        (위 [STEP] 블록을 개념 이해에 필요한 만큼 반복해주세요. 최소 2개 이상 생성해주세요.)

        [EXAMPLE_QUESTIONS]
        # {question_type_instruction}
        # 생성되는 모든 문제와 보기, 특히 정답은 문법적, 내용적으로 반드시 정확해야 합니다.
        # 문제와 문제 사이에는 빈 줄을 한 줄 넣어주세요.
        # 예시 형식 (실제 생성 시에는 이 예시를 그대로 사용하지 마세요):
        # {example_qa_format}
        
        (이런 식으로 Q/A 또는 Q/O1-O4/A 쌍을 총 10개 생성)
        """)
        
        print(f"--- AI Prompt for {subject_name_for_prompt} - {concept.name} ---\n{prompt}\n------------------------------------") # 디버깅용 프롬프트 출력

        response = model.generate_content(prompt)
        content = response.text
        print(f"--- AI Response for {concept.name} ---\n{content}\n------------------------------------") # 디버깅용 AI 응답 출력
        
        steps_data = []
        step_pattern = re.compile(r"\[STEP\]\s*Title:(.*?)\s*Explanation:(.*?)(?=\[STEP\]|\[EXAMPLE_QUESTIONS\]|$)", re.DOTALL | re.IGNORECASE)
        for match in step_pattern.finditer(content):
            steps_data.append({'title': match.group(1).strip(), 'explanation': match.group(2).strip()})
        
        questions_data = []
        example_questions_match = re.search(r"\[EXAMPLE_QUESTIONS\](.*)", content, re.DOTALL | re.IGNORECASE)
        if example_questions_match:
            questions_block_text = example_questions_match.group(1).strip()
            # 문제 구분을 "Q:" 또는 "\nQ:" 기준으로 변경하고, 빈 문자열 제거
            individual_question_blocks = [q.strip() for q in re.split(r"(?<!\S)Q:", questions_block_text) if q.strip()]

            for block_num, block in enumerate(individual_question_blocks):
                block = block.strip()
                if not block: continue
                
                # print(f"--- Parsing Question Block {block_num + 1} ---\n{block}\n----------------------------------") # 디버깅용

                # Q: 다음 줄부터 O1: 또는 A: 전까지를 문제 내용으로 파싱
                q_match = re.match(r"^(.*?)(?=(\n\s*O1:|\n\s*A:))", block, re.DOTALL)
                question_text = q_match.group(1).strip() if q_match else None
                
                if not question_text:
                    # print(f"Block {block_num+1}에서 문제 내용을 찾을 수 없음. 건너뜀.")
                    continue

                o1_match = re.search(r"\n\s*O1:\s*(.*?)(?=\n\s*O2:)", block, re.DOTALL)
                o2_match = re.search(r"\n\s*O2:\s*(.*?)(?=\n\s*O3:)", block, re.DOTALL)
                o3_match = re.search(r"\n\s*O3:\s*(.*?)(?=\n\s*O4:)", block, re.DOTALL)
                o4_match = re.search(r"\n\s*O4:\s*(.*?)(?=\n\s*A:)", block, re.DOTALL)
                a_mc_match = re.search(r"\n\s*A:\s*([1-4])(?!\S)", block) # 객관식 정답 (숫자만)
                a_short_match = re.search(r"\n\s*A:\s*(.*)", block, re.DOTALL) # 주관식 또는 일반 정답

                if o1_match and o2_match and o3_match and o4_match and a_mc_match: # 객관식
                    questions_data.append({
                        'content': question_text,
                        'option1': o1_match.group(1).strip(),
                        'option2': o2_match.group(1).strip(),
                        'option3': o3_match.group(1).strip(),
                        'option4': o4_match.group(1).strip(),
                        'answer': a_mc_match.group(1).strip(),
                        'type': 'multiple_choice'
                    })
                elif a_short_match: # 주관식 (또는 AI가 다른 형식으로 답했을 때의 fallback)
                    questions_data.append({
                        'content': question_text,
                        'option1': None, 'option2': None, 'option3': None, 'option4': None,
                        'answer': a_short_match.group(1).strip(),
                        'type': 'short_answer' # 또는 'descriptive' 등
                    })
                # else:
                    # print(f"Block {block_num+1}에서 문제 형식을 인식할 수 없음: {question_text}")


        step_order = 1
        for step_info in steps_data:
            new_step = Step(title=step_info['title'], explanation=step_info['explanation'], step_order=step_order, concept_id=concept.id)
            db.session.add(new_step)
            step_order += 1
        
        for q_info in questions_data:
            new_question = Question(
                content=q_info['content'],
                option1=q_info.get('option1'),
                option2=q_info.get('option2'),
                option3=q_info.get('option3'),
                option4=q_info.get('option4'),
                answer=q_info['answer'],
                question_type=q_info['type'],
                concept_id=concept.id
            )
            db.session.add(new_question)
            
        if not steps_data and not questions_data:
            flash(f"AI가 '{concept.name}'에 대한 학습 내용을 생성하지 못했습니다. 응답을 확인해주세요.", 'warning')
        else:
            db.session.commit()
            flash(f"'{concept.name}' ({concept.subject.name})에 대한 학습 내용이 AI에 의해 성공적으로 생성되었습니다! ({len(steps_data)}개 단계, {len(questions_data)}개 문제)", 'success')

    except Exception as e:
        db.session.rollback()
        flash(f"AI 콘텐츠 생성 중 오류가 발생했습니다 ({concept.name}): {e}", 'danger')
        print(f"AI Error in generate_ai_content: {e}")
        # content 변수가 정의되었는지 확인 후 출력 (오류 발생 전에 content가 할당되지 않았을 수 있음)
        if 'content' in locals() and content: 
            print(f"AI Response Content (on error): {content}")
            
    return redirect(url_for('admin.manage_concepts', subject_id=concept.subject_id))