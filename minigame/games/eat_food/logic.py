# minigame/games/eat_food/logic.py
# 이 파일은 'eat_food' 미니게임의 모든 핵심 로직을 담당합니다.

import random
import uuid
import math
# import asyncio # 컨슈머에서 시간을 받아오므로 직접 사용하지 않음
from . import config

# --- 충돌 감지 유틸리티 함수 ---

def check_circle_circle_collision(c1_x, c1_y, c1_r, c2_x, c2_y, c2_r):
    """두 원 간의 충돌을 확인합니다."""
    dist_sq = (c1_x - c2_x)**2 + (c1_y - c2_y)**2
    radii_sum_sq = (c1_r + c2_r)**2
    return dist_sq < radii_sum_sq

def check_rect_rect_collision(r1_x, r1_y, r1_w, r1_h, r2_x, r2_y, r2_w, r2_h):
    """두 사각형 간의 충돌을 확인합니다 (AABB 방식)."""
    return (r1_x < r2_x + r2_w and r1_x + r1_w > r2_x and
            r1_y < r2_y + r2_h and r1_y + r1_h > r2_y)

def check_circle_rect_collision(circle_x, circle_y, circle_r, rect_x, rect_y, rect_w, rect_h):
    """원과 사각형 간의 충돌을 확인합니다."""
    closest_x = max(rect_x, min(circle_x, rect_x + rect_w))
    closest_y = max(rect_y, min(circle_y, rect_y + rect_h))
    distance_sq = (circle_x - closest_x)**2 + (circle_y - closest_y)**2
    return distance_sq < (circle_r * circle_r)

# --- 위치 안전성 및 유효성 검사 헬퍼 함수 ---

def is_position_within_canvas_bounds(x, y, element_radius):
    """요소가 캔버스 경계 내에 있는지 확인합니다 (여백 포함)."""
    return (element_radius + config.EDGE_MARGIN <= x <= config.CANVAS_WIDTH - element_radius - config.EDGE_MARGIN and
            element_radius + config.EDGE_MARGIN <= y <= config.CANVAS_HEIGHT - element_radius - config.EDGE_MARGIN)

def is_safe_to_spawn_element(x, y, radius, game_state, 
                             check_vs_obstacles=True, 
                             check_vs_players=True, 
                             check_vs_npcs=True, 
                             check_vs_foods=False, 
                             own_id_to_ignore=None,
                             items_in_current_batch=None):
    if not is_position_within_canvas_bounds(x, y, radius):
        # print(f"LOGIC_DEBUG: Spawn fail - Out of bounds: ({x},{y}) r:{radius}")
        return False

    if items_in_current_batch:
        for item_in_batch in items_in_current_batch:
            sep = config.OBSTACLE_ELEMENT_SEPARATION # 배치 중인 장애물 간 간격
            if item_in_batch['type'] == 'circle':
                if check_circle_circle_collision(x, y, radius, item_in_batch['x'], item_in_batch['y'], item_in_batch['r'] + sep):
                    return False
            elif item_in_batch['type'] == 'rect':
                if check_circle_rect_collision(x, y, radius, 
                                               item_in_batch['x'] - sep, item_in_batch['y'] - sep, 
                                               item_in_batch['w'] + 2 * sep, item_in_batch['h'] + 2 * sep):
                    return False
    
    if check_vs_obstacles:
        for obs in game_state.get('obstacles', []):
            sep = config.OBSTACLE_ELEMENT_SEPARATION # 기존 장애물과의 간격
            if obs['type'] == 'circle':
                if check_circle_circle_collision(x, y, radius, obs['x'], obs['y'], obs['r'] + sep):
                    return False
            elif obs['type'] == 'rect':
                if check_circle_rect_collision(x, y, radius, 
                                               obs['x'] - sep, obs['y'] - sep, 
                                               obs['w'] + 2 * sep, obs['h'] + 2 * sep):
                    return False
    
    if check_vs_players:
        players_to_check = []
        if 'player' in game_state and game_state['player']: players_to_check.append(game_state['player'])
        elif 'players' in game_state and game_state['players']: players_to_check.extend(game_state['players'].values())

        for p_data in players_to_check:
            if p_data.get('id') == own_id_to_ignore: continue
            # 스폰 시 플레이어와의 최소 이격거리 사용
            player_clearance = p_data.get('collision_r', config.PLAYER_COLLISION_RADIUS) + config.OBSTACLE_PLAYER_CLEARANCE 
            if check_circle_circle_collision(x, y, radius, p_data['x'], p_data['y'], player_clearance):
                return False

    if check_vs_npcs:
        for npc_data in game_state.get('npcs', []):
            if npc_data.get('id') == own_id_to_ignore: continue
            npc_clearance = config.NPC_COLLISION_RADIUS + config.OBSTACLE_NPC_CLEARANCE
            if check_circle_circle_collision(x, y, radius, npc_data['x'], npc_data['y'], npc_clearance):
                return False

    if check_vs_foods:
        for food_data in game_state.get('foods', []):
            if check_circle_circle_collision(x, y, radius, food_data['x'], food_data['y'], food_data['collision_r'] + config.GENERAL_ELEMENT_SEPARATION):
                return False
    return True

