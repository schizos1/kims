// socket_server/game_logics/eat_food/entity_manager.js
// 'eat_food' 미니게임의 서버 측 게임 요소(음식, NPC, 장애물) 생성 및 관리

import * as config from './config.js';
import {
    checkCircleCircleCollision,
    checkCircleRectCollision,
    isPositionWithinCanvasBounds
} from './collision_utils.js';
import { randomUUID } from 'crypto'; // Node.js 내장 crypto 모듈 사용

/**
 * 주어진 위치에 새로운 요소를 안전하게 배치할 수 있는지 확인합니다.
 * @param {number} x 배치할 요소의 중심 x 좌표
 * @param {number} y 배치할 요소의 중심 y 좌표
 * @param {number} radius 배치할 요소의 충돌 반경
 * @param {object} gameState 현재 게임 상태 (다른 요소들의 위치 정보 포함)
 * @param {boolean} checkVsObstacles 장애물과의 충돌을 확인할지 여부
 * @param {boolean} checkVsPlayers 플레이어와의 충돌을 확인할지 여부
 * @param {boolean} checkVsNpcs NPC와의 충돌을 확인할지 여부
 * @param {boolean} checkVsFoods 음식과의 충돌을 확인할지 여부
 * @param {string|null} ownIdToIgnore 충돌 검사 시 무시할 자신의 ID (주로 NPC 생성 시)
 * @param {Array|null} itemsInCurrentBatch 현재 배치 중인 다른 아이템 목록 (주로 장애물 일괄 생성 시)
 * @returns {boolean} 안전하게 배치 가능하면 true, 아니면 false
 */
function isSafeToSpawnElement(
    x, y, radius, gameState,
    checkVsObstacles = true,
    checkVsPlayers = true,
    checkVsNpcs = true,
    checkVsFoods = false,
    ownIdToIgnore = null,
    itemsInCurrentBatch = null
) {
    if (!isPositionWithinCanvasBounds(x, y, radius, config)) {
        return false;
    }

    // 현재 일괄 생성 중인 다른 아이템들과의 충돌 검사 (주로 장애물용)
    if (itemsInCurrentBatch) {
        for (const itemInBatch of itemsInCurrentBatch) {
            // 장애물 생성 시에는 장애물 간 최소 이격 거리를 추가로 고려
            const separation = config.OBSTACLE_ELEMENT_SEPARATION;
            if (itemInBatch.type === 'circle') {
                if (checkCircleCircleCollision(x, y, radius, itemInBatch.x, itemInBatch.y, itemInBatch.r + separation)) {
                    return false;
                }
            } else if (itemInBatch.type === 'rect') {
                // 사각형 장애물은 충돌 영역을 약간 확장하여 검사
                if (checkCircleRectCollision(x, y, radius,
                    itemInBatch.x - separation, itemInBatch.y - separation,
                    itemInBatch.w + 2 * separation, itemInBatch.h + 2 * separation)) {
                    return false;
                }
            }
        }
    }

    // 기존 장애물과의 충돌 검사
    if (checkVsObstacles && gameState.obstacles) {
        for (const obs of gameState.obstacles) {
            const separation = config.OBSTACLE_ELEMENT_SEPARATION;
            if (obs.type === 'circle') {
                if (checkCircleCircleCollision(x, y, radius, obs.x, obs.y, obs.r + separation)) return false;
            } else if (obs.type === 'rect') {
                if (checkCircleRectCollision(x, y, radius,
                    obs.x - separation, obs.y - separation,
                    obs.w + 2 * separation, obs.h + 2 * separation)) return false;
            }
        }
    }

    // 플레이어와의 충돌 검사
    if (checkVsPlayers && gameState.players) {
        for (const playerId in gameState.players) {
            if (playerId === ownIdToIgnore) continue;
            const p_data = gameState.players[playerId];
            const playerClearance = p_data.collisionRadius + config.OBSTACLE_PLAYER_CLEARANCE;
            if (checkCircleCircleCollision(x, y, radius, p_data.x, p_data.y, playerClearance)) {
                return false;
            }
        }
    }
     // 싱글 플레이어 모드 (gameState.player)
    if (checkVsPlayers && gameState.player) {
        if (gameState.player.id === ownIdToIgnore) { /* no-op */ }
        else {
            const p_data = gameState.player;
            const playerClearance = p_data.collisionRadius + config.OBSTACLE_PLAYER_CLEARANCE;
            if (checkCircleCircleCollision(x, y, radius, p_data.x, p_data.y, playerClearance)) {
                return false;
            }
        }
    }


    // NPC와의 충돌 검사
    if (checkVsNpcs && gameState.npcs) {
        for (const npc_data of gameState.npcs) {
            if (npc_data.id === ownIdToIgnore) continue;
            const npcClearance = npc_data.collisionRadius + config.OBSTACLE_NPC_CLEARANCE;
            if (checkCircleCircleCollision(x, y, radius, npc_data.x, npc_data.y, npcClearance)) {
                return false;
            }
        }
    }

    // 음식과의 충돌 검사
    if (checkVsFoods && gameState.foods) {
        for (const food_data of gameState.foods) {
            if (checkCircleCircleCollision(x, y, radius, food_data.x, food_data.y, food_data.collision_r + config.GENERAL_ELEMENT_SEPARATION)) {
                return false;
            }
        }
    }
    return true;
}

