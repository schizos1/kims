from django.urls import path
from . import views

app_name = 'minigame'
urlpatterns = [
    path('', views.minigame_index, name='minigame_index'),
    path('play/<str:game_key>/', views.play_game, name='play_game'),
    path('fishing/', views.fishing_game, name='minigame_fishing'),
    path('play/eat_food/', views.play_game, {'game_key':'eat_food'}, name='play_eat_food'),
]