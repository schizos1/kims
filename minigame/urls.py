# minigame/urls.py

from django.urls import path
from . import views # minigame 앱의 views.py

app_name = 'minigame' # 네임스페이스는 이미 잘 설정되어 있습니다.

urlpatterns = [
    # 기존: path('', views.minigame_index, name='minigame_index'),
    # 변경: name을 'minigame_lobby'로 수정하여 템플릿과 일치시킵니다.
    # 이 경로는 /minigame/ 으로 접속 시 미니게임 목록/선택 페이지(로비)를 보여줍니다.
    path('', views.minigame_index, name='minigame_lobby'), 

    # 특정 게임 플레이 경로 (이 부분은 그대로 유지)
    path('play/<str:game_name>/', views.play_game, name='play_game'),
    
    # ... (다른 미니게임 관련 URL 패턴이 있다면 여기에 추가)
]