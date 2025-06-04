// socket_server/game_logics/eat_food/game_rules.js
// 'eat_food' 미니게임의 서버 측 핵심 게임 규칙 및 로직 (상세 구현)

import * as config from './config.js';
import {
    checkCircleCircleCollision,
    checkCircleRectCollision,
    isPositionWithinCanvasBounds
} from './collision_utils.js';
import { removeFoodById, generateFoodItem } from './entity_manager.js';

/**
 * 플레이어 이동 시도 및 충돌 처리
 * @param {object} playerState 현재 플레이어 상태
 * @param {number} requestedX 요청된 x 좌표
 * @param {number} requestedY 요청된 y 좌표
 * @param {object} gameState 현재 게임 상태 (장애물 정보 포함)
 * @returns {{x: number, y: number, collided: boolean}} 최종 위치 및 충돌 여부
 */
export function attemptPlayerMove(playerState, requestedX, requestedY, gameState) {
    const playerRadius = playerState.collisionRadius || config.PLAYER_COLLISION_RADIUS;
    let nextX = requestedX;
    let nextY = requestedY;

    nextX = Math.max(playerRadius + config.EDGE_MARGIN, Math.min(nextX, config.CANVAS_WIDTH - playerRadius - config.EDGE_MARGIN));
    nextY = Math.max(playerRadius + config.EDGE_MARGIN, Math.min(nextY, config.CANVAS_HEIGHT - playerRadius - config.EDGE_MARGIN));

    if (gameState.obstacles) {
        for (const obs of gameState.obstacles) {
            let collision = false;
            if (obs.type === 'circle') {
                if (checkCircleCircleCollision(nextX, nextY, playerRadius, obs.x, obs.y, obs.r)) {
                    collision = true;
                }
            } else if (obs.type === 'rect') {
                if (checkCircleRectCollision(nextX, nextY, playerRadius, obs.x, obs.y, obs.w, obs.h)) {
                    collision = true;
                }
            }
            if (collision) {
                // 충돌 시 이전 위치 반환 (Python 로직과 유사하게)
                return { x: playerState.x, y: playerState.y, collided: true };
            }
        }
    }
    return { x: nextX, y: nextY, collided: false };
}

/**
 * NPC가 특정 위치로 안전하게 이동할 수 있는지 확인합니다.
 * @param {number} nextX 이동할 x 좌표
 * @param {number} nextY 이동할 y 좌표
 * @param {number} actorRadius 이동하는 액터의 충돌 반경
 * @param {object} gameState 현재 게임 상태
 * @param {string} ownId 자신의 ID (다른 NPC와 충돌 시 자신은 제외)
 * @returns {boolean} 안전하게 이동 가능하면 true
 */
function isSafeToMoveActor(nextX, nextY, actorRadius, gameState, ownId) {
    if (!isPositionWithinCanvasBounds(nextX, nextY, actorRadius, config)) {
        return false;
    }

    if (gameState.obstacles) {
        for (const obs of gameState.obstacles) {
            if (obs.type === 'circle' && checkCircleCircleCollision(nextX, nextY, actorRadius, obs.x, obs.y, obs.r)) return false;
            if (obs.type === 'rect' && checkCircleRectCollision(nextX, nextY, actorRadius, obs.x, obs.y, obs.w, obs.h)) return false;
        }
    }

    if (gameState.npcs) {
        for (const otherNpc of gameState.npcs) {
            if (otherNpc.id === ownId) continue;
            if (checkCircleCircleCollision(nextX, nextY, actorRadius, otherNpc.x, otherNpc.y, otherNpc.collisionRadius + 2)) return false;
        }
    }
    return true;
}

/**
 * 단일 NPC의 상태를 업데이트합니다.
 * @param {object} npcState 현재 NPC 상태 객체
 * @param {object} gameState 현재 게임 상태
 * @param {number} currentTimeMs 현재 시간 (밀리초)
 */