// --- 음식(Food) 관련 로직 ---
/**
 * 새로운 음식 아이템 하나를 생성합니다.
 * @param {object} gameState 현재 게임 상태
 * @returns {object|null} 생성된 음식 객체 또는 생성 실패 시 null
 */
export function generateFoodItem(gameState) {
    const foodTypeInfo = config.SERVER_FOOD_TYPES[Math.floor(Math.random() * config.SERVER_FOOD_TYPES.length)];
    const foodId = randomUUID(); // Node.js crypto 모듈 사용
    const visualRadius = foodTypeInfo.radius; // 클라이언트 시각적 표현용
    const collisionRadius = foodTypeInfo.collision_r; // 서버 충돌 판정용

    for (let i = 0; i < config.POSITION_GENERATION_MAX_ATTEMPTS; i++) {
        const x = Math.floor(Math.random() * (config.CANVAS_WIDTH - 2 * (visualRadius + config.EDGE_MARGIN))) + (visualRadius + config.EDGE_MARGIN);
        const y = Math.floor(Math.random() * (config.CANVAS_HEIGHT - 2 * (visualRadius + config.EDGE_MARGIN))) + (visualRadius + config.EDGE_MARGIN);

        if (isSafeToSpawnElement(x, y, collisionRadius, gameState,
            true, // checkVsObstacles
            false, // checkVsPlayers (음식은 플레이어 위에 스폰될 수 있음)
            false, // checkVsNpcs (음식은 NPC 위에 스폰될 수 있음)
            true  // checkVsFoods (다른 음식과는 겹치지 않도록)
        )) {
            return {
                id: foodId,
                name: foodTypeInfo.name, // 클라이언트에서 이미지 매칭용
                x: x,
                y: y,
                r: visualRadius, // 클라이언트 전송용 시각적 반지름
                collision_r: collisionRadius, // 서버 로직용 충돌 반지름
                special: foodTypeInfo.special,
                score: foodTypeInfo.score
            };
        }
    }
    // 최대 시도 후에도 안전한 위치를 찾지 못하면, 일단 랜덤 위치에 생성 (게임에 따라 null 반환 고려)
    console.warn(`[GameLogic] Failed to find a safe spot for food ${foodId} after ${config.POSITION_GENERATION_MAX_ATTEMPTS} attempts. Placing randomly.`);
    return {
        id: foodId, name: foodTypeInfo.name,
        x: Math.floor(Math.random() * (config.CANVAS_WIDTH - 2 * (visualRadius + config.EDGE_MARGIN))) + (visualRadius + config.EDGE_MARGIN),
        y: Math.floor(Math.random() * (config.CANVAS_HEIGHT - 2 * (visualRadius + config.EDGE_MARGIN))) + (visualRadius + config.EDGE_MARGIN),
        r: visualRadius, collision_r: collisionRadius, special: foodTypeInfo.special, score: foodTypeInfo.score
    };
}

/**
 * 게임 상태에 음식을 초기화하거나 추가합니다.
 * @param {object} gameState 현재 게임 상태 (foods 배열을 가짐)
 * @param {number|null} count 생성할 음식 개수 (null이면 config.INITIAL_FOOD_COUNT 사용)
 */
export function initializeFoods(gameState, count = null) {
    const targetCount = count === null ? config.INITIAL_FOOD_COUNT : count;
    if (!gameState.foods) {
        gameState.foods = [];
    }
    const foodsToAdd = Math.max(0, targetCount - gameState.foods.length);

    for (let i = 0; i < foodsToAdd; i++) {
        const newFood = generateFoodItem(gameState);
        if (newFood) {
            gameState.foods.push(newFood);
        }
    }
}

