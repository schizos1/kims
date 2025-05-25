# app/views/admin_views.py

import os # os.getenv 등에서 사용될 수 있으므로 유지
from flask import Blueprint, render_template, request, redirect, url_for, flash
from functools import wraps
from flask_login import current_user
import google.generativeai as genai
import re
from app import db
from app.utils import allowed_file, save_image, delete_image_file # <-- 유틸리티 함수 임포트

# --- admin_required 데코레이터 (여기에 유지) ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash('이 페이지에 접근할 권한이 없습니다.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- Main Admin Route ---
@bp.route('/')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

# --- Subject Routes ---
@bp.route('/subjects', methods=['GET', 'POST'])
@admin_required
def manage_subjects():
    from app.models import Subject
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        if not subject_name: # 이름이 비어있는 경우 방지
            flash('과목 이름을 입력해주세요.', 'warning')
            return redirect(url_for('admin.manage_subjects'))
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
    from app.models import Subject
    subject = Subject.query.get_or_404(subject_id)
    # TODO: 과목에 연결된 개념, 문제 등이 있다면 함께 삭제하거나, 삭제를 막는 로직 필요
    db.session.delete(subject)
    db.session.commit()
    flash(f"'{subject.name}' 과목이 삭제되었습니다.", 'success')
    return redirect(url_for('admin.manage_subjects'))

# --- Concept Routes ---
@bp.route('/subject/<int:subject_id>/concepts', methods=['GET', 'POST'])
@admin_required
def manage_concepts(subject_id):
    from app.models import Subject, Concept
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        concept_name = request.form.get('concept_name')
        if not concept_name: # 이름 비어있는 경우 방지
            flash('개념 이름을 입력해주세요.', 'warning')
            return redirect(url_for('admin.manage_concepts', subject_id=subject.id))
        if not Concept.query.filter_by(name=concept_name, subject_id=subject.id).first():
            new_concept = Concept(name=concept_name, subject_id=subject.id)
            db.session.add(new_concept)
            db.session.commit()
            flash(f"'{subject.name}' 과목에 새 개념 '{concept_name}'이(가) 추가되었습니다.", "success")
        else:
            flash("이미 존재하는 개념입니다.", "warning")
        return redirect(url_for('admin.manage_concepts', subject_id=subject.id))
    concepts = Concept.query.filter_by(subject_id=subject.id).order_by(Concept.name).all()
    return render_template('admin/concepts.html', subject=subject, concepts=concepts) 

@bp.route('/concept/delete/<int:concept_id>', methods=['POST'])
@admin_required
def delete_concept(concept_id):
    from app.models import Concept
    concept = Concept.query.get_or_404(concept_id)
    subject_id = concept.subject_id
    # TODO: 개념에 연결된 문제, 스텝 등이 있다면 함께 삭제하거나, 삭제를 막는 로직 필요
    db.session.delete(concept)
    db.session.commit()
    flash(f"'{concept.name}' 개념이 삭제되었습니다.", 'success')
    return redirect(url_for('admin.manage_concepts', subject_id=subject_id))

# --- Question Routes ---
@bp.route('/concept/<int:concept_id>/questions')
@admin_required
def manage_questions(concept_id):
    from app.models import Concept, Question
    concept = Concept.query.get_or_404(concept_id)
    questions = Question.query.filter_by(concept_id=concept.id).order_by(Question.id).all()
    return render_template('admin/manage_questions.html', concept=concept, questions=questions)

