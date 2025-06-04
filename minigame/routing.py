# minigame/routing.py
# 이 파일은 minigame 앱의 WebSocket URL 라우팅 설정을 담당합니다.
# 클라이언트의 WebSocket 요청 URL에 따라 적절한 Consumer로 연결합니다.

from django.urls import re_path

# 기존 consumers.EatFoodConsumer는 분리되었으므로 더 이상 직접 사용하지 않습니다.
# from . import consumers # 주석 처리 또는 삭제

# 새로 생성된 게임별, 모드별 컨슈머들을 임포트합니다.
# 'eat_food' 게임의 싱글 및 멀티플레이어 컨슈머
from .games.eat_food import single_consumer as eat_food_single_player_consumer
from .games.eat_food import multi_consumer as eat_food_multi_player_consumer

# (향후 추가될 로비 컨슈머 임포트 예시)
# from .lobby import consumer as lobby_consumer

websocket_urlpatterns = [
    # 기존 EatFoodConsumer 라우트는 주석 처리 또는 삭제합니다.
    # re_path(r'ws/minigame/(?P<room_id>\w+)/$', consumers.EatFoodConsumer.as_asgi()),

    # --- 'eat_food' 게임을 위한 WebSocket 경로 ---
    # 1. 'eat_food' 싱글플레이어 모드 경로
    #    예: ws://localhost:8000/ws/minigame/games/eat_food/single/
    re_path(
        r'ws/minigame/games/eat_food/single/$', 
        eat_food_single_player_consumer.EatFoodSinglePlayerConsumer.as_asgi()
    ),

    # 2. 'eat_food' 멀티플레이어 모드 경로
    #    room_id를 URL 파라미터로 받아 해당 방으로 연결합니다.
    #    예: ws://localhost:8000/ws/minigame/games/eat_food/multi/some_room_name/
    re_path(
        r'ws/minigame/games/eat_food/multi/(?P<room_id>\w+)/$', 
        eat_food_multi_player_consumer.EatFoodMultiPlayerConsumer.as_asgi()
    ),

    # --- (향후 추가) 멀티플레이어 로비 경로 ---
    # 예: ws://localhost:8000/ws/minigame/lobby/
    # re_path(r'ws/minigame/lobby/$', lobby_consumer.LobbyConsumer.as_asgi()),
    
    # --- 다른 미니게임들을 위한 경로도 유사한 방식으로 추가할 수 있습니다 ---
    # 예: ws/minigame/games/another_game/single/
    # 예: ws/minigame/games/another_game/multi/<room_id>/
]