# --- 음식(Food) 관련 로직 ---
def generate_food_item(game_state):
    food_type_info = random.choice(config.SERVER_FOOD_TYPES)
    food_id = str(uuid.uuid4())
    visual_radius = food_type_info["radius"]
    collision_radius = food_type_info["collision_r"]

    for _ in range(config.POSITION_GENERATION_MAX_ATTEMPTS):
        x = random.randint(visual_radius + config.EDGE_MARGIN, config.CANVAS_WIDTH - visual_radius - config.EDGE_MARGIN)
        y = random.randint(visual_radius + config.EDGE_MARGIN, config.CANVAS_HEIGHT - visual_radius - config.EDGE_MARGIN)
        if is_safe_to_spawn_element(x, y, collision_radius, game_state, check_vs_obstacles=True, check_vs_foods=True, check_vs_players=False, check_vs_npcs=False):
            return {"id": food_id, "name": food_type_info["name"], "x": x, "y": y, "r": visual_radius, 
                    "collision_r": collision_radius, "special": food_type_info["special"], "score": food_type_info["score"]}
    return {"id": food_id, "name": food_type_info["name"], 
            "x": random.randint(visual_radius + config.EDGE_MARGIN, config.CANVAS_WIDTH - visual_radius - config.EDGE_MARGIN),
            "y": random.randint(visual_radius + config.EDGE_MARGIN, config.CANVAS_HEIGHT - visual_radius - config.EDGE_MARGIN),
            "r": visual_radius, "collision_r": collision_radius, "special": food_type_info["special"], "score": food_type_info["score"]}

def initialize_foods(game_state, count=None):
    if count is None: count = config.INITIAL_FOOD_COUNT
    if 'foods' not in game_state: game_state['foods'] = []
    foods_to_add = max(0, count - len(game_state['foods']))
    for _ in range(foods_to_add):
        new_food = generate_food_item(game_state)
        if new_food: game_state['foods'].append(new_food)
    # print(f"LOGIC_DEBUG: Initialized/Updated foods. Total: {len(game_state['foods'])}")

def remove_food_by_id(foods_list, food_id):
    for i, food_item in enumerate(foods_list):
        if food_item['id'] == food_id:
            return foods_list.pop(i)
    return None