@bp.route('/concept/<int:concept_id>/question/add', methods=['GET', 'POST'])
@admin_required
def add_question(concept_id):
    from app.models import Concept, Question
    concept = Concept.query.get_or_404(concept_id)
    if request.method == 'POST':
        content = request.form.get('content')
        question_type = request.form.get('question_type')
        answer = request.form.get('answer')
        source_type = request.form.get('source_type')
        if not content or not question_type or not answer or not source_type:
            flash('문제 내용, 유형, 정답, 출처는 모두 필수입니다.', 'danger')
            return render_template('admin/add_question.html', concept=concept, form_data=request.form)
        
        image_filename_main = save_image(request.files.get('image_filename'), subfolder='questions')
        option_texts = [request.form.get(f'option{i}') for i in range(1, 5)]
        option_images_filenames = [save_image(request.files.get(f'option{i}_img'), subfolder='questions') for i in range(1, 5)]
        
        new_question = Question(
            content=content, image_filename=image_filename_main,
            question_type=question_type,
            option1=option_texts[0], option1_img=option_images_filenames[0],
            option2=option_texts[1], option2_img=option_images_filenames[1],
            option3=option_texts[2], option3_img=option_images_filenames[2],
            option4=option_texts[3], option4_img=option_images_filenames[3],
            answer=answer, source_type=source_type, concept_id=concept.id
        )
        db.session.add(new_question)
        db.session.commit()
        flash(f"'{concept.name}' 개념에 새 문제가 성공적으로 추가되었습니다!", "success")
        return redirect(url_for('admin.manage_questions', concept_id=concept.id))
    return render_template('admin/add_question.html', concept=concept, form_data={})

@bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    from app.models import Question
    question_to_edit = Question.query.get_or_404(question_id)
    concept = question_to_edit.concept
    if request.method == 'POST':
        question_to_edit.content = request.form.get('content')
        question_to_edit.question_type = request.form.get('question_type')
        question_to_edit.answer = request.form.get('answer')
        question_to_edit.source_type = request.form.get('source_type')

        if request.form.get('delete_image_filename'): 
            delete_image_file(question_to_edit.image_filename, subfolder='questions')
            question_to_edit.image_filename = None
        elif 'image_filename' in request.files and request.files['image_filename'].filename != '': 
            delete_image_file(question_to_edit.image_filename, subfolder='questions') 
            new_filename = save_image(request.files['image_filename'], subfolder='questions')
            if new_filename:
                question_to_edit.image_filename = new_filename
            else: 
                flash('문제 본문 이미지 업로드 실패. 파일 형식을 확인하세요.', 'danger')
                return render_template('admin/edit_question.html', question=question_to_edit, concept=concept)

        question_to_edit.option1 = request.form.get('option1')
        question_to_edit.option2 = request.form.get('option2')
        question_to_edit.option3 = request.form.get('option3')
        question_to_edit.option4 = request.form.get('option4')

        for i in range(1, 5):
            option_img_field_name = f'option{i}_img'
            delete_checkbox_name = f'delete_option{i}_img'
            current_img_attr_name = f'option{i}_img'
            
            if request.form.get(delete_checkbox_name): 
                delete_image_file(getattr(question_to_edit, current_img_attr_name), subfolder='questions')
                setattr(question_to_edit, current_img_attr_name, None)
            elif option_img_field_name in request.files and request.files[option_img_field_name].filename != '': 
                delete_image_file(getattr(question_to_edit, current_img_attr_name), subfolder='questions') 
                new_option_filename = save_image(request.files[option_img_field_name], subfolder='questions')
                if new_option_filename:
                    setattr(question_to_edit, current_img_attr_name, new_option_filename)
                else: 
                    flash(f'보기 {i} 이미지 업로드 실패. 파일 형식을 확인하세요.', 'danger')
                    return render_template('admin/edit_question.html', question=question_to_edit, concept=concept)
        
        db.session.commit()
        flash(f"문제(ID: {question_to_edit.id})가 성공적으로 수정되었습니다.", "success")
        return redirect(url_for('admin.manage_questions', concept_id=question_to_edit.concept_id))
    return render_template('admin/edit_question.html', question=question_to_edit, concept=concept)

