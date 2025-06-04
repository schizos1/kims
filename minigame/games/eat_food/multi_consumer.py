# minigame/games/eat_food/multi_consumer.py
# 이 파일은 'eat_food' 미니게임의 멀티플레이어 모드를 위한 WebSocket 컨슈머입니다.
# 여러 플레이어가 'room'을 기반으로 함께 게임을 즐길 수 있도록 합니다.

import asyncio
import json
import random 
import uuid   

from channels.generic.websocket import AsyncWebsocketConsumer
from . import config as eat_food_config 
from . import logic as eat_food_logic   

rooms = {} 

class EatFoodMultiPlayerConsumer(AsyncWebsocketConsumer):
    """
    EatFood 미니게임의 멀티플레이어 버전 컨슈머.
    플레이어들은 room_id를 통해 같은 게임 세션에 참여합니다.
    """

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs'].get('room_id', 'default_eat_food_room')
        self.room_group_name = f'eat_food_multi_{self.room_id}'
        self.user = None 

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"DEBUG (MultiPlayer Connect): Player {self.channel_name} connected to room {self.room_id} (Group: {self.room_group_name})")

        if self.room_id not in rooms:
            rooms[self.room_id] = {
                'players': {}, 'foods': [], 'npcs': [], 'obstacles': [],
                'game_started': False, 'game_winner': None,
                'tasks': {'game_loop_task': None, 'obstacle_update_task': None} # 통합된 게임 루프 사용
            }
            print(f"DEBUG (MultiPlayer Connect): Room {self.room_id} created.")
        
        await self.send(text_data=json.dumps({
            "action": "connection_established",
            "message": f"멀티플레이어 게임 방 '{self.room_id}'에 연결되었습니다. 'join' 메시지로 게임에 참여하세요."
        }))

    async def disconnect(self, close_code):
        print(f"DEBUG (MultiPlayer Disconnect): Player {self.channel_name} attempting to disconnect from room {self.room_id}. Code: {close_code}")

        room_state = rooms.get(self.room_id)
        if room_state:
            player_data = room_state['players'].pop(self.channel_name, None)
            if player_data:
                disconnected_user_name = player_data.get('user', 'Unknown Player')
                print(f"DEBUG (MultiPlayer Disconnect): Player {disconnected_user_name} ({self.channel_name}) removed from room {self.room_id}.")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'broadcast_system_message', 'message': f"{disconnected_user_name}님이 퇴장했습니다."}
                )
            
            if not room_state['players'] and self.room_id in rooms: # 방이 비었고, 아직 삭제되지 않았다면
                print(f"DEBUG (MultiPlayer Disconnect): Room {self.room_id} is now empty. Cleaning up.")
                for task_name, task in list(room_state['tasks'].items()): # list로 복사하여 순회 중 변경에 안전하게
                    if task and not task.done():
                        task.cancel()
                        print(f"DEBUG (MultiPlayer Disconnect): Task '{task_name}' for room {self.room_id} cancelled.")
                if self.room_id in rooms: # 최종 확인 후 삭제
                    del rooms[self.room_id]
                    print(f"DEBUG (MultiPlayer Disconnect): Room {self.room_id} deleted.")
            elif room_state['players']: # 아직 플레이어가 남아있으면 상태 업데이트
                 await self._broadcast_current_game_state(self.room_id)

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if self.room_id not in rooms and action != "join": # join 액션은 방 생성 가능성 있음
                 # join이 아닌데 방이 없다면 오류 (방이 막 삭제된 직후일 수 있음)
                if self.room_id not in rooms: # 재확인
                    await self.send_error_message(f"게임 방 '{self.room_id}'을 찾을 수 없거나 이미 종료되었습니다.")
                    return

            # join 액션의 경우, connect에서 방이 없으면 생성하므로 room_state는 항상 존재한다고 가정 가능
            # 단, 동시 접속 등으로 rooms[self.room_id] 접근 시점에 없을 수도 있으므로 get으로 안전하게 접근
            room_state = rooms.get(self.room_id)
            if not room_state and action == "join": # 방이 아직 생성 안됐는데 join 요청이 먼저 온 경우 (이론상 connect에서 처리)
                # 이 경우는 connect에서 rooms[self.room_id]를 생성하므로, 여기 도달 시 room_state는 있어야 함
                # 만약 그럼에도 없다면 로직 오류 또는 심각한 경쟁상태
                print(f"WARN (MultiPlayer Receive): Room {self.room_id} not found for join action, should have been created in connect.")
                # 안전하게 한번 더 시도 (또는 오류 처리)
                if self.room_id not in rooms:
                    rooms[self.room_id] = {
                        'players': {}, 'foods': [], 'npcs': [], 'obstacles': [],
                        'game_started': False, 'game_winner': None,
                        'tasks': {'game_loop_task': None, 'obstacle_update_task': None}
                    }
                room_state = rooms[self.room_id]


            if action == "join":
                if self.channel_name in room_state['players']:
                    await self.send_error_message("이미 게임에 참여했습니다.")
                    return

                self.user = data.get("user", f"Player_{random.randint(100,999)}")
                player_char_img_path = data.get("charImgPath", "dino1.png")
                
                player_count = len(room_state['players'])
                initial_player_x = eat_food_config.CANVAS_WIDTH * (0.25 + (player_count * 0.5)) 
                initial_player_y = eat_food_config.CANVAS_HEIGHT / 2

                room_state['players'][self.channel_name] = {
                    "id": self.channel_name, "user": self.user, "x": initial_player_x, "y": initial_player_y,
                    "score": 0, "eatCount": 0, "charImgPath": player_char_img_path,
                    "collision_r": eat_food_config.PLAYER_COLLISION_RADIUS
                }
                print(f"DEBUG (MultiPlayer Join): Player {self.user} ({self.channel_name}) joined room {self.room_id}. Total players: {len(room_state['players'])}")

                await self.channel_layer.group_send(
                    self.room_group_name, {'type': 'broadcast_system_message', 'message': f"{self.user}님이 입장했습니다!"})

                min_players_to_start = 1 # 테스트용. 실제로는 2 권장
                if len(room_state['players']) >= min_players_to_start and not room_state['game_started']:
                    await self._start_game_for_room(self.room_id)
                else:
                    await self._broadcast_current_game_state(self.room_id) # 다른 플레이어에게 새 플레이어 정보 포함된 상태 전송

            elif room_state and room_state.get('game_started'): # 게임 시작된 방에서만 유효한 액션
                if action == "move" and self.channel_name in room_state['players']:
                    await self._handle_player_move(room_state, data.get("player"))
                elif action == "eatAttempt" and self.channel_name in room_state['players']:
                    await self._handle_eat_attempt(room_state, data.get("foodId"))
            
            if action == "chat" and self.user: # 채팅은 게임 시작 여부와 무관
                message_text = data.get("message", "")
                if message_text:
                    await self.channel_layer.group_send(
                        self.room_group_name, {'type': 'broadcast_chat_message', 'user': self.user, 'message': message_text})
            
        except json.JSONDecodeError:
            print(f"ERROR (MultiPlayer Receive): Invalid JSON from {self.channel_name}")
            await self.send_error_message("잘못된 JSON 형식입니다.")
        except Exception as e:
            print(f"ERROR (MultiPlayer Receive): Exception for {self.channel_name} in room {self.room_id} - {e}")
            import traceback; traceback.print_exc()
            await self.send_error_message(f"오류가 발생했습니다: {str(e)}")


    async def _start_game_for_room(self, room_id):
        room_state = rooms.get(room_id)
        if not room_state or room_state['game_started']: return

        print(f"DEBUG (MultiPlayer StartGame): Starting game for room {room_id}")
        room_state['game_started'] = True
        room_state['game_winner'] = None

        # logic.py를 사용하여 게임 요소 초기화
        eat_food_logic.initialize_foods(room_state, eat_food_config.INITIAL_FOOD_COUNT)
        eat_food_logic.initialize_npcs(room_state, eat_food_config.INITIAL_NPC_COUNT)
        eat_food_logic.initialize_obstacles(room_state, eat_food_config.OBSTACLE_COUNT) # 최초 장애물 생성
        print(f"DEBUG (MultiPlayer StartGame): Elements initialized for room {room_id}. Foods: {len(room_state['foods'])}, NPCs: {len(room_state['npcs'])}, Obstacles: {len(room_state['obstacles'])}")

        start_info_payload = {
            'type': 'broadcast_game_start_info',
            'initial_foods': room_state['foods'], 'initial_npcs': room_state['npcs'], 
            'initial_obstacles': room_state['obstacles'], 'players_in_game': list(room_state['players'].values()),
            'total_foods_to_win': eat_food_config.TOTAL_FOODS_TO_WIN,
            'canvas_width': eat_food_config.CANVAS_WIDTH, 'canvas_height': eat_food_config.CANVAS_HEIGHT
        }
        await self.channel_layer.group_send(self.room_group_name, start_info_payload)

        # 방별 게임 루프 및 장애물 재생성 루프 시작/재시작
        tasks = room_state['tasks']
        if tasks.get('game_loop_task') is None or tasks['game_loop_task'].done():
            tasks['game_loop_task'] = asyncio.create_task(self._game_loop_for_room(room_id))
            print(f"DEBUG (MultiPlayer StartGame): Game loop CREATED/RESTARTED for room {room_id}")
        
        if tasks.get('obstacle_update_task') is None or tasks['obstacle_update_task'].done():
            tasks['obstacle_update_task'] = asyncio.create_task(self._obstacle_update_loop_for_room(room_id))
            print(f"DEBUG (MultiPlayer StartGame): Obstacle update loop CREATED/RESTARTED for room {room_id}")
        
        # 게임 시작 직후 현재 상태 브로드캐스트 (모든 요소 포함)
        await self._broadcast_current_game_state(room_id)


    async def _game_loop_for_room(self, room_id):
        """특정 방의 주요 게임 로직(NPC AI, 충돌 등)을 주기적으로 실행합니다."""
        loop_interval = 0.05 # 50ms
        print(f"DEBUG (MultiPlayer GameLoop): Started for room {room_id}")
        while True:
            room_state = rooms.get(room_id)
            if not room_state or not room_state.get('game_started', False): break 
            
            current_time_ms = asyncio.get_event_loop().time() * 1000
            try:
                # NPC AI 업데이트 (logic.py 호출)
                eat_food_logic.update_all_npcs(room_state, current_time_ms)

                # 플레이어-NPC 충돌 처리 (logic.py 호출)
                eat_food_logic.handle_npc_player_collisions(room_state) # room_state['players']는 이미 딕셔너리 형태

                # 모든 업데이트 후 게임 상태 브로드캐스트
                await self._broadcast_current_game_state(room_id)
                
            except asyncio.CancelledError:
                print(f"DEBUG (MultiPlayer GameLoop): Cancelled for room {room_id}.")
                break
            except Exception as e:
                print(f"ERROR (MultiPlayer GameLoop): Exception in room {room_id}: {e}")
                import traceback; traceback.print_exc()
            await asyncio.sleep(loop_interval)
        print(f"DEBUG (MultiPlayer GameLoop): Ended for room {room_id}")
        if room_id in rooms and rooms[room_id]['tasks']['game_loop_task']: rooms[room_id]['tasks']['game_loop_task'] = None


    async def _obstacle_update_loop_for_room(self, room_id):
        """특정 방의 장애물 재생성 로직을 주기적으로 실행합니다."""
        print(f"DEBUG (MultiPlayer ObstacleLoop): Started for room {room_id}")
        while True:
            room_state = rooms.get(room_id)
            if not room_state or not room_state.get('game_started', False): break
            
            try:
                await asyncio.sleep(eat_food_config.OBSTACLE_REGEN_INTERVAL)
                if room_id in rooms and rooms[room_id]['game_started']: # 재확인
                    print(f"DEBUG (MultiPlayer ObstacleLoop): Regenerating obstacles for room {room_id}")
                    eat_food_logic.initialize_obstacles(rooms[room_id], eat_food_config.OBSTACLE_COUNT)
                    # 장애물 변경 후 상태 전송 (선택적, game_loop_for_room에서도 주기적으로 전송됨)
                    # await self._broadcast_current_game_state(room_id) 
            except asyncio.CancelledError:
                print(f"DEBUG (MultiPlayer ObstacleLoop): Cancelled for room {room_id}.")
                break
            except Exception as e:
                print(f"ERROR (MultiPlayer ObstacleLoop): Exception in room {room_id}: {e}")
        print(f"DEBUG (MultiPlayer ObstacleLoop): Ended for room {room_id}")
        if room_id in rooms and rooms[room_id]['tasks']['obstacle_update_task']: rooms[room_id]['tasks']['obstacle_update_task'] = None


    async def _handle_player_move(self, room_state, player_data_from_client):
        player_server_state = room_state['players'].get(self.channel_name)
        if player_server_state and player_data_from_client:
            new_x = player_data_from_client.get('x', player_server_state['x'])
            new_y = player_data_from_client.get('y', player_server_state['y'])
            player_radius = player_server_state.get('collision_r', eat_food_config.PLAYER_COLLISION_RADIUS)

            player_server_state['x'] = max(player_radius, min(new_x, eat_food_config.CANVAS_WIDTH - player_radius))
            player_server_state['y'] = max(player_radius, min(new_y, eat_food_config.CANVAS_HEIGHT - player_radius))
            
            # 이동 정보는 _game_loop_for_room에서 주기적으로 전송되므로 여기서는 즉시 전송 안 함.
            # 만약 매우 빠른 반영이 필요하면 여기서 특정 플레이어 이동만 브로드캐스트 할 수도 있음.
            # await self._broadcast_current_game_state(self.room_id) # 이렇게 하면 모든 이동마다 전체 상태 전송
        # else: await self.send_error_message("이동 처리 중 플레이어 정보를 찾을 수 없습니다.") # 개인에게만 오류


    async def _handle_eat_attempt(self, room_state, food_id_from_client):
        player_state = room_state['players'].get(self.channel_name)
        foods_list = room_state['foods']

        if player_state and foods_list is not None and food_id_from_client:
            eaten_food_index = -1
            for i, food_item in enumerate(foods_list):
                if food_item["id"] == food_id_from_client:
                    if eat_food_logic.check_circle_circle_collision(
                        player_state["x"], player_state["y"], player_state["collision_r"],
                        food_item["x"], food_item["y"], food_item["collision_r"]
                    ):
                        eaten_food_index = i
                        break
            
            if eaten_food_index != -1:
                eaten_food = foods_list.pop(eaten_food_index)
                player_state["score"] += eaten_food["score"]
                player_state["eatCount"] += 1
                print(f"DEBUG (MultiPlayer Eat): Player {player_state['user']} ate {eaten_food['name']} in room {self.room_id}. New score: {player_state['score']}")

                new_food = eat_food_logic.generate_food_item(room_state) 
                if new_food: foods_list.append(new_food)

                # 승리 조건 확인 (logic.py 사용)
                if eat_food_logic.check_player_win_condition(player_state):
                    room_state['game_winner'] = player_state["user"]
                    room_state['game_started'] = False 
                    for task_name, task_obj in list(room_state['tasks'].items()):
                        if task_obj and not task_obj.done(): task_obj.cancel()
                    
                    await self.channel_layer.group_send(
                        self.room_group_name, {'type': 'broadcast_game_over', 'winner': room_state['game_winner']}
                    )
                else:
                    await self._broadcast_current_game_state(self.room_id) # 즉시 상태 업데이트
        # else: await self.send_error_message("음식 섭취 시도 중 오류가 발생했습니다.") # 개인에게만 오류


    async def _broadcast_current_game_state(self, room_id):
        room_state = rooms.get(room_id)
        if not room_state: return
        
        payload = {
            'type': 'broadcast_state_update',
            'players': list(room_state['players'].values()), 
            'foods': room_state['foods'],
            'npcs': room_state.get('npcs', []),
            'obstacles': room_state.get('obstacles', [])
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    # --- 브로드캐스트 메시지 핸들러 메소드들 ---
    async def broadcast_system_message(self, event):
        await self.send(text_data=json.dumps({"action": "system_message", "message": event["message"]}))

    async def broadcast_chat_message(self, event):
        await self.send(text_data=json.dumps({"action": "chat_message", "user": event["user"], "message": event["message"]}))

    async def broadcast_game_start_info(self, event):
        payload = {"action": "game_start_info", "foods": event['initial_foods'], "npcs": event.get('initial_npcs', []),
                   "obstacles": event.get('initial_obstacles', []), "players": event.get('players_in_game', []),
                   "total_foods_to_win": event['total_foods_to_win'], "canvas_width": event['canvas_width'], "canvas_height": event['canvas_height']}
        await self.send(text_data=json.dumps(payload))

    async def broadcast_state_update(self, event):
        payload = {"action": "state_update", "players": event.get('players', []), "foods": event.get('foods', []),
                   "npcs": event.get('npcs', []), "obstacles": event.get('obstacles', [])}
        await self.send(text_data=json.dumps(payload))

    async def broadcast_game_over(self, event):
        await self.send(text_data=json.dumps({"action": "game_over", "winner": event["winner"]}))

    async def send_error_message(self, message):
        await self.send(text_data=json.dumps({"action": "error", "message": message}))