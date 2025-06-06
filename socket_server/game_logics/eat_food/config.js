// socket_server/game_logics/eat_food/config.js
// 'eat_food' 미니게임의 서버 측 설정값 정의

// --- 캔버스 및 게임 환경 설정 ---
export const CANVAS_WIDTH = 1280;   // 캔버스 너비
export const CANVAS_HEIGHT = 720;  // 캔버스 높이
export const EDGE_MARGIN = 30;     // 객체가 캔버스 가장자리로부터 유지해야 하는 최소 여백

// --- 음식(Food) 관련 설정 ---
export const FOOD_RADIUS_NORMAL = 28;        // 일반 음식의 시각적 반지름 (클라이언트 참조용)
export const FOOD_RADIUS_SPECIAL = 38;       // 특별 음식의 시각적 반지름 (클라이언트 참조용)
export const FOOD_COLLISION_RADIUS_NORMAL = 12; // 일반 음식의 충돌 판정용 반지름 (서버 로직용)
export const FOOD_COLLISION_RADIUS_SPECIAL = 15; // 특별 음식의 충돌 판정용 반지름 (서버 로직용)

export const INITIAL_FOOD_COUNT = 5;        // 게임 시작 시 생성되는 초기 음식 개수
export const TOTAL_FOODS_TO_WIN = 30;        // 게임 승리를 위해 먹어야 하는 총 음식 개수

// 음식 종류별 상세 설정 (서버 로직에서 사용)
export const SERVER_FOOD_TYPES = [
    { name: "apple", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "chips", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "icecream", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "kola", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "noodle", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "pizza", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "salad", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "serial", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "steak", score: 10, special: false, radius: FOOD_RADIUS_NORMAL, collision_r: FOOD_COLLISION_RADIUS_NORMAL },
    { name: "koala", score: 100, special: true, radius: FOOD_RADIUS_SPECIAL, collision_r: FOOD_COLLISION_RADIUS_SPECIAL },
    { name: "monkey", score: 100, special: true, radius: FOOD_RADIUS_SPECIAL, collision_r: FOOD_COLLISION_RADIUS_SPECIAL }
];

// --- 플레이어(Player) 관련 설정 ---
export const PLAYER_COLLISION_RADIUS = 25; // 플레이어의 충돌 판정용 반지름

// --- NPC 관련 설정 ---
export const NPC_COLLISION_RADIUS = 25;    // NPC의 충돌 판정용 반지름
export const NPC_SPEED = 1.8;              // NPC의 기본 이동 속도
export const INITIAL_NPC_COUNT = 4;        // 게임 시작 시 생성되는 초기 NPC 수
export const NPC_CHAR_IMG_NAME = "monster.png"; // NPC 기본 캐릭터 이미지 파일 이름 (클라이언트 참조용)
export const NPC_SPAWN_INTERVAL = 15000;        // NPC 생성 간격 (ms)
export const OBSTACLE_MOVE_INTERVAL = 10000;     // 장애물 이동 간격 (ms)
export const OBSTACLE_COUNT_MIN = 4;             // 장애물 최소 개수
export const OBSTACLE_COUNT_MAX = 6;             // 장애물 최대 개수

// --- 장애물(Obstacle) 관련 설정 ---
export const OBSTACLE_COUNT = 8;               // 게임 내 생성되는 장애물 개수
export const OBSTACLE_REGEN_INTERVAL = 5000;   // 장애물 재생성 주기 (밀리초 단위, 예: 5초)
export const OBSTACLE_ELEMENT_SEPARATION = 30; // 장애물 간 또는 다른 요소와의 최소 이격 거리 (장애물 생성 시)
export const OBSTACLE_PLAYER_CLEARANCE = 50;   // 장애물 생성 시 플레이어와의 최소 이격 거리
export const OBSTACLE_NPC_CLEARANCE = 40;      // 장애물 생성 시 NPC와의 최소 이격 거리

export const OBSTACLE_CIRCLE_COLOR = "#d16060";  // 원형 장애물 기본 색상
export const OBSTACLE_RECT_COLOR = "#4A5568";    // 사각형 장애물 기본 색상
export const OBSTACLE_MIN_RADIUS = 50;           // 원형 장애물 최소 반지름
export const OBSTACLE_MAX_RADIUS = 100;          // 원형 장애물 최대 반지름
export const OBSTACLE_MIN_SIZE = 80;             // 사각형 장애물 최소 너비/높이
export const OBSTACLE_MAX_SIZE = 200;            // 사각형 장애물 최대 너비/높이

// --- 일반 게임 로직 설정 ---
export const GENERAL_ELEMENT_SEPARATION = 20; // 아이템(음식 등) 생성 시 다른 요소와 유지해야 하는 최소 간격
export const POSITION_GENERATION_MAX_ATTEMPTS = 30; // 새 아이템 위치 선정 시 최대 시도 횟수

// --- 싱글플레이어 게임 루프 설정 ---
export const SINGLE_GAME_LOOP_INTERVAL = 50; // 싱글플레이어 게임 루프 간격 (밀리초, 예: 20 FPS 면 50ms)
