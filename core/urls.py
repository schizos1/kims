from django.urls import path
from . import views, views_quiz, views_learn

urlpatterns = [
    path('', views.quick_login, name='quick_login'),
    path('login/<str:username>/', views.quick_login_action, name='quick_login_action'),
    path('student_dashboard/', views_quiz.student_dashboard, name='student_dashboard'),
    path('admin_dashboard/', views_quiz.admin_dashboard, name='admin_dashboard'),
    path('learn/', views_learn.learn_home, name='learn_home'),
]

