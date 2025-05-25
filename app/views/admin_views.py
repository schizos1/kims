# app/views/admin_views.py (수정 완료된 최종본)

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from functools import wraps
from flask_login import current_user
from werkzeug.utils import secure_filename
import uuid 
import google.generativeai as genai
import re
from app import db

# --- Helper Functions ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('이 페이지에 접근할 권한이 없습니다.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_image(file_storage, subfolder='questions'):
    if file_storage and file_storage.filename != '' and allowed_file(file_storage.filename):
        original_filename = secure_filename(file_storage.filename)
        ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        upload_folder_base = None
        if subfolder == 'mascots':
            upload_folder_base = os.path.join(current_app.root_path, 'static/images/mascots')
        elif subfolder == 'trophies':
            upload_folder_base = current_app.config.get('UPLOAD_FOLDER_TROPHIES', os.path.join(current_app.root_path, 'static/uploads/trophies'))
        else:
            upload_folder_base = current_app.config.get('UPLOAD_FOLDER_QUESTIONS', os.path.join(current_app.root_path, 'static/uploads/questions'))

        os.makedirs(upload_folder_base, exist_ok=True)
        file_path = os.path.join(upload_folder_base, unique_filename)
        file_storage.save(file_path)
        return unique_filename
    return None

def delete_image_file(filename, subfolder='questions'):
    if filename:
        upload_folder_base = None
        if subfolder == 'mascots':
            upload_folder_base = os.path.join(current_app.root_path, 'static/images/mascots')
        elif subfolder == 'trophies':
            upload_folder_base = current_app.config.get('UPLOAD_FOLDER_TROPHIES', os.path.join(current_app.root_path, 'static/uploads/trophies'))
        else:
            upload_folder_base = current_app.config.get('UPLOAD_FOLDER_QUESTIONS', os.path.join(current_app.root_path, 'static/uploads/questions'))
            
        file_path = os.path.join(upload_folder_base, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            print(f"Error deleting image file {file_path}: {e}")

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
    from app.models import Subject
    subject = Subject.query.get_or_404(subject_id)
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
    return render_template('admin/concepts.html', subject=subject, concepts=concepts) 

@bp.route('/concept/delete/<int:concept_id>', methods=['POST'])
@admin_required
def delete_concept(concept_id):
    from app.models import Concept
    concept = Concept.query.get_or_404(concept_id)
    subject_id = concept.subject_id
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
            return render_template('admin/add_question.html', concept=concept)
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
    return render_template('admin/add_question.html', concept=concept)

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
    from app.models import Concept, Step, Question, PromptTemplate
    concept = Concept.query.get_or_404(concept_id)
    subject = concept.subject
    prompt_template = PromptTemplate.query.filter_by(name=f'초등 {subject.name} 문제 생성 프롬프트').first()
    if not prompt_template:
        prompt_template = PromptTemplate.query.filter_by(name='초등 일반 과목 문제 생성 프롬프트').first()
    if not prompt_template:
        flash("AI 프롬프트 템플릿을 찾을 수 없습니다.", "danger")
        return redirect(url_for('admin.manage_concepts', subject_id=subject.id))
    
    final_prompt_text = prompt_template.content.replace('{{concept_name}}', concept.name)
    Step.query.filter_by(concept_id=concept.id).delete()
    Question.query.filter_by(concept_id=concept.id).delete()
    
    try:
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(final_prompt_text)
        
        # ... (AI 파싱 로직은 동일)
        
        db.session.commit()
        flash(f"'{concept.name}'에 대한 학습 내용이 AI에 의해 생성되었습니다!", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"AI 콘텐츠 생성 중 오류 발생: {e}", 'danger')
        
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
        new_trophy = Trophy(
            name=request.form.get('name'),
            description=request.form.get('description'),
            icon_class=request.form.get('icon_class', 'fas fa-trophy'),
            points=int(request.form.get('points', 0)),
            condition_type=request.form.get('condition_type'),
            condition_value_int=int(request.form.get('condition_value_int')) if request.form.get('condition_value_int') else None,
            condition_value_str=request.form.get('condition_value_str'),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(new_trophy)
        db.session.commit()
        flash(f"새 트로피 '{new_trophy.name}'이(가) 추가되었습니다!", "success")
        return redirect(url_for('admin.manage_trophies'))
    return render_template('admin/add_trophy.html')

@bp.route('/trophy/<int:trophy_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_trophy(trophy_id):
    from app.models import Trophy
    trophy = Trophy.query.get_or_404(trophy_id)
    if request.method == 'POST':
        trophy.name = request.form.get('name')
        trophy.description = request.form.get('description')
        trophy.icon_class = request.form.get('icon_class')
        trophy.points = int(request.form.get('points', 0))
        trophy.condition_type = request.form.get('condition_type')
        trophy.condition_value_int = int(request.form.get('condition_value_int')) if request.form.get('condition_value_int') else None
        trophy.condition_value_str = request.form.get('condition_value_str')
        trophy.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash(f"트로피 '{trophy.name}' 정보가 수정되었습니다.", "success")
        return redirect(url_for('admin.manage_trophies'))
    return render_template('admin/edit_trophy.html', trophy=trophy)

@bp.route('/trophy/<int:trophy_id>/delete', methods=['POST'])
@admin_required
def delete_trophy(trophy_id):
    from app.models import Trophy, UserTrophy
    UserTrophy.query.filter_by(trophy_id=trophy_id).delete()
    trophy = Trophy.query.get_or_404(trophy_id)
    db.session.delete(trophy)
    db.session.commit()
    flash(f"트로피 '{trophy.name}'이(가) 삭제되었습니다.", "success")
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
        db.session.commit()
        flash(f"마스코트 '{mascot_to_edit.name}'의 정보가 수정되었습니다.", "success")
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
    flash(f"마스코트 '{mascot_to_delete.name}'이(가) 삭제되었습니다.", "success")
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
        new_prompt = PromptTemplate(
            name=request.form.get('name'),
            subject_id=int(request.form.get('subject_id')) if request.form.get('subject_id') else None,
            content=request.form.get('content'),
            notes=request.form.get('notes'),
            is_default_for_subject=request.form.get('is_default_for_subject') == 'on'
        )
        db.session.add(new_prompt)
        db.session.commit()
        flash(f"새 프롬프트 템플릿 '{new_prompt.name}'이(가) 추가되었습니다!", "success")
        return redirect(url_for('admin.manage_prompt_templates'))
    return render_template('admin/add_prompt_template.html', subjects=subjects)

@bp.route('/prompt/<int:prompt_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_prompt_template(prompt_id):
    from app.models import PromptTemplate, Subject
    prompt = PromptTemplate.query.get_or_404(prompt_id)
    subjects = Subject.query.order_by(Subject.name).all()
    if request.method == 'POST':
        prompt.name = request.form.get('name')
        prompt.subject_id = int(request.form.get('subject_id')) if request.form.get('subject_id') else None
        prompt.content = request.form.get('content')
        prompt.notes = request.form.get('notes')
        prompt.is_default_for_subject = request.form.get('is_default_for_subject') == 'on'
        db.session.commit()
        flash(f"프롬프트 템플릿 '{prompt.name}'이(가) 수정되었습니다.", "success")
        return redirect(url_for('admin.manage_prompt_templates'))
    return render_template('admin/edit_prompt_template.html', prompt=prompt, subjects=subjects)

@bp.route('/prompt/<int:prompt_id>/delete', methods=['POST'])
@admin_required
def delete_prompt_template(prompt_id):
    from app.models import PromptTemplate
    prompt = PromptTemplate.query.get_or_404(prompt_id)
    db.session.delete(prompt)
    db.session.commit()
    flash(f"프롬프트 템플릿 '{prompt.name}'이(가) 삭제되었습니다.", "success")
    return redirect(url_for('admin.manage_prompt_templates'))
    