# --- NPC 관련 로직 ---
def generate_npc_item(game_state):
    npc_id = str(uuid.uuid4())
    npc_radius = config.NPC_COLLISION_RADIUS
    for _ in range(config.POSITION_GENERATION_MAX_ATTEMPTS):
        x = random.randint(npc_radius + config.EDGE_MARGIN, config.CANVAS_WIDTH - npc_radius - config.EDGE_MARGIN)
        y = random.randint(npc_radius + config.EDGE_MARGIN, config.CANVAS_HEIGHT - npc_radius - config.EDGE_MARGIN)
        if is_safe_to_spawn_element(x, y, npc_radius, game_state, check_vs_obstacles=True, check_vs_players=True, check_vs_npcs=True, own_id_to_ignore=npc_id):
            return {"id": npc_id, "x": x, "y": y, "charImgName": config.NPC_CHAR_IMG_NAME, 
                    "speed": config.NPC_SPEED * (1 + random.uniform(-0.15, 0.15)), 
                    "targetFoodId": None, "isAngry": False, "angryEndTime": 0, 
                    "eatingTargetId": None, "eatStartTime": 0, 
                    "originalEatDuration": 1200 + random.randint(-200, 200), 
                    "stuckCounter": 0, "moveAttemptAngle": random.uniform(0, 2 * math.pi),
                    "collision_r": config.NPC_COLLISION_RADIUS}
    return {"id": npc_id, 
            "x": random.randint(npc_radius + config.EDGE_MARGIN, config.CANVAS_WIDTH - npc_radius - config.EDGE_MARGIN),
            "y": random.randint(npc_radius + config.EDGE_MARGIN, config.CANVAS_HEIGHT - npc_radius - config.EDGE_MARGIN),
            "charImgName": config.NPC_CHAR_IMG_NAME, "speed": config.NPC_SPEED,
            "targetFoodId": None, "isAngry": False, "angryEndTime": 0,
            "eatingTargetId": None, "eatStartTime": 0, "originalEatDuration": 1200,
            "stuckCounter": 0, "moveAttemptAngle": random.uniform(0, 2 * math.pi),
            "collision_r": config.NPC_COLLISION_RADIUS}

def initialize_npcs(game_state, count=None):
    if count is None: count = config.INITIAL_NPC_COUNT
    if 'npcs' not in game_state: game_state['npcs'] = []
    for _ in range(count):
        new_npc = generate_npc_item(game_state)
        if new_npc: game_state['npcs'].append(new_npc)
    # print(f"LOGIC_DEBUG: Initialized {len(game_state['npcs'])} NPCs.")

def is_safe_to_move_actor(current_x, current_y, next_x, next_y, actor_radius, game_state, own_id, 
                          check_vs_obstacles=True, check_vs_other_npcs=True):
    if not is_position_within_canvas_bounds(next_x, next_y, actor_radius):
        # print(f"LOGIC_DEBUG (Move): Actor {own_id} ({next_x},{next_y}) out of bounds.")
        return False
    if check_vs_obstacles:
        for obs in game_state.get('obstacles', []):
            collided = False
            if obs['type'] == 'circle':
                if check_circle_circle_collision(next_x, next_y, actor_radius, obs['x'], obs['y'], obs['r']):
                    collided = True
            elif obs['type'] == 'rect':
                if check_circle_rect_collision(next_x, next_y, actor_radius, obs['x'], obs['y'], obs['w'], obs['h']):
                    collided = True
            if collided:
                print(f"---- LOGIC_DEBUG (Move): NPC {own_id} move BLOCKED by obstacle {obs.get('id')} ----")
                return False
    if check_vs_other_npcs:
        for other_npc in game_state.get('npcs', []):
            if other_npc.get('id') == own_id: continue
            if check_circle_circle_collision(next_x, next_y, actor_radius, other_npc['x'], other_npc['y'], config.NPC_COLLISION_RADIUS + 2):
                print(f"---- LOGIC_DEBUG (Move): NPC {own_id} move BLOCKED by other NPC {other_npc.get('id')} ----")
                return False
    return True