@bp.route('/question/<int:question_id>/delete', methods=['POST'])
@admin_required
def delete_question(question_id):
    from app.models import Question
    question_to_delete = Question.query.get_or_404(question_id)
    concept_id = question_to_delete.concept_id
    image_filenames_to_delete = []
    if question_to_delete.image_filename:
        image_filenames_to_delete.append(question_to_delete.image_filename)
    for i in range(1, 5):
        img_attr = f'option{i}_img'
        img_filename = getattr(question_to_delete, img_attr)
        if img_filename:
            image_filenames_to_delete.append(img_filename)
    
    db.session.delete(question_to_delete)
    db.session.commit()
    
    for filename in image_filenames_to_delete:
        delete_image_file(filename, subfolder='questions')
        
    flash(f"문제(ID: {question_to_delete.id})가 삭제되었습니다.", "success")
    return redirect(url_for('admin.manage_questions', concept_id=concept_id))

# --- AI Content Generation ---
@bp.route('/concept/<int:concept_id>/generate', methods=['POST'])
@admin_required
def generate_ai_content(concept_id):
    from app.models import Concept, Step, Question, PromptTemplate, Subject # Subject 추가
    concept = Concept.query.get_or_404(concept_id)
    subject = concept.subject

    prompt_template = PromptTemplate.query.filter_by(subject_id=subject.id, is_default_for_subject=True).first()
    if not prompt_template:
        is_math_subject = any(keyword in subject.name for keyword in ["수학", "산수", "계산"])
        if is_math_subject:
            prompt_template = PromptTemplate.query.filter_by(name='초등 수학 객관식 문제 생성 프롬프트').first()
        else:
            prompt_template = PromptTemplate.query.filter_by(name='초등 일반 과목 문제 생성 프롬프트 (객관식/주관식 혼합)').first()
    
    if not prompt_template:
        flash(f"'{subject.name}' 과목에 대한 AI 프롬프트 템플릿을 찾을 수 없습니다. 먼저 프롬프트를 등록해주세요.", "danger")
        return redirect(url_for('admin.manage_concepts', subject_id=subject.id))
    
    final_prompt_text = prompt_template.content.replace('{{subject_name}}', subject.name).replace('{{concept_name}}', concept.name)

    # TODO: 기존 이미지 파일들 삭제 로직 필요 (Question.image_filename, Question.optionX_img 등)
    Step.query.filter_by(concept_id=concept.id).delete()
    Question.query.filter_by(concept_id=concept.id).delete(synchronize_session='fetch') # synchronize_session 옵션 주의

    ai_response_content = None
    try:
        if not os.getenv('GOOGLE_API_KEY'):
            flash("Google API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.", "danger")
            return redirect(url_for('admin.manage_concepts', subject_id=subject.id))
        
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        print(f"--- AI Prompt for {subject.name} - {concept.name} (using template: {prompt_template.name}) ---\n{final_prompt_text}\n------------------------------------")
        response = model.generate_content(final_prompt_text)
        ai_response_content = response.text 
        print(f"--- AI Response for {concept.name} ---\n{ai_response_content}\n------------------------------------")
        
        steps_data = []
        step_pattern = re.compile(r"\[STEP\]\s*Title:(.*?)\s*Explanation:(.*?)(?=\[STEP\]|\[EXAMPLE_QUESTIONS\]|$)", re.DOTALL | re.IGNORECASE)
        for match in step_pattern.finditer(ai_response_content):
            steps_data.append({'title': match.group(1).strip(), 'explanation': match.group(2).strip()})
        
        questions_data = []
        example_questions_match = re.search(r"\[EXAMPLE_QUESTIONS\](.*)", ai_response_content, re.DOTALL | re.IGNORECASE)
        if example_questions_match:
            questions_block_text = example_questions_match.group(1).strip()
            individual_question_blocks = [q.strip() for q in re.split(r"(?<!\S)Q:", questions_block_text) if q.strip()]
            for block in individual_question_blocks:
                block = block.strip()
                if not block: continue
                q_match = re.match(r"^(.*?)(?=(\n\s*O1:|\n\s*A:))", block, re.DOTALL)
                question_text = q_match.group(1).strip() if q_match else None
                if not question_text: continue
                
                o1_match = re.search(r"\n\s*O1:\s*(.*?)(?=(\n\s*O2:|\n\s*A:|$))", block, re.DOTALL)
                o2_match = re.search(r"\n\s*O2:\s*(.*?)(?=(\n\s*O3:|\n\s*A:|$))", block, re.DOTALL)
                o3_match = re.search(r"\n\s*O3:\s*(.*?)(?=(\n\s*O4:|\n\s*A:|$))", block, re.DOTALL)
                o4_match = re.search(r"\n\s*O4:\s*(.*?)(?=(\n\s*A:|$))", block, re.DOTALL)
                a_mc_match = re.search(r"\n\s*A:\s*([1-4])(?!\S)", block) 
                a_short_match = re.search(r"\n\s*A:\s*(.*)", block, re.DOTALL) # 주관식 정답은 나머지 전체

                if o1_match and o2_match and o3_match and o4_match and a_mc_match:
                    questions_data.append({
                        'content': question_text, 
                        'option1': o1_match.group(1).strip(), 'option2': o2_match.group(1).strip(), 
                        'option3': o3_match.group(1).strip(), 'option4': o4_match.group(1).strip(), 
                        'answer': a_mc_match.group(1).strip(), 'type': 'multiple_choice'
                    })
                elif a_short_match:
                    answer_text = a_short_match.group(1).strip()
                    questions_data.append({
                        'content': question_text, 'option1': None, 'option2': None, 
                        'option3': None, 'option4': None, 'answer': answer_text, 'type': 'short_answer'
                    })
        
        step_order_counter = 1
        for step_info in steps_data:
            new_step = Step(title=step_info['title'], explanation=step_info['explanation'], step_order=step_order_counter, concept_id=concept.id)
            db.session.add(new_step)
            step_order_counter += 1
        
        for q_info in questions_data:
            new_question = Question(
                content=q_info['content'], option1=q_info.get('option1'), option2=q_info.get('option2'), 
                option3=q_info.get('option3'), option4=q_info.get('option4'), 
                answer=q_info['answer'], question_type=q_info['type'], 
                concept_id=concept.id, source_type='ai_generated'
            )
            db.session.add(new_question)
        
        if not steps_data and not questions_data:
            flash(f"AI가 '{concept.name}'에 대한 학습 내용을 생성하지 못했거나 텍스트 파싱에 실패했습니다. AI 응답을 확인해주세요.", 'warning')
        else:
            db.session.commit()
            flash(f"'{concept.name}' ({subject.name})에 대한 학습 내용이 AI에 의해 성공적으로 생성되었습니다!", 'success')
        return redirect(url_for('admin.manage_concepts', subject_id=subject.id))
    except Exception as e:
        db.session.rollback()
        flash(f"AI 콘텐츠 생성 중 심각한 오류 발생 ({concept.name}): {e}", 'danger')
        if ai_response_content: 
            print(f"AI Response Content (on error in except block):\n{ai_response_content}")
        return redirect(url_for('admin.manage_concepts', subject_id=subject.id))

