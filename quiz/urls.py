from django.urls import path
from . import views

urlpatterns = [
    path('concept_select/', views.concept_select, name='concept_select'),
    path('wrong_note/', views.wrong_note, name='wrong_note'),
    # ... (기타 문제풀기, 과목선택, 오답풀이 등)
]
