# app/views/admin_views.py

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from functools import wraps
from flask_login import current_user
from werkzeug.utils import secure_filename
import uuid 

import google.generativeai as genai
import re
from textwrap import dedent

from app import db
# --- ★★★ UserTrophy 모델 임포트 추가 ★★★ ---
from app.models import Subject, Concept, Step, Question, Trophy, UserTrophy

bp = Blueprint('admin', __name__, url_prefix='/admin')

# ... (admin_required, allowed_file, save_image, delete_image_file 및 다른 라우트 함수들은 이전과 동일) ...
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
        upload_folder_key = f'UPLOAD_FOLDER_{subfolder.upper()}'
        upload_folder_base = current_app.config.get('UPLOAD_FOLDER_QUESTIONS', 
                                                os.path.join(current_app.root_path, 'static/uploads/questions'))
        if subfolder != 'questions' and upload_folder_key in current_app.config:
             upload_folder_base = current_app.config[upload_folder_key]
        os.makedirs(upload_folder_base, exist_ok=True)
        file_path = os.path.join(upload_folder_base, unique_filename)
        file_storage.save(file_path)
        return unique_filename
    return None

def delete_image_file(filename, subfolder='questions'):
    if filename:
        upload_folder_key = f'UPLOAD_FOLDER_{subfolder.upper()}'
        upload_folder_base = current_app.config.get('UPLOAD_FOLDER_QUESTIONS', 
                                                os.path.join(current_app.root_path, 'static/uploads/questions'))
        if subfolder != 'questions' and upload_folder_key in current_app.config:
             upload_folder_base = current_app.config[upload_folder_key]
        file_path = os.path.join(upload_folder_base, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted image file: {file_path}")
        except OSError as e:
            print(f"Error deleting image file {file_path}: {e}")

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
    return render_template('admin/concepts.html', subject=subject, concepts=concepts)

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

@bp.route('/concept/<int:concept_id>/question/add', methods=['GET', 'POST'])
@admin_required
def add_question(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    if request.method == 'POST':
        content = request.form.get('content')
        question_type = request.form.get('question_type')
        answer = request.form.get('answer')
        source_type = request.form.get('source_type')
        if not content or not question_type or not answer or not source_type:
            flash('문제 내용, 유형, 정답, 출처는 모두 필수입니다.', 'danger')
            return render_template('admin/add_question.html', concept=concept)
        image_filename_main = save_image(request.files.get('image_filename'))
        option_texts = [request.form.get(f'option{i}') for i in range(1, 5)]
        option_images_filenames = [save_image(request.files.get(f'option{i}_img')) for i in range(1, 5)]
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
        try:
            db.session.commit()
            flash(f"'{concept.name}' 개념에 새 문제가 성공적으로 추가되었습니다!", "success")
            return redirect(url_for('admin.manage_questions', concept_id=concept.id))
        except Exception as e:
            db.session.rollback()
            flash(f"문제 추가 중 오류 발생: {e}", "danger")
            print(f"Error adding question: {e}")
    return render_template('admin/add_question.html', concept=concept)

@bp.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_question(question_id):
    question_to_edit = Question.query.get_or_404(question_id)
    concept = question_to_edit.concept
    if request.method == 'POST':
        question_to_edit.content = request.form.get('content')
        question_to_edit.question_type = request.form.get('question_type')
        question_to_edit.answer = request.form.get('answer')
        question_to_edit.source_type = request.form.get('source_type')
        if request.form.get('delete_image_filename'):
            delete_image_file(question_to_edit.image_filename)
            question_to_edit.image_filename = None
        elif 'image_filename' in request.files and request.files['image_filename'].filename != '':
            delete_image_file(question_to_edit.image_filename)
            new_filename = save_image(request.files['image_filename'])
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
                delete_image_file(getattr(question_to_edit, current_img_attr_name))
                setattr(question_to_edit, current_img_attr_name, None)
            elif option_img_field_name in request.files and request.files[option_img_field_name].filename != '':
                delete_image_file(getattr(question_to_edit, current_img_attr_name))
                new_option_filename = save_image(request.files[option_img_field_name])
                if new_option_filename:
                    setattr(question_to_edit, current_img_attr_name, new_option_filename)
                else:
                    flash(f'보기 {i} 이미지 업로드 실패. 파일 형식을 확인하세요.', 'danger')
                    return render_template('admin/edit_question.html', question=question_to_edit, concept=concept)
        try:
            db.session.commit()
            flash(f"문제(ID: {question_to_edit.id})가 성공적으로 수정되었습니다.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"문제 수정 중 오류 발생: {e}", "danger")
            print(f"Error editing question: {e}")
        return redirect(url_for('admin.manage_questions', concept_id=question_to_edit.concept_id))
    return render_template('admin/edit_question.html', question=question_to_edit, concept=concept)

@bp.route('/question/<int:question_id>/delete', methods=['POST'])
@admin_required
def delete_question(question_id):
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
    try:
        db.session.commit()
        for filename in image_filenames_to_delete:
            delete_image_file(filename)
        flash(f"문제(ID: {question_to_delete.id})가 삭제되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"문제 삭제 중 오류 발생: {e}", "danger")
        print(f"Error deleting question: {e}")
    return redirect(url_for('admin.manage_questions', concept_id=concept_id))

@bp.route('/concept/<int:concept_id>/generate', methods=['POST'])
@admin_required
def generate_ai_content(concept_id):
    concept = Concept.query.get_or_404(concept_id)
    subject_name_for_prompt = concept.subject.name
    Step.query.filter_by(concept_id=concept.id).delete()
    Question.query.filter_by(concept_id=concept.id).delete()
    ai_response_content = None
    try:
        if not os.getenv('GOOGLE_API_KEY'):
            flash("Google API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.", "danger")
            return redirect(url_for('admin.manage_concepts', subject_id=concept.subject_id))
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        is_math_subject = "수학" in subject_name_for_prompt or "산수" in subject_name_for_prompt or "계산" in subject_name_for_prompt
        if is_math_subject:
            question_type_instruction = "객관식 문제 10개를 만들어주세요. 각 문제는 질문(Q), 4개의 보기 (O1, O2, O3, O4), 그리고 정답 보기의 번호(A)를 포함해야 합니다."
            example_qa_format = dedent("""Q: 2 + 3 = ?\nO1: 4\nO2: 5\nO3: 6\nO4: 7\nA: 2""")
        else:
            question_type_instruction = "이 개념을 이해했는지 확인할 수 있는 다양한 유형의 총 10개 예제 문제와 그에 대한 정답 또는 모범 답안을 제공해주세요. 객관식 문제(Q, O1, O2, O3, O4, A 형식)와 단답형 주관식 문제(Q, A 형식)를 섞어도 좋습니다."
            example_qa_format = dedent("""예시 1 (객관식):\nQ: 다음 중 식물의 광합성에 필요한 요소가 아닌 것은 무엇일까요?\nO1: 햇빛\nO2: 물\nO3: 이산화탄소\nO4: 바람\nA: 4\n\n예시 2 (단답형):\nQ: 물이 얼음으로 변하는 현상을 무엇이라고 하나요?\nA: 응고""")
        prompt = dedent(f"""당신은 대한민국 초등학생을 가르치는 친절하고 유능한 '{subject_name_for_prompt}' 과목 선생님입니다.
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
        (이런 식으로 Q/A 또는 Q/O1-O4/A 쌍을 총 10개 생성)""")
        print(f"--- AI Prompt for {subject_name_for_prompt} - {concept.name} ---\n{prompt}\n------------------------------------")
        response = model.generate_content(prompt)
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
                o1_match = re.search(r"\n\s*O1:\s*(.*?)(?=\n\s*O2:)", block, re.DOTALL)
                o2_match = re.search(r"\n\s*O2:\s*(.*?)(?=\n\s*O3:)", block, re.DOTALL)
                o3_match = re.search(r"\n\s*O3:\s*(.*?)(?=\n\s*O4:)", block, re.DOTALL)
                o4_match = re.search(r"\n\s*O4:\s*(.*?)(?=\n\s*A:)", block, re.DOTALL)
                a_mc_match = re.search(r"\n\s*A:\s*([1-4])(?!\S)", block)
                a_short_match = re.search(r"\n\s*A:\s*(.*)", block, re.DOTALL)
                if o1_match and o2_match and o3_match and o4_match and a_mc_match:
                    questions_data.append({'content': question_text, 'option1': o1_match.group(1).strip(), 'option2': o2_match.group(1).strip(), 'option3': o3_match.group(1).strip(), 'option4': o4_match.group(1).strip(), 'answer': a_mc_match.group(1).strip(), 'type': 'multiple_choice'})
                elif a_short_match:
                    questions_data.append({'content': question_text, 'option1': None, 'option2': None, 'option3': None, 'option4': None, 'answer': a_short_match.group(1).strip(), 'type': 'short_answer'})
        step_order = 1
        for step_info in steps_data:
            new_step = Step(title=step_info['title'], explanation=step_info['explanation'], step_order=step_order, concept_id=concept.id)
            db.session.add(new_step)
            step_order += 1
        for q_info in questions_data:
            new_question = Question(content=q_info['content'], option1=q_info.get('option1'), option2=q_info.get('option2'), option3=q_info.get('option3'), option4=q_info.get('option4'), answer=q_info['answer'], question_type=q_info['type'], concept_id=concept.id, source_type='ai_generated')
            db.session.add(new_question)
        if not steps_data and not questions_data:
            flash(f"AI가 '{concept.name}'에 대한 학습 내용을 생성하지 못했거나, 응답에서 유효한 데이터를 파싱하지 못했습니다. AI 응답 로그를 확인해주세요.", 'warning')
        else:
            db.session.commit()
            flash(f"'{concept.name}' ({concept.subject.name})에 대한 학습 내용이 AI에 의해 성공적으로 생성되었습니다! ({len(steps_data)}개 단계, {len(questions_data)}개 문제)", 'success')
        return redirect(url_for('admin.manage_concepts', subject_id=concept.subject_id))
    except Exception as e:
        db.session.rollback()
        flash(f"AI 콘텐츠 생성 중 심각한 오류가 발생했습니다 ({concept.name}): {e}", 'danger')
        print(f"AI Error in generate_ai_content (Exception Block): {e}")
        if ai_response_content: 
            print(f"AI Response Content (on error in except block): {ai_response_content}")
        return redirect(url_for('admin.manage_concepts', subject_id=concept.subject_id))

# --- ★★★ 트로피 관리 CRUD 함수들 ★★★ ---
@bp.route('/trophy/add', methods=['GET', 'POST'])
@admin_required
def add_trophy():
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
            return render_template('admin/add_trophy.html', form_data=request.form) # 오류 시 입력값 유지
        
        try:
            points = int(points_str)
        except ValueError:
            flash('획득 포인트는 숫자로 입력해야 합니다.', 'danger')
            return render_template('admin/add_trophy.html', form_data=request.form)

        condition_value_int = None
        if condition_value_int_str: # 빈 문자열이 아닐 때만 변환 시도
            try:
                condition_value_int = int(condition_value_int_str)
            except ValueError:
                flash('조건 숫자 값은 유효한 숫자로 입력해야 합니다.', 'danger')
                return render_template('admin/add_trophy.html', form_data=request.form)

        # ID는 자동 증가하므로 직접 설정하지 않음
        new_trophy = Trophy(
            name=name,
            description=description,
            icon_class=icon_class,
            points=points,
            condition_type=condition_type if condition_type else None,
            condition_value_int=condition_value_int,
            condition_value_str=condition_value_str if condition_value_str else None,
            is_active=is_active
        )
        db.session.add(new_trophy)
        try:
            db.session.commit()
            flash(f"새 트로피 '{name}'이(가) 성공적으로 추가되었습니다!", "success")
            return redirect(url_for('admin.manage_trophies'))
        except Exception as e:
            db.session.rollback()
            flash(f"트로피 추가 중 오류 발생: {e}", "danger")
            print(f"Error adding trophy: {e}")
            return render_template('admin/add_trophy.html', form_data=request.form) # 오류 시 폼으로
            
    return render_template('admin/add_trophy.html', form_data={})

@bp.route('/trophy/<int:trophy_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_trophy(trophy_id):
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
            return render_template('admin/edit_trophy.html', trophy=trophy_to_edit) # 오류 시 현재 값으로 폼 다시 표시
        
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
            trophy_to_edit.condition_value_int = None # 빈 문자열이면 None으로 저장

        # 빈 문자열이면 None으로 저장 (모델에서 nullable=True 이므로)
        if not trophy_to_edit.condition_type: trophy_to_edit.condition_type = None
        if not trophy_to_edit.condition_value_str: trophy_to_edit.condition_value_str = None

        try:
            db.session.commit()
            flash(f"트로피(ID: {trophy_to_edit.id})가 성공적으로 수정되었습니다.", "success")
            return redirect(url_for('admin.manage_trophies'))
        except Exception as e:
            db.session.rollback()
            flash(f"트로피 수정 중 오류 발생: {e}", "danger")
            print(f"Error editing trophy: {e}")

    return render_template('admin/edit_trophy.html', trophy=trophy_to_edit)

@bp.route('/trophy/<int:trophy_id>/delete', methods=['POST'])
@admin_required
def delete_trophy(trophy_id):
    trophy_to_delete = Trophy.query.get_or_404(trophy_id)
    
    # 이 트로피를 획득한 사용자 기록(UserTrophy)을 먼저 삭제 (외래 키 제약 조건 위반 방지)
    UserTrophy.query.filter_by(trophy_id=trophy_id).delete()
    
    db.session.delete(trophy_to_delete)
    try:
        db.session.commit()
        flash(f"트로피(ID: {trophy_id}, 이름: {trophy_to_delete.name})가 성공적으로 삭제되었습니다.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"트로피 삭제 중 오류 발생: {e}", "danger")
        print(f"Error deleting trophy: {e}")
        
    return redirect(url_for('admin.manage_trophies'))
# --- ★★★ 트로피 관리 CRUD 함수들 끝 ★★★ ---