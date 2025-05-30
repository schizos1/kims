from django.urls import path
from . import views

urlpatterns = [
    path('', views.mypage, name='mypage'),  # ★ 주소를 ''(빈 문자열)로!
    # ... (프로필수정/테마선택 등)
]