# --- Trophy CRUD ---
@bp.route('/trophies')
@admin_required
def manage_trophies():
    from app.models import Trophy
    trophies = Trophy.query.order_by(Trophy.id).all()
    return render_template('admin/manage_trophies.html', trophies=trophies)

@bp.route('/trophy/add', methods=['GET', 'POST'])
@admin_required
def add_trophy():
    from app.models import Trophy
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon_class = request.form.get('icon_class', 'fas fa-trophy')
        points_str = request.form.get('points')
        condition_type = request.form.get('condition_type')
        condition_value_int_str = request.form.get('condition_value_int')
        condition_value_str = request.form.get('condition_value_str')
        is_active = request.form.get('is_active') == 'on'

        if not name or not icon_class or not points_str:
            flash('트로피 이름, 아이콘 클래스, 획득 포인트는 필수입니다.', 'danger')
            return render_template('admin/add_trophy.html', form_data=request.form)
        try:
            points = int(points_str)
        except ValueError:
            flash('획득 포인트는 숫자로 입력해야 합니다.', 'danger')
            return render_template('admin/add_trophy.html', form_data=request.form)
        
        condition_value_int = None
        if condition_value_int_str:
            try:
                condition_value_int = int(condition_value_int_str)
            except ValueError:
                flash('조건 숫자 값은 유효한 숫자로 입력해야 합니다.', 'danger')
                return render_template('admin/add_trophy.html', form_data=request.form)

        new_trophy = Trophy(
            name=name, description=description, icon_class=icon_class, points=points,
            condition_type=condition_type if condition_type else None,
            condition_value_int=condition_value_int,
            condition_value_str=condition_value_str if condition_value_str else None,
            is_active=is_active
        )
        db.session.add(new_trophy)
        db.session.commit()
        flash(f"새 트로피 '{name}'이(가) 성공적으로 추가되었습니다!", "success")
        return redirect(url_for('admin.manage_trophies'))
    return render_template('admin/add_trophy.html', form_data={})

