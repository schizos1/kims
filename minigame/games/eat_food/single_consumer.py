# minigame/games/eat_food/single_consumer.py
# 'eat_food' 미니게임의 싱글플레이어 모드를 위한 WebSocket 컨슈머입니다.

import asyncio
import json
import random # 사용자 ID 생성 등에 임시 사용
# import time # asyncio.get_event_loop().time() 대신 time.time() 사용 시 필요

from channels.generic.websocket import AsyncWebsocketConsumer
from . import config as eat_food_config 
from . import logic as eat_food_logic   

class EatFoodSinglePlayerConsumer(AsyncWebsocketConsumer):
    """
    EatFood 미니게임의 싱글플레이어 버전 컨슈머.
    각 플레이어는 자신만의 게임 환경(음식, NPC, 장애물)을 가집니다.
    """

    async def connect(self):
        self.user = None
        self.game_state = {} 
        self.game_loop_task = None
        self.obstacle_regen_task = None 
        self.is_game_running = False

        await self.accept()
        print(f"DEBUG (SinglePlayerConsumer Connect): WebSocket connection accepted from {self.channel_name}")
        await self.send(text_data=json.dumps({
            "action": "connection_established",
            "message": "싱글플레이어 게임 서버에 연결되었습니다. 'join' 메시지로 게임을 시작하세요."
        }))

    async def disconnect(self, close_code):
        print(f"DEBUG (SinglePlayerConsumer Disconnect): WebSocket connection closed from {self.channel_name}. Code: {close_code}")
        self.is_game_running = False
        if self.game_loop_task and not self.game_loop_task.done():
            self.game_loop_task.cancel()
            print(f"DEBUG (SinglePlayerConsumer Disconnect): Game loop task cancelled for {self.channel_name}.")
        if self.obstacle_regen_task and not self.obstacle_regen_task.done():
            self.obstacle_regen_task.cancel()
            print(f"DEBUG (SinglePlayerConsumer Disconnect): Obstacle regen task cancelled for {self.channel_name}.")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")
            print(f"DEBUG (SinglePlayerConsumer Receive): Action '{action}' from {self.channel_name}, Data: {data}")


            if action == "join":
                # 사용자 정보 설정 (실제 서비스에서는 인증 정보 활용)
                user_name = data.get("user", f"Player_{random.randint(1000, 9999)}")
                char_img_path = data.get("charImgPath", "dino1.png") 
                await self._initialize_game(user_name, char_img_path)

            elif self.is_game_running:
                if action == "move":
                    player_data_from_client = data.get("player")
                    player_state = self.game_state.get("player")
                    if player_data_from_client and player_state:
                        requested_x = player_data_from_client.get('x')
                        requested_y = player_data_from_client.get('y')
                        
                        print(f"DEBUG (SinglePlayerConsumer Move): Player {player_state.get('user')} requested move to ({requested_x},{requested_y})")
                        
                        final_x, final_y, collided_with_obstacle = eat_food_logic.attempt_player_move(
                            player_state, 
                            requested_x, 
                            requested_y, 
                            self.game_state # game_state 전체 전달 (내부의 obstacles 사용)
                        )
                        player_state['x'] = final_x
                        player_state['y'] = final_y
                        
                        if collided_with_obstacle:
                            print(f"DEBUG (SinglePlayerConsumer Move): Player collision with obstacle. New pos: ({final_x},{final_y})")
                        
                        await self._send_current_game_state()

                elif action == "eatAttempt":
                    food_id_from_client = data.get("foodId")
                    player_state = self.game_state.get("player")
                    foods_list = self.game_state.get("foods")

                    if food_id_from_client and player_state and foods_list is not None:
                        print(f"DEBUG (SinglePlayerConsumer EatAttempt): FoodId: {food_id_from_client} from {player_state.get('user')}")
                        
                        food_to_eat = None
                        for food_item in foods_list: # 직접 순회하며 ID로 찾기
                            if food_item["id"] == food_id_from_client:
                                food_to_eat = food_item
                                break
                        
                        if food_to_eat:
                            if eat_food_logic.check_circle_circle_collision(
                                player_state["x"], player_state["y"], player_state.get("collision_r", eat_food_config.PLAYER_COLLISION_RADIUS),
                                food_to_eat["x"], food_to_eat["y"], food_to_eat["collision_r"]
                            ):
                                print(f"DEBUG (SinglePlayerConsumer EatAttempt): Player {player_state.get('user')} confirmed eating food {food_to_eat['name']}")
                                
                                player_state["score"] += food_to_eat["score"]
                                player_state["eatCount"] += 1
                                
                                eat_food_logic.remove_food_by_id(foods_list, food_id_from_client)
                                new_food = eat_food_logic.generate_food_item(self.game_state)
                                if new_food: foods_list.append(new_food)
                                
                                print(f"DEBUG (SinglePlayerConsumer EatAttempt): Player score: {player_state['score']}, eatCount: {player_state['eatCount']}")

                                if eat_food_logic.check_player_win_condition(player_state):
                                    print(f"DEBUG (SinglePlayerConsumer EatAttempt): Player {player_state.get('user')} WON!")
                                    await self._send_game_over(player_state.get("user")) # is_game_running 등은 _send_game_over에서 처리
                                else:
                                    await self._send_current_game_state()
                            else:
                                print(f"DEBUG (SinglePlayerConsumer EatAttempt): Food {food_id_from_client} FAILED - not close enough.")
                        else:
                            print(f"DEBUG (SinglePlayerConsumer EatAttempt): Food ID {food_id_from_client} FAILED - food not found.")
            else:
                await self.send_error_message("게임이 아직 시작되지 않았거나, 알 수 없는 액션입니다.")

        except json.JSONDecodeError:
            print(f"ERROR (SinglePlayerConsumer Receive): Invalid JSON received from {self.channel_name}")
            await self.send_error_message("잘못된 JSON 형식입니다.")
        except Exception as e:
            print(f"ERROR (SinglePlayerConsumer Receive): Exception for {self.channel_name} - {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error_message(f"서버 오류가 발생했습니다: {str(e)}")


    async def _initialize_game(self, user_name, char_img_path):
        if self.is_game_running:
            await self.send_error_message("게임이 이미 진행 중입니다.")
            return

        print(f"DEBUG (SinglePlayerConsumer Init): Initializing game for user {user_name} ({self.channel_name})")
        self.user = user_name # Consumer 인스턴스에 사용자 이름 저장
        
        initial_player_x = eat_food_config.CANVAS_WIDTH / 2
        initial_player_y = eat_food_config.CANVAS_HEIGHT / 2
        self.game_state["player"] = { 
            "id": self.channel_name, 
            "user": self.user, "x": initial_player_x, "y": initial_player_y,
            "score": 0, "eatCount": 0, "charImgPath": char_img_path,
            "collision_r": eat_food_config.PLAYER_COLLISION_RADIUS 
        }
        
        self.game_state["foods"] = [] 
        self.game_state["npcs"] = [] 
        self.game_state["obstacles"] = []

        eat_food_logic.initialize_foods(self.game_state, eat_food_config.INITIAL_FOOD_COUNT)
        eat_food_logic.initialize_npcs(self.game_state, eat_food_config.INITIAL_NPC_COUNT)
        eat_food_logic.initialize_obstacles(self.game_state, eat_food_config.OBSTACLE_COUNT)

        self.is_game_running = True

        print(f"DEBUG (SinglePlayerConsumer Init): Sending game_start_info to {self.channel_name}")
        await self.send(text_data=json.dumps({
            "action": "game_start_info",
            "player": self.game_state["player"],
            "foods": self.game_state["foods"], "npcs": self.game_state["npcs"], "obstacles": self.game_state["obstacles"],
            "total_foods_to_win": eat_food_config.TOTAL_FOODS_TO_WIN,
            "canvas_width": eat_food_config.CANVAS_WIDTH, "canvas_height": eat_food_config.CANVAS_HEIGHT
        }))
        print(f"DEBUG (SinglePlayerConsumer Init): Game started for {self.user}. Foods: {len(self.game_state['foods'])}, NPCs: {len(self.game_state['npcs'])}, Obstacles: {len(self.game_state['obstacles'])}")

        if self.game_loop_task and not self.game_loop_task.done(): self.game_loop_task.cancel()
        self.game_loop_task = asyncio.create_task(self._game_loop())
        print(f"DEBUG (SinglePlayerConsumer Init): Game loop task CREATED for {self.channel_name}")

        if self.obstacle_regen_task and not self.obstacle_regen_task.done(): self.obstacle_regen_task.cancel()
        self.obstacle_regen_task = asyncio.create_task(self._obstacle_regeneration_loop())
        print(f"DEBUG (SinglePlayerConsumer Init): Obstacle regeneration task CREATED for {self.channel_name}")


    async def _game_loop(self):
        loop_interval = 0.05  
        print(f"DEBUG (SinglePlayerConsumer GameLoop): Started for {self.channel_name}")

        while self.is_game_running:
            try:
                current_time_ms = asyncio.get_event_loop().time() * 1000 

                eat_food_logic.update_all_npcs(self.game_state, current_time_ms)

                # handle_npc_player_collisions는 game_state['players']를 딕셔너리로 기대하므로, 
                # 싱글플레이어에서는 player 객체를 포함하는 딕셔너리를 만들어 전달합니다.
                current_game_state_with_player_dict = {
                    "foods": self.game_state.get("foods", []),
                    "npcs": self.game_state.get("npcs", []),
                    "obstacles": self.game_state.get("obstacles", []),
                    "player": self.game_state.get("player"), # logic.py에서 이 키를 직접 사용하도록 수정함
                    # 또는 'players': {self.channel_name: self.game_state.get("player")} 로 전달하고 logic.py를 그에 맞게 수정
                }
                eat_food_logic.handle_npc_player_collisions(current_game_state_with_player_dict, current_time_ms)
                # logic.py의 handle_npc_player_collisions가 player_state를 직접 수정하므로,
                # 여기서 game_state['player']를 다시 할당할 필요는 현재 로직상 없습니다. (만약 반환값을 사용한다면 필요)

                await self._send_current_game_state()
                await asyncio.sleep(loop_interval)

            except asyncio.CancelledError:
                print(f"DEBUG (SinglePlayerConsumer GameLoop): Loop cancelled for {self.channel_name}.")
                break
            except Exception as e:
                print(f"ERROR (SinglePlayerConsumer GameLoop): {type(e).__name__} - {str(e)}") 
                import traceback; traceback.print_exc()
                # 오류 발생 시 게임 루프 중단 또는 특정 시간 후 재시도 등을 고려할 수 있음
                # self.is_game_running = False # 예: 오류 시 게임 중단
                await asyncio.sleep(1) # 디버깅 위해 잠시 대기
        
        print(f"DEBUG (SinglePlayerConsumer GameLoop): Ended for {self.channel_name}")


    async def _obstacle_regeneration_loop(self):
        print(f"DEBUG (SinglePlayerConsumer ObstacleLoop): Started for {self.channel_name}")
        while self.is_game_running:
            try:
                await asyncio.sleep(eat_food_config.OBSTACLE_REGEN_INTERVAL)
                if self.is_game_running: 
                    print(f"DEBUG (SinglePlayerConsumer ObstacleLoop): Regenerating obstacles for {self.channel_name}")
                    eat_food_logic.initialize_obstacles(self.game_state, eat_food_config.OBSTACLE_COUNT)
                    # 장애물 변경 후 상태 전송은 메인 게임 루프의 _send_current_game_state()에 의해 처리됨
            except asyncio.CancelledError:
                print(f"DEBUG (SinglePlayerConsumer ObstacleLoop): Cancelled for {self.channel_name}.")
                break
            except Exception as e:
                print(f"ERROR (SinglePlayerConsumer ObstacleLoop): {type(e).__name__} - {str(e)}")
        print(f"DEBUG (SinglePlayerConsumer ObstacleLoop): Ended for {self.channel_name}")

    async def _send_current_game_state(self):
        if not self.is_game_running: return
        payload = {
            "action": "state_update",
            "player": self.game_state.get("player"),
            "foods": self.game_state.get("foods"),
            "npcs": self.game_state.get("npcs"),
            "obstacles": self.game_state.get("obstacles")
        }
        try:
            # print(f"DEBUG (SinglePlayerConsumer SendState): Sending state to {self.channel_name}") # 너무 빈번할 수 있음
            await self.send(text_data=json.dumps(payload))
        except Exception as e:
            print(f"ERROR (SinglePlayerConsumer SendState): Failed to send state to {self.channel_name}: {e}")

    async def _send_game_over(self, winner_name):
        print(f"DEBUG (SinglePlayerConsumer GameOver): Game over! Winner: {winner_name}")
        self.is_game_running = False 
        if self.game_loop_task and not self.game_loop_task.done(): self.game_loop_task.cancel()
        if self.obstacle_regen_task and not self.obstacle_regen_task.done(): self.obstacle_regen_task.cancel()
        await self.send(text_data=json.dumps({"action": "game_over", "winner": winner_name}))

    async def send_error_message(self, message):
        await self.send(text_data=json.dumps({"action": "error", "message": message}))