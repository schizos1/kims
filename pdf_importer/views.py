# pdf_importer/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .forms import PDFUploadForm
import logging
import os
from django.conf import settings
from django.utils.text import get_valid_filename
import json 
import re # 정규 표현식 사용

import fitz  # PyMuPDF 라이브러리

logger = logging.getLogger(__name__)

# 기존 함수 대신 아래 코드로 덮어쓰기!

def parse_extracted_data_to_json(extracted_pages_data):
    question_number_pattern = re.compile(r"^\s*(\d+)\.\s*(.*)")
    choice_pattern = re.compile(r"(①|②|③|④)\s*([^①②③④]+)")
    parsed_questions = []
    current_question = None
    state = "search_question"

    # 페이지 전체 라인화
    lines = []
    for page_data in extracted_pages_data:
        for block in page_data.get("blocks", []):
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    line_text = "".join([span.get("text", "") for span in line.get("spans", [])]).strip()
                    if line_text:
                        lines.append(line_text)

    for line in lines:
        # 문제 시작
        q_match = question_number_pattern.match(line)
        if q_match:
            if current_question:
                parsed_questions.append(current_question)
            current_question = {
                "question_number_detected": q_match.group(1),
                "text": q_match.group(2).strip(),
                "choices": [],
                "explanation": ""
            }
            state = "in_question"
            continue

        # 보기(한 줄에 여러 개 가능)
        choices = choice_pattern.findall(line)
        if choices and current_question:
            for m in choice_pattern.finditer(line):
                current_question["choices"].append(f"{m.group(1)} {m.group(2).strip()}")
            state = "in_choice"
            continue

        # 본문 계속(문제 본문 이어쓰기)
        if current_question and state == "in_question":
            current_question["text"] += " " + line.strip()

    if current_question:
        parsed_questions.append(current_question)

    # choices 중복 정리
    for q in parsed_questions:
        uniq = []
        seen = set()
        for c in q["choices"]:
            if c not in seen:
                uniq.append(c)
                seen.add(c)
        q["choices"] = uniq

    return parsed_questions



@staff_member_required
def admin_pdf_processor_view(request):
    form = PDFUploadForm()
    upload_summary = None
    processed_data_preview = None 

    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            question_pdf_file = request.FILES.get('question_pdf')
            
            summary_lines = []
            extracted_pages_data = [] 
            logger.info("PDF 텍스트 직접 추출 요청 접수됨.")

            if question_pdf_file:
                filename = get_valid_filename(question_pdf_file.name)
                logger.info(f"문제 PDF '{filename}' 텍스트 추출 시작...")
                
                try:
                    pdf_bytes = question_pdf_file.read()
                    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
                    
                    for page_num in range(len(pdf_document)):
                        page = pdf_document.load_page(page_num)
                        # 텍스트 블록과 그 안의 라인, 스팬, 좌표 정보 등을 상세히 추출
                        page_data_dict = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_LIGATURES & ~fitz.TEXT_PRESERVE_WHITESPACE, sort=True)
                        # flags 옵션으로 리가처(합자) 해제, 불필요한 공백 제거 시도, sort로 읽기 순서 정렬
                        
                        extracted_pages_data.append({
                            "page_number": page_num + 1,
                            "blocks": page_data_dict.get("blocks", []) # 블록 정보 저장
                        })
                        logger.debug(f"페이지 {page_num + 1} 텍스트 구조 정보 추출 완료.")
                    
                    pdf_document.close()
                    
                    if extracted_pages_data:
                        summary_lines.append(f"문제 PDF '{filename}': 텍스트 구조 정보 추출 완료.")
                        
                        logger.info("추출된 데이터로 문제/보기 파싱 시작...")
                        parsed_questions = parse_extracted_data_to_json(extracted_pages_data) # ✨ 새 파싱 함수 호출 ✨
                        
                        if parsed_questions:
                            # 파싱된 결과를 JSON으로 변환하여 미리보기에 표시
                            processed_data_preview = json.dumps(parsed_questions, ensure_ascii=False, indent=2)
                            summary_lines.append(f"{len(parsed_questions)}개의 문제 구조를 인식했습니다.")
                        else:
                            processed_data_preview = "문제 구조를 인식하지 못했습니다.\n\n(참고: 추출된 원본 텍스트 구조는 서버 로그에서 page_get_text_dict_output.json 파일로 확인 가능합니다.)"
                            # 원본 전체 데이터는 너무 길어서 여기서 직접 보여주기 어려울 수 있음
                            # 필요하다면 파일로 저장하고 그 경로를 안내
                            # with open("page_get_text_dict_output.json", "w", encoding="utf-8") as f:
                            #    json.dump(extracted_pages_data, f, ensure_ascii=False, indent=2)

                    else:
                        summary_lines.append(f"문제 PDF '{filename}': 텍스트 정보를 추출하지 못했습니다.")

                except Exception as e:
                    logger.error(f"PDF 파일 '{filename}' 처리 중 오류: {e}", exc_info=True)
                    messages.error(request, f"'{filename}' 파일 처리 중 오류가 발생했습니다: {e}")
                    summary_lines.append(f"문제 PDF '{filename}': 처리 중 오류 발생.")
            
            if not summary_lines:
                 summary_lines.append("처리할 PDF 파일이 없었습니다.")
            
            upload_summary = "\n".join(summary_lines)
            messages.success(request, "PDF 처리 및 분석 시도가 완료되었습니다.")
            form = PDFUploadForm() 
        else:
            messages.error(request, "파일 업로드 중 오류가 발생했습니다. 폼 에러를 확인해주세요.")
            logger.error(f"PDF 업로드 폼 유효성 검사 실패: {form.errors.as_json()}")

    context = {
        'form': form,
        'upload_summary': upload_summary,
        'processed_data_preview': processed_data_preview, 
        'title': '기출문제 PDF 분석기 (문제/보기 추출)', 
        'has_permission': request.user.is_active and request.user.is_staff,
    }
    return render(request, 'pdf_importer/admin_pdf_upload.html', context)