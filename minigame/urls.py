# 파일 경로: /home/schizos/study_site/minigame/urls.py
# 파일 설명: Django 미니게임 앱의 URL 라우팅 설정
#
# 이 파일은 minigame 앱으로 들어오는 URL 요청들을 분석하여,
# 해당하는 View 함수로 연결해주는 역할을 합니다.
#
# - 주요 경로:
#   - '' (앱의 루트 경로): 미니게임 전체 목록을 보여주는 인덱스 페이지로 연결합니다.
#   - 'play/<str:game_key>/': 가장 핵심적인 경로. 게임의 고유 키(game_key)를 받아
#     하나의 View(play_game)에서 모든 게임의 진입을 동적으로 처리합니다.
#
# - 수정 사항 (2025-06-08):
#   - 중복되거나 충돌을 일으킬 수 있는 URL 경로들을 정리했습니다.
#   - 'play/<str:game_key>/' 경로가 'typing_game'을 포함한 모든 게임을 처리할 수 있음을 명확히 하고, 불필요한 경로를 제거했습니다.

from django.urls import path
from minigame.api_views import update_number_shooter_score
from . import views

app_name = 'minigame'

urlpatterns = [
    # 1. 미니게임 인덱스 페이지
    # 예: /minigame/
    path('', views.minigame_index, name='minigame_index'),

    # 2. 모든 게임을 위한 동적 진입 경로 (가장 효율적인 방식)
    # 'typing_game'을 포함한 모든 게임은 이 하나의 경로로 처리됩니다.
    # 예: /minigame/play/typing_game/, /minigame/play/fishing/ 등
    path('play/<str:game_key>/', views.play_game, name='play_game'),

    # 3. API 경로
    # 게임 내부에서 서버와 통신이 필요할 때 사용하는 경로입니다.
    path('api/number_shooter/update_score/', update_number_shooter_score, name='update_number_shooter_score'),


    # --- 아래 경로들은 정리되었습니다 ---

    # 비고: 아래의 하드코딩된 경로들은 위의 'play/<str:game_key>/' 동적 경로와 기능이 중복됩니다.
    # 특정 게임에 대해 별도의 URL 이름(name)이 필요한 경우가 아니라면, 동적 경로 하나로 충분합니다.
    # path('play/eat_food/', views.play_game, {'game_key':'eat_food'}, name='play_eat_food'),
    # path('play/fishing/', views.play_game, {'game_key':'fishing'}, name='play_fishing'),
    # path('play/number_shooter/', views.play_game, {'game_key':'number_shooter'}, name='play_number_shooter'),

    # 오류 수정: 아래 경로는 'play/<str:game_key>/'와 URL 이름('play_game')이 중복되고,
    # 너무 광범위하여 다른 경로와 충돌할 수 있으므로 제거했습니다.
    # path('<str:game_key>/', views.play_game, name='play_game'),
]