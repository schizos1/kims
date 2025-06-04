# pdf_importer/forms.py

from django import forms

class PDFUploadForm(forms.Form):
    question_pdf = forms.FileField(
        label='문제 PDF 파일', 
        help_text='문제 내용이 포함된 PDF 파일을 업로드하세요.',
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf'})
    )
    answer_pdf = forms.FileField(
        label='정답 PDF 파일 (선택 사항)', 
        help_text='정답만 별도로 있는 PDF 파일이 있다면 업로드하세요.',
        required=False,
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf'})
    )
    # 추가적인 처리 옵션 필드 (예시)
    # source_description = forms.CharField(
    #     label='출처 설명 (예: 2024년 1회 기출)', 
    #     max_length=100, 
    #     required=False,
    #     help_text='업로드하는 PDF의 출처나 설명을 간략히 적어주세요.'
    # )