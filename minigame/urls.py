from django.urls import path
from minigame.api_views import update_number_shooter_score
from . import views

app_name = 'minigame'
urlpatterns = [
    path('', views.minigame_index, name='minigame_index'),
    path('play/<str:game_key>/', views.play_game, name='play_game'),
    path('play/eat_food/', views.play_game, {'game_key':'eat_food'}, name='play_eat_food'),
    path('play/fishing/', views.play_game, {'game_key':'fishing'}, name='play_fishing'),
    path('play/number_shooter/', views.play_game, {'game_key':'number_shooter'}, name='play_number_shooter'),
    path('api/number_shooter/update_score/', update_number_shooter_score, name='update_number_shooter_score'),
]