def update_one_npc(npc_state, game_state, current_time_ms):
    if npc_state.get('isAngry', False) and current_time_ms > npc_state.get('angryEndTime', 0):
        npc_state['isAngry'] = False
    if npc_state.get('eatingTargetId'):
        if current_time_ms - npc_state.get('eatStartTime', 0) > npc_state.get('originalEatDuration', 1200):
            eaten_food_id = npc_state['eatingTargetId']
            if remove_food_by_id(game_state.get('foods', []), eaten_food_id):
                new_food = generate_food_item(game_state)
                if new_food: game_state['foods'].append(new_food)
            npc_state['eatingTargetId'] = None; npc_state['targetFoodId'] = None
        else: return 
    current_target_food_object = None
    if npc_state.get('targetFoodId'):
        current_target_food_object = next((f for f in game_state.get('foods', []) if f['id'] == npc_state['targetFoodId']), None)
        if not current_target_food_object: npc_state['targetFoodId'] = None
    if not npc_state.get('targetFoodId') and game_state.get('foods'):
        closest_food = None; min_dist_sq = float('inf')
        targeted_by_others = {o_npc.get('targetFoodId') for o_npc in game_state.get('npcs', []) if o_npc.get('id') != npc_state['id'] and o_npc.get('targetFoodId')}
        for food in game_state.get('foods', []):
            if food['id'] in targeted_by_others and not food.get('special', False): continue
            dist_sq = (npc_state['x'] - food['x'])**2 + (npc_state['y'] - food['y'])**2
            if dist_sq < min_dist_sq: min_dist_sq = dist_sq; closest_food = food
        if closest_food: npc_state['targetFoodId'] = closest_food['id']; current_target_food_object = closest_food
    if current_target_food_object:
        target_x, target_y = current_target_food_object['x'], current_target_food_object['y']
        dx, dy = target_x - npc_state['x'], target_y - npc_state['y']
        dist_to_target = math.hypot(dx, dy)
        npc_radius = npc_state.get('collision_r', config.NPC_COLLISION_RADIUS)
        if dist_to_target < (npc_radius + current_target_food_object['collision_r'] + 2):
            npc_state['eatingTargetId'] = npc_state['targetFoodId']; npc_state['eatStartTime'] = current_time_ms
        elif dist_to_target > 0:
            move_x = (dx / dist_to_target) * npc_state['speed']; move_y = (dy / dist_to_target) * npc_state['speed']
            next_x, next_y = npc_state['x'] + move_x, npc_state['y'] + move_y
            if is_safe_to_move_actor(npc_state['x'], npc_state['y'], next_x, next_y, npc_radius, game_state, npc_state['id']):
                npc_state['x'], npc_state['y'] = next_x, next_y; npc_state['stuckCounter'] = 0
            else:
                npc_state['stuckCounter'] += 1
                if npc_state['stuckCounter'] > 3:
                    npc_state['targetFoodId'] = None; npc_state['moveAttemptAngle'] = random.uniform(0, 2 * math.pi); npc_state['stuckCounter'] = 0
                else: 
                    angle = math.atan2(move_y, move_x); npc_state['moveAttemptAngle'] = angle + random.choice([-math.pi/2, math.pi/2, math.pi*random.uniform(0.4,0.6)]) 
                    alt_move_x = math.cos(npc_state['moveAttemptAngle'])*npc_state['speed']*0.7; alt_move_y = math.sin(npc_state['moveAttemptAngle'])*npc_state['speed']*0.7
                    if is_safe_to_move_actor(npc_state['x'],npc_state['y'],npc_state['x']+alt_move_x,npc_state['y']+alt_move_y,npc_radius,game_state,npc_state['id']):
                        npc_state['x']+=alt_move_x; npc_state['y']+=alt_move_y
    else: 
        if random.random()<0.05 or npc_state['stuckCounter']>8 : npc_state['moveAttemptAngle']=random.uniform(0,2*math.pi); npc_state['stuckCounter']=0
        wander_dx = math.cos(npc_state['moveAttemptAngle'])*npc_state['speed']*0.5; wander_dy = math.sin(npc_state['moveAttemptAngle'])*npc_state['speed']*0.5
        npc_radius = npc_state.get('collision_r', config.NPC_COLLISION_RADIUS)
        if is_safe_to_move_actor(npc_state['x'],npc_state['y'],npc_state['x']+wander_dx,npc_state['y']+wander_dy,npc_radius,game_state,npc_state['id']):
            npc_state['x']+=wander_dx; npc_state['y']+=wander_dy
        else: npc_state['moveAttemptAngle']=random.uniform(0,2*math.pi); npc_state['stuckCounter']+=1
    npc_radius = npc_state.get('collision_r', config.NPC_COLLISION_RADIUS)
    npc_state['x'] = max(npc_radius, min(npc_state['x'], config.CANVAS_WIDTH - npc_radius))
    npc_state['y'] = max(npc_radius, min(npc_state['y'], config.CANVAS_HEIGHT - npc_radius))

