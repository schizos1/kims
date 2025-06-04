# minigame/games/eat_food/config.py
# 이 파일은 'eat_food' 미니게임의 모든 설정값을 정의합니다.
# 게임의 기본적인 환경, 객체의 크기, 점수, NPC 및 장애물 관련 설정을 포함합니다.

# --- 캔버스 및 게임 환경 설정 ---
CANVAS_WIDTH = 1280   # 캔버스 너비 (기존 1280)
CANVAS_HEIGHT = 720  # 캔버스 높이 (기존 720)
EDGE_MARGIN = 30     # 객체가 캔버스 가장자리로부터 유지해야 하는 최소 여백

# --- 음식(Food) 관련 설정 ---
FOOD_RADIUS_NORMAL = 28        # 일반 음식의 시각적 반지름
FOOD_RADIUS_SPECIAL = 38       # 특별 음식의 시각적 반지름
FOOD_COLLISION_RADIUS_NORMAL = 12 # 일반 음식의 충돌 판정용 반지름
FOOD_COLLISION_RADIUS_SPECIAL = 15 # 특별 음식의 충돌 판정용 반지름

INITIAL_FOOD_COUNT = 12        # 게임 시작 시 생성되는 초기 음식 개수
TOTAL_FOODS_TO_WIN = 30        # 게임 승리를 위해 먹어야 하는 총 음식 개수

# 음식 종류별 상세 설정:
#   name: 음식 이름 (클라이언트 이미지 파일 이름과 일치 권장)
#   score: 획득 점수
#   special: 특별 음식 여부 (True/False)
#   radius: 시각적 반지름 (위에 정의된 값 사용)
#   collision_r: 충돌 판정용 반지름 (위에 정의된 값 사용)
SERVER_FOOD_TYPES = [
    {"name": "apple", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "chips", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "icecream", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "kola", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "noodle", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "pizza", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "salad", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "serial", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "steak", "score": 10, "special": False, "radius": FOOD_RADIUS_NORMAL, "collision_r": FOOD_COLLISION_RADIUS_NORMAL},
    {"name": "koala", "score": 100, "special": True, "radius": FOOD_RADIUS_SPECIAL, "collision_r": FOOD_COLLISION_RADIUS_SPECIAL}, # 특별 아이템
    {"name": "monkey", "score": 100, "special": True, "radius": FOOD_RADIUS_SPECIAL, "collision_r": FOOD_COLLISION_RADIUS_SPECIAL} # 특별 아이템
]

# --- 플레이어(Player) 관련 설정 ---
PLAYER_COLLISION_RADIUS = 25 # 플레이어의 충돌 판정용 반지름

# --- NPC 관련 설정 ---
NPC_COLLISION_RADIUS = 25    # NPC의 충돌 판정용 반지름
NPC_SPEED = 1.8              # NPC의 기본 이동 속도
INITIAL_NPC_COUNT = 4        # 게임 시작 시 생성되는 초기 NPC 수
NPC_CHAR_IMG_NAME = "monster.png" # NPC 기본 캐릭터 이미지 파일 이름

# --- 장애물(Obstacle) 관련 설정 ---
OBSTACLE_COUNT = 8               # 게임 내 생성되는 장애물 개수
OBSTACLE_REGEN_INTERVAL = 5      # 장애물 재생성 주기 (초)
OBSTACLE_ELEMENT_SEPARATION = 30 # 장애물 간 또는 다른 요소와의 최소 이격 거리 (장애물 생성 시)
OBSTACLE_PLAYER_CLEARANCE = 50   # 장애물 생성 시 플레이어와의 최소 이격 거리
OBSTACLE_NPC_CLEARANCE = 40      # 장애물 생성 시 NPC와의 최소 이격 거리

# 👇 [추가!] 장애물 색상 및 크기 관련 설정
OBSTACLE_CIRCLE_COLOR = "#d16060"  # 원형 장애물 기본 색상 (예시)
OBSTACLE_RECT_COLOR = "#4A5568"    # 사각형 장애물 기본 색상 (예시)
OBSTACLE_MIN_RADIUS = 50           # 원형 장애물 최소 반지름
OBSTACLE_MAX_RADIUS = 100          # 원형 장애물 최대 반지름
OBSTACLE_MIN_SIZE = 80             # 사각형 장애물 최소 너비/높이
OBSTACLE_MAX_SIZE = 200            # 사각형 장애물 최대 너비/높이

# --- 일반 게임 로직 설정 ---
GENERAL_ELEMENT_SEPARATION = 20 # 아이템(음식 등) 생성 시 다른 요소와 유지해야 하는 최소 간격
POSITION_GENERATION_MAX_ATTEMPTS = 30 # 새 아이템 위치 선정 시 최대 시도 횟수