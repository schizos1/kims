from django.urls import path
from . import views

urlpatterns = [
    path('mypage/', views.mypage, name='mypage'),
    # ... (프로필수정/테마선택 등)
]