/**
 * 음식 ID로 음식 목록에서 해당 음식을 찾아 제거합니다.
 * @param {Array} foodsList 음식 객체 배열
 * @param {string} foodId 제거할 음식의 ID
 * @returns {object|null} 제거된 음식 객체 또는 찾지 못하면 null
 */
export function removeFoodById(foodsList, foodId) {
    const index = foodsList.findIndex(food => food.id === foodId);
    if (index !== -1) {
        return foodsList.splice(index, 1)[0];
    }
    return null;
}


// --- NPC 관련 로직 ---
/**
 * 새로운 NPC 아이템 하나를 생성합니다.
 * @param {object} gameState 현재 게임 상태
 * @returns {object|null} 생성된 NPC 객체 또는 생성 실패 시 null
 */
export function generateNpcItem(gameState) {
    const npcId = randomUUID();
    const npcRadius = config.NPC_COLLISION_RADIUS;

    for (let i = 0; i < config.POSITION_GENERATION_MAX_ATTEMPTS; i++) {
        const x = Math.floor(Math.random() * (config.CANVAS_WIDTH - 2 * (npcRadius + config.EDGE_MARGIN))) + (npcRadius + config.EDGE_MARGIN);
        const y = Math.floor(Math.random() * (config.CANVAS_HEIGHT - 2 * (npcRadius + config.EDGE_MARGIN))) + (npcRadius + config.EDGE_MARGIN);

        if (isSafeToSpawnElement(x, y, npcRadius, gameState,
            true, // checkVsObstacles
            true, // checkVsPlayers
            true, // checkVsNpcs (다른 NPC와 겹치지 않도록)
            false, // checkVsFoods (음식과는 겹쳐도 됨)
            npcId // 자기 자신은 무시
        )) {
            return {
                id: npcId,
                x: x,
                y: y,
                charImgName: config.NPC_CHAR_IMG_NAME, // 클라이언트 이미지 매칭용
                speed: config.NPC_SPEED * (1 + (Math.random() * 0.3 - 0.15)), // 속도 약간 랜덤화
                targetFoodId: null,
                isAngry: false,
                angryEndTime: 0,
                eatingTargetId: null,
                eatStartTime: 0,
                originalEatDuration: 1200 + Math.floor(Math.random() * 401) - 200, // 먹는 시간 랜덤화
                stuckCounter: 0,
                moveAttemptAngle: Math.random() * 2 * Math.PI,
                collisionRadius: npcRadius // 서버 로직용 충돌 반지름
            };
        }
    }
    console.warn(`[GameLogic] Failed to find a safe spot for NPC ${npcId}. Placing randomly.`);
    return { /* 기본값으로 랜덤 위치에 생성 */
        id: npcId,
        x: Math.floor(Math.random() * (config.CANVAS_WIDTH - 2 * (npcRadius + config.EDGE_MARGIN))) + (npcRadius + config.EDGE_MARGIN),
        y: Math.floor(Math.random() * (config.CANVAS_HEIGHT - 2 * (npcRadius + config.EDGE_MARGIN))) + (npcRadius + config.EDGE_MARGIN),
        charImgName: config.NPC_CHAR_IMG_NAME, speed: config.NPC_SPEED,
        targetFoodId: null, isAngry: false, angryEndTime: 0,
        eatingTargetId: null, eatStartTime: 0, originalEatDuration: 1200,
        stuckCounter: 0, moveAttemptAngle: Math.random() * 2 * Math.PI,
        collisionRadius: npcRadius
    };
}

/**
 * 게임 상태에 NPC를 초기화하거나 추가합니다.
 * @param {object} gameState 현재 게임 상태 (npcs 배열을 가짐)
 * @param {number|null} count 생성할 NPC 개수 (null이면 config.INITIAL_NPC_COUNT 사용)
 */
export function initializeNpcs(gameState, count = null) {
    const targetCount = count === null ? config.INITIAL_NPC_COUNT : count;
    if (!gameState.npcs) {
        gameState.npcs = [];
    }
    for (let i = 0; i < targetCount; i++) { // 항상 목표 개수만큼 새로 생성 (기존 NPC 유지 안 함)
        const newNpc = generateNpcItem(gameState);
        if (newNpc) {
            gameState.npcs.push(newNpc);
        }
    }
}