def update_all_npcs(game_state, current_time_ms):
    if 'npcs' in game_state:
        for npc_state in game_state['npcs']:
            update_one_npc(npc_state, game_state, current_time_ms)

def handle_npc_player_collisions(game_state, current_time_ms): # current_time_ms 인자 추가
    npcs = game_state.get('npcs', [])
    players_to_check = []
    if 'player' in game_state and game_state['player']: players_to_check.append(game_state['player'])
    elif 'players' in game_state and game_state['players']: players_to_check.extend(game_state['players'].values())

    for npc_state in npcs:
        if npc_state.get('isAngry', False) and current_time_ms < npc_state.get('angryEndTime', 0):
            continue 
        for player_state in players_to_check:
            npc_radius = npc_state.get('collision_r', config.NPC_COLLISION_RADIUS)
            player_radius = player_state.get('collision_r', config.PLAYER_COLLISION_RADIUS)
            if check_circle_circle_collision(npc_state['x'], npc_state['y'], npc_radius, player_state['x'], player_state['y'], player_radius):
                print(f"!!!! LOGIC_DEBUG (Collision): NPC {npc_state['id']} and Player {player_state.get('user')} COLLIDED !!!!")
                dx = npc_state['x'] - player_state['x']; dy = npc_state['y'] - player_state['y']
                distance = math.hypot(dx, dy); distance = 0.1 if distance == 0 else distance
                overlap = (npc_radius + player_radius) - distance
                push_dx = dx / distance; push_dy = dy / distance
                npc_push = overlap * 0.6 + 1.5; player_push = overlap * 0.4 + 1.0
                
                npc_state['x'] = max(npc_radius, min(npc_state['x'] + push_dx * npc_push, config.CANVAS_WIDTH - npc_radius))
                npc_state['y'] = max(npc_radius, min(npc_state['y'] + push_dy * npc_push, config.CANVAS_HEIGHT - npc_radius))
                player_state['x'] = max(player_radius, min(player_state['x'] - push_dx * player_push, config.CANVAS_WIDTH - player_radius))
                player_state['y'] = max(player_radius, min(player_state['y'] - push_dy * player_push, config.CANVAS_HEIGHT - player_radius))
                
                npc_state['isAngry'] = True; npc_state['angryEndTime'] = current_time_ms + 2000 
                npc_state['targetFoodId'] = None; npc_state['eatingTargetId'] = None 
                break 

# --- 플레이어 이동 및 충돌 처리 ---
def attempt_player_move(player_state, requested_x, requested_y, game_state):
    player_radius = player_state.get('collision_r', config.PLAYER_COLLISION_RADIUS)
    obstacles_list = game_state.get('obstacles', [])
    
    # 1. 요청된 위치가 경계 밖이면 일단 경계 안으로 (EDGE_MARGIN 고려)
    next_x = max(player_radius + config.EDGE_MARGIN, min(requested_x, config.CANVAS_WIDTH - player_radius - config.EDGE_MARGIN))
    next_y = max(player_radius + config.EDGE_MARGIN, min(requested_y, config.CANVAS_HEIGHT - player_radius - config.EDGE_MARGIN))
    
    # print(f"LOGIC_DEBUG (PlayerMove): Requested ({requested_x},{requested_y}), Adjusted to bounds: ({next_x},{next_y})")

    # 2. 조정된 위치에 대해 장애물 충돌 검사
    for obs in obstacles_list:
        collided_with_this_obstacle = False
        if obs['type'] == 'circle':
            if check_circle_circle_collision(next_x, next_y, player_radius, obs['x'], obs['y'], obs['r']):
                collided_with_this_obstacle = True
        elif obs['type'] == 'rect':
            if check_circle_rect_collision(next_x, next_y, player_radius, obs['x'], obs['y'], obs['w'], obs['h']):
                collided_with_this_obstacle = True
        
        if collided_with_this_obstacle:
            print(f"LOGIC_DEBUG (PlayerMove): Player would collide with obstacle {obs.get('id')}. Staying at current pos: ({player_state['x']},{player_state['y']})")
            return player_state['x'], player_state['y'], True # 충돌 시, 이전 위치 반환

    # 충돌하지 않았으면 최종 위치 반환
    # print(f"LOGIC_DEBUG (PlayerMove): Player move to ({next_x},{next_y}) is safe from obstacles.")
    return next_x, next_y, False


