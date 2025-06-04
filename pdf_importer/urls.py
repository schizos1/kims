# pdf_importer/urls.py
from django.urls import path
from . import views # pdf_importer 앱의 views.py

app_name = 'pdf_importer'

urlpatterns = [
    # 예시 URL: /importer/admin/process/ (프로젝트 urls.py에서 'importer/'로 include 했다고 가정)
    path('admin/process/', views.admin_pdf_processor_view, name='admin_pdf_process'),
]