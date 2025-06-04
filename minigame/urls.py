# minigame/urls.py (수정 후)

from django.urls import path
from . import views

app_name = 'minigame'
urlpatterns = [
    path('', views.minigame_index, name='minigame_index'),
    path('play/<str:game_key>/', views.play_game, name='play_game'),
    path('<str:game_key>/', views.play_game, name='play_game'),
    # 👇 'game_name'을 'game_key'로 변경했습니다.
    path('play/eat_food/', views.play_game, {'game_key':'eat_food'}, name='play_eat_food'),
    path('fishing/', views.fishing_game, name='minigame_fishing'),
]