# --- 장애물(Obstacle) 관련 로직 ---
def generate_obstacle_item(game_state, existing_obstacles_in_batch):
    obs_type = random.choice(["circle", "rect"])
    obs_id = str(uuid.uuid4())
    main_color = config.OBSTACLE_CIRCLE_COLOR if obs_type == "circle" else config.OBSTACLE_RECT_COLOR
    
    for _ in range(config.POSITION_GENERATION_MAX_ATTEMPTS):
        temp_obs_props = {}
        check_radius_for_spawn_safety = 0 # is_safe_to_spawn_element에 전달될 대략적인 반경
        center_x_for_spawn_safety, center_y_for_spawn_safety = 0, 0

        if obs_type == "circle":
            r = random.uniform(config.OBSTACLE_MIN_RADIUS, config.OBSTACLE_MAX_RADIUS)
            x = random.uniform(config.EDGE_MARGIN + r, config.CANVAS_WIDTH - config.EDGE_MARGIN - r)
            y = random.uniform(config.EDGE_MARGIN + r, config.CANVAS_HEIGHT - config.EDGE_MARGIN - r)
            temp_obs_props = {"type": "circle", "x": x, "y": y, "r": r}
            check_radius_for_spawn_safety = r
            center_x_for_spawn_safety, center_y_for_spawn_safety = x, y
        else: # rect
            w = random.uniform(config.OBSTACLE_MIN_SIZE, config.OBSTACLE_MAX_SIZE)
            h = random.uniform(config.OBSTACLE_MIN_SIZE, config.OBSTACLE_MAX_SIZE)
            x = random.uniform(config.EDGE_MARGIN, config.CANVAS_WIDTH - config.EDGE_MARGIN - w)
            y = random.uniform(config.EDGE_MARGIN, config.CANVAS_HEIGHT - config.EDGE_MARGIN - h)
            temp_obs_props = {"type": "rect", "x": x, "y": y, "w": w, "h": h}
            check_radius_for_spawn_safety = max(w, h) / 2 # 사각형을 감싸는 원으로 근사
            center_x_for_spawn_safety, center_y_for_spawn_safety = x + w/2, y + h/2
            
        if is_safe_to_spawn_element(center_x_for_spawn_safety, center_y_for_spawn_safety, 
                                  check_radius_for_spawn_safety, # 실제 장애물 모양에 따른 충돌은 is_safe_to_spawn_element 내부에서 처리됨
                                  game_state, 
                                  check_vs_obstacles=True, 
                                  check_vs_players=True, 
                                  check_vs_npcs=True,
                                  items_in_current_batch=existing_obstacles_in_batch, 
                                  own_id_to_ignore=obs_id): # own_id는 현재 생성 중인 장애물 ID
            return {**temp_obs_props, "id": obs_id, "mainColor": main_color}
            
    # print(f"LOGIC_DEBUG (ObstacleGen): Failed to place obstacle {obs_id} safely. Skipping.")
    return None 

def initialize_obstacles(game_state, count=None):
    if count is None: count = config.OBSTACLE_COUNT
    game_state['obstacles'] = [] 
    newly_generated_obstacles_in_this_call = [] 
    for _ in range(count):
        item = generate_obstacle_item(game_state, newly_generated_obstacles_in_this_call) 
        if item:
            newly_generated_obstacles_in_this_call.append(item) 
            game_state['obstacles'].append(item) 
    # print(f"LOGIC_DEBUG: Initialized/Regenerated {len(game_state['obstacles'])} obstacles.")

# --- 게임 규칙 및 승리 조건 ---
def check_player_win_condition(player_state):
    if player_state and player_state.get('eatCount', 0) >= config.TOTAL_FOODS_TO_WIN:
        return True
    return False