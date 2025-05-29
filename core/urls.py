from django.urls import path
from . import views

urlpatterns = [
    path('', views.quick_login, name='quick_login'),
    path('login/<str:username>/', views.quick_login_action, name='quick_login_action'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