@bp.route('/trophy/<int:trophy_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_trophy(trophy_id):
    from app.models import Trophy
    trophy_to_edit = Trophy.query.get_or_404(trophy_id)
    if request.method == 'POST':
        trophy_to_edit.name = request.form.get('name')
        trophy_to_edit.description = request.form.get('description')
        trophy_to_edit.icon_class = request.form.get('icon_class', 'fas fa-trophy')
        points_str = request.form.get('points')
        trophy_to_edit.condition_type = request.form.get('condition_type')
        condition_value_int_str = request.form.get('condition_value_int')
        trophy_to_edit.condition_value_str = request.form.get('condition_value_str')
        trophy_to_edit.is_active = request.form.get('is_active') == 'on'

        if not trophy_to_edit.name or not trophy_to_edit.icon_class or not points_str:
            flash('트로피 이름, 아이콘 클래스, 획득 포인트는 필수입니다.', 'danger')
            return render_template('admin/edit_trophy.html', trophy=trophy_to_edit)
        try:
            trophy_to_edit.points = int(points_str)
        except ValueError:
            flash('획득 포인트는 숫자로 입력해야 합니다.', 'danger')
            return render_template('admin/edit_trophy.html', trophy=trophy_to_edit)
        
        if condition_value_int_str:
            try:
                trophy_to_edit.condition_value_int = int(condition_value_int_str)
            except ValueError:
                flash('조건 숫자 값은 유효한 숫자로 입력해야 합니다.', 'danger')
                return render_template('admin/edit_trophy.html', trophy=trophy_to_edit)
        else:
            trophy_to_edit.condition_value_int = None
        
        if not trophy_to_edit.condition_type: trophy_to_edit.condition_type = None
        if not trophy_to_edit.condition_value_str: trophy_to_edit.condition_value_str = None
        
        db.session.commit()
        flash(f"트로피(ID: {trophy_to_edit.id})가 성공적으로 수정되었습니다.", "success")
        return redirect(url_for('admin.manage_trophies'))
    return render_template('admin/edit_trophy.html', trophy=trophy_to_edit)

@bp.route('/trophy/<int:trophy_id>/delete', methods=['POST'])
@admin_required
def delete_trophy(trophy_id):
    from app.models import Trophy, UserTrophy
    UserTrophy.query.filter_by(trophy_id=trophy_id).delete(synchronize_session='fetch')
    trophy_to_delete = Trophy.query.get_or_404(trophy_id)
    db.session.delete(trophy_to_delete)
    db.session.commit()
    flash(f"트로피(ID: {trophy_id}, 이름: {trophy_to_delete.name})가 성공적으로 삭제되었습니다.", "success")
    return redirect(url_for('admin.manage_trophies'))

# --- Mascot Routes ---
@bp.route('/mascots')
@admin_required
def manage_mascots():
    from app.models import Mascot
    mascots = Mascot.query.order_by(Mascot.name).all()
    return render_template('admin/manage_mascots.html', mascots=mascots)

@bp.route('/mascot/add', methods=['GET', 'POST'])
@admin_required
def add_mascot():
    from app.models import Mascot
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image_file = request.files.get('image_filename')
        if not name or not image_file or not image_file.filename:
            flash('마스코트 이름과 이미지 파일은 필수입니다.', 'danger')
            return render_template('admin/add_mascot.html', form_data=request.form)
        
        image_filename = save_image(image_file, subfolder='mascots')
        if not image_filename: 
            flash('마스코트 이미지 업로드 실패. 파일 형식을 확인하거나 파일이 올바른지 확인하세요.', 'danger')
            return render_template('admin/add_mascot.html', form_data=request.form)

        new_mascot = Mascot(name=name, description=description, image_filename=image_filename)
        db.session.add(new_mascot)
        db.session.commit()
        flash(f"새 마스코트 '{name}'이(가) 성공적으로 추가되었습니다!", "success")
        return redirect(url_for('admin.manage_mascots'))
    return render_template('admin/add_mascot.html', form_data={})

@bp.route('/mascot/<int:mascot_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_mascot(mascot_id):
    from app.models import Mascot
    mascot_to_edit = Mascot.query.get_or_404(mascot_id)
    if request.method == 'POST':
        mascot_to_edit.name = request.form.get('name')
        mascot_to_edit.description = request.form.get('description')
        image_file = request.files.get('image_filename')
        if image_file and image_file.filename != '':
            delete_image_file(mascot_to_edit.image_filename, subfolder='mascots')
            new_filename = save_image(image_file, subfolder='mascots')
            if new_filename:
                mascot_to_edit.image_filename = new_filename
            else:
                flash('마스코트 이미지 업로드 실패. 파일 형식을 확인하세요.', 'danger')
                return render_template('admin/edit_mascot.html', mascot=mascot_to_edit)
        
        db.session.commit()
        flash(f"마스코트 '{mascot_to_edit.name}'의 정보가 성공적으로 수정되었습니다.", "success")
        return redirect(url_for('admin.manage_mascots'))
    return render_template('admin/edit_mascot.html', mascot=mascot_to_edit)

@bp.route('/mascot/<int:mascot_id>/delete', methods=['POST'])
@admin_required
def delete_mascot(mascot_id):
    from app.models import Mascot
    mascot_to_delete = Mascot.query.get_or_404(mascot_id)
    image_to_delete = mascot_to_delete.image_filename
    db.session.delete(mascot_to_delete)
    db.session.commit()
    if image_to_delete:
        delete_image_file(image_to_delete, subfolder='mascots')
    flash(f"마스코트 '{mascot_to_delete.name}'이(가) 성공적으로 삭제되었습니다.", "success")
    return redirect(url_for('admin.manage_mascots'))

# --- PromptTemplate CRUD Routes ---
@bp.route('/prompts')
@admin_required
def manage_prompt_templates():
    from app.models import PromptTemplate
    prompts = PromptTemplate.query.order_by(PromptTemplate.name).all()
    return render_template('admin/manage_prompts.html', prompts=prompts)

@bp.route('/prompt/add', methods=['GET', 'POST'])
@admin_required
def add_prompt_template():
    from app.models import PromptTemplate, Subject
    subjects = Subject.query.order_by(Subject.name).all()
    if request.method == 'POST':
        name = request.form.get('name')
        subject_id_str = request.form.get('subject_id')
        content = request.form.get('content')
        notes = request.form.get('notes')
        is_default_for_subject = request.form.get('is_default_for_subject') == 'on'

        if not name or not content: 
            flash('템플릿 이름과 프롬프트 내용은 필수입니다.', 'danger')
            return render_template('admin/add_prompt_template.html', subjects=subjects, form_data=request.form)

        subject_id = None
        if subject_id_str and subject_id_str.isdigit(): # 숫자형인지 확인
            subject_id = int(subject_id_str)
        elif subject_id_str: # 숫자가 아닌 값이 들어온 경우 (예: 빈 문자열이 아닌 경우)
             flash('유효하지 않은 과목 ID 형식입니다.', 'danger')
             return render_template('admin/add_prompt_template.html', subjects=subjects, form_data=request.form)
        
        if subject_id and is_default_for_subject: 
            PromptTemplate.query.filter_by(subject_id=subject_id, is_default_for_subject=True).update({"is_default_for_subject": False})

        new_prompt = PromptTemplate(
            name=name, 
            subject_id=subject_id, 
            content=content, 
            notes=notes,
            is_default_for_subject=is_default_for_subject if subject_id else False
        )
        db.session.add(new_prompt)
        db.session.commit()
        flash(f"새 프롬프트 템플릿 '{name}'이(가) 성공적으로 추가되었습니다!", "success")
        return redirect(url_for('admin.manage_prompt_templates'))
    return render_template('admin/add_prompt_template.html', subjects=subjects, form_data={})

@bp.route('/prompt/<int:prompt_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_prompt_template(prompt_id):
    from app.models import PromptTemplate, Subject
    prompt_to_edit = PromptTemplate.query.get_or_404(prompt_id)
    subjects = Subject.query.order_by(Subject.name).all()
    if request.method == 'POST':
        prompt_to_edit.name = request.form.get('name')
        subject_id_str = request.form.get('subject_id')
        prompt_to_edit.content = request.form.get('content')
        prompt_to_edit.notes = request.form.get('notes')
        is_default_for_subject = request.form.get('is_default_for_subject') == 'on'

        if not prompt_to_edit.name or not prompt_to_edit.content: 
            flash('템플릿 이름과 프롬프트 내용은 필수입니다.', 'danger')
            return render_template('admin/edit_prompt_template.html', prompt=prompt_to_edit, subjects=subjects)

        subject_id = None
        if subject_id_str and subject_id_str.isdigit():
            subject_id = int(subject_id_str)
        elif subject_id_str:
             flash('유효하지 않은 과목 ID 형식입니다.', 'danger')
             return render_template('admin/edit_prompt_template.html', prompt=prompt_to_edit, subjects=subjects)
        
        prompt_to_edit.subject_id = subject_id
        
        if subject_id and is_default_for_subject: 
            PromptTemplate.query.filter(
                PromptTemplate.subject_id == subject_id,
                PromptTemplate.id != prompt_id, 
                PromptTemplate.is_default_for_subject == True
            ).update({"is_default_for_subject": False})
        
        prompt_to_edit.is_default_for_subject = is_default_for_subject if subject_id else False

        db.session.commit()
        flash(f"프롬프트 템플릿(ID: {prompt_id})이 성공적으로 수정되었습니다.", "success")
        return redirect(url_for('admin.manage_prompt_templates'))
    return render_template('admin/edit_prompt_template.html', prompt=prompt_to_edit, subjects=subjects)

@bp.route('/prompt/<int:prompt_id>/delete', methods=['POST'])
@admin_required
def delete_prompt_template(prompt_id):
    from app.models import PromptTemplate
    prompt_to_delete = PromptTemplate.query.get_or_404(prompt_id)
    db.session.delete(prompt_to_delete)
    db.session.commit()
    flash(f"프롬프트 템플릿(ID: {prompt_id}, 이름: {prompt_to_delete.name})이 성공적으로 삭제되었습니다.", "success")
    return redirect(url_for('admin.manage_prompt_templates'))