function updateOneNpc(npcState, gameState, currentTimeMs) {
    if (npcState.isAngry && currentTimeMs > npcState.angryEndTime) {
        npcState.isAngry = false;
    }

    if (npcState.eatingTargetId) {
        if (currentTimeMs - npcState.eatStartTime > npcState.originalEatDuration) {
            const eatenFood = removeFoodById(gameState.foods, npcState.eatingTargetId);
            if (eatenFood) {
                const newFood = generateFoodItem(gameState);
                if (newFood) gameState.foods.push(newFood);
            }
            npcState.eatingTargetId = null;
            npcState.targetFoodId = null;
        } else {
            return;
        }
    }

    if (npcState.isAngry) return;

    let currentTargetFoodObject = null;
    if (npcState.targetFoodId) {
        currentTargetFoodObject = gameState.foods.find(f => f.id === npcState.targetFoodId);
        if (!currentTargetFoodObject) npcState.targetFoodId = null;
    }

    if (!npcState.targetFoodId && gameState.foods && gameState.foods.length > 0) {
        let closestFood = null;
        let minDistanceSq = Infinity;
        const targetedByOthers = new Set(gameState.npcs.filter(oNpc => oNpc.id !== npcState.id && oNpc.targetFoodId).map(oNpc => oNpc.targetFoodId));
        for (const food of gameState.foods) {
            if (targetedByOthers.has(food.id) && !food.special) continue;
            const distSq = (npcState.x - food.x) ** 2 + (npcState.y - food.y) ** 2;
            if (distSq < minDistanceSq) {
                minDistanceSq = distSq;
                closestFood = food;
            }
        }
        if (closestFood) {
            npcState.targetFoodId = closestFood.id;
            currentTargetFoodObject = closestFood;
        }
    }

    if (currentTargetFoodObject) {
        const targetX = currentTargetFoodObject.x;
        const targetY = currentTargetFoodObject.y;
        const dx = targetX - npcState.x;
        const dy = targetY - npcState.y;
        const distanceToTarget = Math.hypot(dx, dy);

        if (distanceToTarget < (npcState.collisionRadius + currentTargetFoodObject.collision_r + 2)) {
            npcState.eatingTargetId = npcState.targetFoodId;
            npcState.eatStartTime = currentTimeMs;
        } else if (distanceToTarget > 0) {
            const moveX = (dx / distanceToTarget) * npcState.speed;
            const moveY = (dy / distanceToTarget) * npcState.speed;
            const nextX = npcState.x + moveX;
            const nextY = npcState.y + moveY;

            if (isSafeToMoveActor(nextX, nextY, npcState.collisionRadius, gameState, npcState.id)) {
                npcState.x = nextX;
                npcState.y = nextY;
                npcState.stuckCounter = 0;
            } else {
                npcState.stuckCounter++;
                if (npcState.stuckCounter > 3) {
                    npcState.targetFoodId = null;
                    npcState.moveAttemptAngle = Math.random() * 2 * Math.PI;
                    npcState.stuckCounter = 0;
                } else {
                    const currentAngle = Math.atan2(moveY, moveX);
                    npcState.moveAttemptAngle = currentAngle + (Math.random() < 0.5 ? -Math.PI / 2 : Math.PI / 2) + (Math.random() * 0.4 - 0.2);
                    const altMoveX = Math.cos(npcState.moveAttemptAngle) * npcState.speed * 0.7;
                    const altMoveY = Math.sin(npcState.moveAttemptAngle) * npcState.speed * 0.7;
                    if (isSafeToMoveActor(npcState.x + altMoveX, npcState.y + altMoveY, npcState.collisionRadius, gameState, npcState.id)) {
                        npcState.x += altMoveX;
                        npcState.y += altMoveY;
                    }
                }
            }
        }
    } else {
        if (Math.random() < 0.05 || npcState.stuckCounter > 8) {
            npcState.moveAttemptAngle = Math.random() * 2 * Math.PI;
            npcState.stuckCounter = 0;
        }
        const wanderDx = Math.cos(npcState.moveAttemptAngle) * npcState.speed * 0.5;
        const wanderDy = Math.sin(npcState.moveAttemptAngle) * npcState.speed * 0.5;
        const nextX = npcState.x + wanderDx;
        const nextY = npcState.y + wanderDy;

        if (isSafeToMoveActor(nextX, nextY, npcState.collisionRadius, gameState, npcState.id)) {
            npcState.x = nextX;
            npcState.y = nextY;
        } else {
            npcState.moveAttemptAngle = Math.random() * 2 * Math.PI;
            npcState.stuckCounter++;
        }
    }
    npcState.x = Math.max(npcState.collisionRadius + config.EDGE_MARGIN, Math.min(npcState.x, config.CANVAS_WIDTH - npcState.collisionRadius - config.EDGE_MARGIN));
    npcState.y = Math.max(npcState.collisionRadius + config.EDGE_MARGIN, Math.min(npcState.y, config.CANVAS_HEIGHT - npcState.collisionRadius - config.EDGE_MARGIN));
}

