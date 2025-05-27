# ============================================
# 📄 FILE: core/views_learn.py
# 📝 DESCRIPTION: 개념 학습 시작 뷰
# ============================================

from django.shortcuts import render, get_object_or_404
from core.models import ConceptLesson

def learn_start_view(request):
    lessons = ConceptLesson.objects.filter(is_published=True).order_by('subject', 'grade')
    
    # 과목별로 그룹핑
    subject_map = {}
    for lesson in lessons:
        subject_map.setdefault(lesson.subject, []).append(lesson)

    return render(request, 'core/learn_start.html', {
        'subject_map': subject_map
    })
def learn_detail_view(request, subject, lesson_id):
    lesson = get_object_or_404(ConceptLesson, id=lesson_id, subject=subject, is_published=True)

    return render(request, 'core/learn_detail.html', {
        'lesson': lesson,
    })