// --- 장애물(Obstacle) 관련 로직 ---
/**
 * 새로운 장애물 아이템 하나를 생성합니다.
 * @param {object} gameState 현재 게임 상태
 * @param {Array} existingObstaclesInBatch 현재 일괄 생성 중인 다른 장애물 목록
 * @returns {object|null} 생성된 장애물 객체 또는 생성 실패 시 null
 */
export function generateObstacleItem(gameState, existingObstaclesInBatch) {
    const obsType = Math.random() < 0.5 ? "circle" : "rect"; // 원 또는 사각형 랜덤
    const obsId = randomUUID();
    const mainColor = obsType === "circle" ? config.OBSTACLE_CIRCLE_COLOR : config.OBSTACLE_RECT_COLOR;

    for (let i = 0; i < config.POSITION_GENERATION_MAX_ATTEMPTS; i++) {
        let tempObsProps = {};
        let checkRadiusForSpawnSafety = 0;
        let centerXForSpawnSafety, centerYForSpawnSafety;

        if (obsType === "circle") {
            const r = Math.random() * (config.OBSTACLE_MAX_RADIUS - config.OBSTACLE_MIN_RADIUS) + config.OBSTACLE_MIN_RADIUS;
            const x = Math.random() * (config.CANVAS_WIDTH - 2 * (r + config.EDGE_MARGIN)) + (r + config.EDGE_MARGIN);
            const y = Math.random() * (config.CANVAS_HEIGHT - 2 * (r + config.EDGE_MARGIN)) + (r + config.EDGE_MARGIN);
            tempObsProps = { type: "circle", x, y, r };
            checkRadiusForSpawnSafety = r;
            centerXForSpawnSafety = x;
            centerYForSpawnSafety = y;
        } else { // rect
            const w = Math.random() * (config.OBSTACLE_MAX_SIZE - config.OBSTACLE_MIN_SIZE) + config.OBSTACLE_MIN_SIZE;
            const h = Math.random() * (config.OBSTACLE_MAX_SIZE - config.OBSTACLE_MIN_SIZE) + config.OBSTACLE_MIN_SIZE;
            const x = Math.random() * (config.CANVAS_WIDTH - config.EDGE_MARGIN - w) + config.EDGE_MARGIN; // 좌상단 기준
            const y = Math.random() * (config.CANVAS_HEIGHT - config.EDGE_MARGIN - h) + config.EDGE_MARGIN; // 좌상단 기준
            tempObsProps = { type: "rect", x, y, w, h };
            // isSafeToSpawnElement는 중심점과 반경을 사용하므로, 사각형의 중심과 외접원의 반경 근사치 사용
            centerXForSpawnSafety = x + w / 2;
            centerYForSpawnSafety = y + h / 2;
            checkRadiusForSpawnSafety = Math.sqrt((w/2)**2 + (h/2)**2); // 대각선 길이의 절반
        }

        if (isSafeToSpawnElement(centerXForSpawnSafety, centerYForSpawnSafety,
            checkRadiusForSpawnSafety,
            gameState,
            true, // checkVsObstacles (기존 장애물)
            true, // checkVsPlayers
            true, // checkVsNpcs
            false, // checkVsFoods
            obsId, // 자기 자신은 무시
            existingObstaclesInBatch // 현재 같이 생성 중인 다른 장애물
        )) {
            return { ...tempObsProps, id: obsId, mainColor: mainColor };
        }
    }
    console.warn(`[GameLogic] Failed to place obstacle ${obsId} safely. Skipping.`);
    return null;
}

/**
 * 게임 상태에 장애물을 (재)초기화합니다. 기존 장애물은 모두 제거됩니다.
 * @param {object} gameState 현재 게임 상태 (obstacles 배열을 가짐)
 * @param {number|null} count 생성할 장애물 개수 (null이면 config.OBSTACLE_COUNT 사용)
 */
export function initializeObstacles(gameState, count = null) {
    const defaultCount = Math.floor(Math.random() * (config.OBSTACLE_COUNT_MAX - config.OBSTACLE_COUNT_MIN + 1)) + config.OBSTACLE_COUNT_MIN;
    const targetCount = count === null ? defaultCount : count;
    gameState.obstacles = []; // 기존 장애물 모두 제거
    const newlyGeneratedObstaclesInThisCall = [];

    for (let i = 0; i < targetCount; i++) {
        const item = generateObstacleItem(gameState, newlyGeneratedObstaclesInThisCall);
        if (item) {
            newlyGeneratedObstaclesInThisCall.push(item); // 현재 호출에서 생성된 것들끼리도 겹치지 않도록
            gameState.obstacles.push(item);
        }
    }
}