/**
 * 모든 NPC들의 상태를 업데이트합니다.
 * @param {object} gameState 현재 게임 상태
 * @param {number} currentTimeMs 현재 시간 (밀리초)
 */
export function updateAllNpcs(gameState, currentTimeMs) {
    if (gameState.npcs) {
        gameState.npcs.forEach(npcState => {
            updateOneNpc(npcState, gameState, currentTimeMs);
        });
    }
}

/**
 * NPC와 플레이어 간의 충돌을 처리합니다.
 * @param {object} gameState 현재 게임 상태
 * @param {number} currentTimeMs 현재 시간 (밀리초)
 */
export function handleNpcPlayerCollisions(gameState, currentTimeMs) {
    if (!gameState.npcs || !gameState.player) return;
    const player = gameState.player;

    gameState.npcs.forEach(npcState => {
        if (npcState.isAngry && currentTimeMs < npcState.angryEndTime) {
            return;
        }
        if (checkCircleCircleCollision(npcState.x, npcState.y, npcState.collisionRadius, player.x, player.y, player.collisionRadius)) {
            npcState.isAngry = true;
            npcState.angryEndTime = currentTimeMs + 2000; // 2초간 화남
            npcState.targetFoodId = null;
            npcState.eatingTargetId = null;

            const dx = npcState.x - player.x;
            const dy = npcState.y - player.y;
            const distance = Math.hypot(dx, dy) || 0.1;
            const overlap = (npcState.collisionRadius + player.collisionRadius) - distance;
            
            if (overlap > 0) {
                const pushRatioNpc = 0.6;
                const pushRatioPlayer = 0.4;
                const totalPush = overlap + 1.5; // 기본 반발력 추가

                const pushX = (dx / distance) * totalPush;
                const pushY = (dy / distance) * totalPush;

                let npcNextX = npcState.x + pushX * pushRatioNpc;
                let npcNextY = npcState.y + pushY * pushRatioNpc;
                let playerNextX = player.x - pushX * pushRatioPlayer;
                let playerNextY = player.y - pushY * pushRatioPlayer;

                npcState.x = Math.max(npcState.collisionRadius + config.EDGE_MARGIN, Math.min(npcNextX, config.CANVAS_WIDTH - npcState.collisionRadius - config.EDGE_MARGIN));
                npcState.y = Math.max(npcState.collisionRadius + config.EDGE_MARGIN, Math.min(npcNextY, config.CANVAS_HEIGHT - npcState.collisionRadius - config.EDGE_MARGIN));
                player.x = Math.max(player.collisionRadius + config.EDGE_MARGIN, Math.min(playerNextX, config.CANVAS_WIDTH - player.collisionRadius - config.EDGE_MARGIN));
                player.y = Math.max(player.collisionRadius + config.EDGE_MARGIN, Math.min(playerNextY, config.CANVAS_HEIGHT - player.collisionRadius - config.EDGE_MARGIN));
            }
        }
    });
}

/**
 * 플레이어 승리 조건을 확인합니다.
 * @param {object} playerState 플레이어 상태 객체
 * @returns {boolean} 승리 조건 충족 시 true, 아니면 false
 */
export function checkPlayerWinCondition(playerState) {
    if (playerState && typeof playerState.eatCount === 'number') {
        return playerState.eatCount >= config.TOTAL_FOODS_TO_WIN;
    }
    return false;
}