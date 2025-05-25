# app/utils.py

import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

# --- 이미지 처리 관련 헬퍼 함수들 ---

def allowed_file(filename):
    """업로드된 파일의 확장자가 허용된 확장자인지 확인합니다."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set()) # ALLOWED_EXTENSIONS가 없을 경우 대비

def save_image(file_storage, subfolder='questions'):
    """
    파일을 안전하게 저장하고 고유한 파일명을 반환합니다.
    subfolder에 따라 저장 위치가 달라집니다.
    (예: 'questions', 'mascots', 'trophies')
    """
    if file_storage and file_storage.filename != '' and allowed_file(file_storage.filename):
        original_filename = secure_filename(file_storage.filename)
        ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        upload_folder_base = None
        # 각 업로드 폴더 설정은 config.py 또는 app.config 에서 가져오는 것이 좋습니다.
        # 여기서는 current_app.root_path를 기준으로 상대 경로를 사용합니다.
        if subfolder == 'mascots':
            upload_folder_base = os.path.join(current_app.root_path, 'static/images/mascots')
        elif subfolder == 'trophies':
            upload_folder_base = current_app.config.get('UPLOAD_FOLDER_TROPHIES', 
                                                     os.path.join(current_app.root_path, 'static/uploads/trophies'))
        else: # 기본은 questions
            upload_folder_base = current_app.config.get('UPLOAD_FOLDER_QUESTIONS', 
                                                     os.path.join(current_app.root_path, 'static/uploads/questions'))

        try:
            os.makedirs(upload_folder_base, exist_ok=True)
            file_path = os.path.join(upload_folder_base, unique_filename)
            file_storage.save(file_path)
            return unique_filename
        except Exception as e:
            print(f"Error saving image to {file_path}: {e}")
            # 필요시 여기서 flash 메시지를 직접 생성하거나 예외를 다시 발생시킬 수 있습니다.
            # flash(f"이미지 저장 중 오류 발생: {e}", "danger")
            return None
    return None

def delete_image_file(filename, subfolder='questions'):
    """지정된 파일을 삭제합니다."""
    if filename:
        upload_folder_base = None
        if subfolder == 'mascots':
            upload_folder_base = os.path.join(current_app.root_path, 'static/images/mascots')
        elif subfolder == 'trophies':
            upload_folder_base = current_app.config.get('UPLOAD_FOLDER_TROPHIES', 
                                                     os.path.join(current_app.root_path, 'static/uploads/trophies'))
        else: # 기본은 questions
            upload_folder_base = current_app.config.get('UPLOAD_FOLDER_QUESTIONS', 
                                                     os.path.join(current_app.root_path, 'static/uploads/questions'))
            
        file_path = os.path.join(upload_folder_base, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            print(f"Error deleting image file {file_path}: {e}")
            # flash(f"이미지 파일 삭제 중 오류 발생: {e}", "danger")