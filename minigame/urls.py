from django.urls import path
from . import views

urlpatterns = [
    path('', views.minigame_index, name='minigame_index'),
    path('play/<str:game_name>/', views.play_game, name='play_game'),
    # ... (게임별 상세 등)
]
