// socket_server/game_logics/eat_food/single_game_session.js
// 'eat_food' 미니게임의 싱글플레이어 게임 세션 관리 (game_rules.js 사용하도록 수정)

import * as config from './config.js';
import {
    initializeFoods,
    initializeNpcs,
    initializeObstacles,
    removeFoodById,
    generateFoodItem // game_rules.js에서도 사용하므로 여기서도 import 할 수 있음 (또는 game_rules를 통해 간접 사용)
} from './entity_manager.js';
import {
    checkCircleCircleCollision
    // isPositionWithinCanvasBounds // game_rules.js 내부에서 주로 사용
} from './collision_utils.js';
// game_rules.js에서 실제 게임 로직 함수들을 가져옴
import {
    attemptPlayerMove,
    updateAllNpcs,
    handleNpcPlayerCollisions,
    checkPlayerWinCondition
} from './game_rules.js';

// --- 싱글플레이어 게임 세션 클래스 ---
class SingleGameSession {
    constructor(socket, userData) {
        this.socket = socket; // 이 세션에 연결된 클라이언트 소켓
        this.gameState = {};  // 이 세션의 게임 상태
        this.gameLoopIntervalId = null;
        this.obstacleRegenIntervalId = null;
        this.npcSpawnIntervalId = null;
        this.isGameRunning = false;
        this.userData = userData; // { user, charImgPath }

        this._initializeGame();
        this._startLoops();

        console.log(`[SingleGameSession] New session created for socket ${socket.id}, user ${userData.user}`);
    }

    _initializeGame() {
        this.gameState.player = {
            id: this.socket.id,
            user: this.userData.user,
            x: config.CANVAS_WIDTH / 2,
            y: config.CANVAS_HEIGHT / 2,
            score: 0,
            eatCount: 0,
            charImgPath: this.userData.charImgPath || (Math.random() < 0.5 ? "dino1.png" : "dino2.png"), // 랜덤 선택
            collisionRadius: config.PLAYER_COLLISION_RADIUS
        };
        this.gameState.foods = [];
        this.gameState.npcs = [];
        this.gameState.obstacles = [];

        initializeFoods(this.gameState, config.INITIAL_FOOD_COUNT);
        initializeNpcs(this.gameState, config.INITIAL_NPC_COUNT);
        initializeObstacles(this.gameState); // 개수는 설정 범위 내 랜덤

        this.isGameRunning = true;

        this.socket.emit("game_start_info", {
            player: this.gameState.player,
            foods: this.gameState.foods,
            npcs: this.gameState.npcs,
            obstacles: this.gameState.obstacles,
            total_foods_to_win: config.TOTAL_FOODS_TO_WIN,
            canvas_width: config.CANVAS_WIDTH,
            canvas_height: config.CANVAS_HEIGHT
        });
        console.log(`[SingleGameSession] Game initialized for ${this.userData.user}. Sent game_start_info.`);
    }

    _startLoops() {
        if (this.gameLoopIntervalId) clearInterval(this.gameLoopIntervalId);
        this.gameLoopIntervalId = setInterval(() => {
            if (this.isGameRunning) {
                this._gameLoop();
            }
        }, config.SINGLE_GAME_LOOP_INTERVAL);

        if (this.obstacleRegenIntervalId) clearInterval(this.obstacleRegenIntervalId);
        this.obstacleRegenIntervalId = setInterval(() => {
            if (this.isGameRunning) {
                this._regenerateObstacles();
            }
        }, config.OBSTACLE_REGEN_INTERVAL);
        if (this.npcSpawnIntervalId) clearInterval(this.npcSpawnIntervalId);
        this.npcSpawnIntervalId = setInterval(() => {
            if (this.isGameRunning) {
                const npc = generateNpcItem(this.gameState);
                if (npc) {
                    this.gameState.npcs.push(npc);
                    const extraFood = generateFoodItem(this.gameState);
                    if (extraFood) this.gameState.foods.push(extraFood);
                }
            }
        }, config.NPC_SPAWN_INTERVAL);
        console.log(`[SingleGameSession] Game loops started for ${this.userData.user}.`);
    }

    _gameLoop() {
        const currentTimeMs = Date.now();

        updateAllNpcs(this.gameState, currentTimeMs); // game_rules.js에서 가져온 함수 사용
        handleNpcPlayerCollisions(this.gameState, currentTimeMs); // game_rules.js에서 가져온 함수 사용
        
        this.socket.emit("state_update", {
            player: this.gameState.player,
            foods: this.gameState.foods,
            npcs: this.gameState.npcs,
            obstacles: this.gameState.obstacles
        });
    }

    _regenerateObstacles() {
        console.log(`[SingleGameSession] Regenerating obstacles for ${this.userData.user}`);
        initializeObstacles(this.gameState); // entity_manager.js 함수 사용 (랜덤 개수)
    }

    handlePlayerMove(moveData) {
        if (!this.isGameRunning || !this.gameState.player) return;

        const { x: requestedX, y: requestedY } = moveData;
        const playerState = this.gameState.player;

        // game_rules.js에서 가져온 함수 사용
        const { x: finalX, y: finalY, collided } = attemptPlayerMove(playerState, requestedX, requestedY, this.gameState);
        
        playerState.x = finalX;
        playerState.y = finalY;

        if (collided) {
            console.log(`[SingleGameSession] Player ${playerState.user} move attempt resulted in collision. Pos: (${finalX},${finalY})`);
            // 충돌 시 클라이언트에게 즉시 보정된 위치를 알려줄 수 있음 (선택 사항)
            // this.socket.emit("player_position_corrected", { x: finalX, y: finalY, collided: true });
        }
        // 플레이어 위치 변경은 다음 _gameLoop의 state_update 시 일괄 전송됨
    }

    handlePlayerEatAttempt(eatData) {
        if (!this.isGameRunning || !this.gameState.player || !this.gameState.foods) return;

        const { foodId } = eatData;
        const playerState = this.gameState.player;
        const foodToEat = this.gameState.foods.find(f => f.id === foodId);

        if (foodToEat) {
            if (checkCircleCircleCollision( // collision_utils.js 함수 사용
                playerState.x, playerState.y, playerState.collisionRadius,
                foodToEat.x, foodToEat.y, foodToEat.collision_r
            )) {
                console.log(`[SingleGameSession] Player ${playerState.user} ate food ${foodToEat.name}`);
                playerState.score += foodToEat.score;
                playerState.eatCount += 1;

                removeFoodById(this.gameState.foods, foodId); // entity_manager.js 함수 사용
                
                const newFood = generateFoodItem(this.gameState); // entity_manager.js 함수 사용
                if (newFood) this.gameState.foods.push(newFood);

                // game_rules.js에서 가져온 함수 사용
                if (checkPlayerWinCondition(playerState)) {
                    this._gameOver(playerState.user);
                }
                // 음식 먹은 상태는 다음 _gameLoop의 state_update 시 클라이언트에 전송됨
            } else {
                console.log(`[SingleGameSession] Player ${playerState.user} eat attempt for ${foodId} failed - not close enough.`);
            }
        } else {
            console.log(`[SingleGameSession] Player ${playerState.user} eat attempt for ${foodId} failed - food not found.`);
        }
    }

    _gameOver(winnerName) {
        console.log(`[SingleGameSession] Game over for ${this.userData.user}. Winner: ${winnerName}`);
        this.isGameRunning = false;
        this._stopLoops();
        this.socket.emit("game_over", { winner: winnerName, finalScore: this.gameState.player.score });
    }

    _stopLoops() {
        if (this.gameLoopIntervalId) {
            clearInterval(this.gameLoopIntervalId);
            this.gameLoopIntervalId = null;
        }
        if (this.obstacleRegenIntervalId) {
            clearInterval(this.obstacleRegenIntervalId);
            this.obstacleRegenIntervalId = null;
        }
        if (this.npcSpawnIntervalId) {
            clearInterval(this.npcSpawnIntervalId);
            this.npcSpawnIntervalId = null;
        }
        console.log(`[SingleGameSession] Game loops stopped for ${this.userData.user}.`);
    }

    destroy() {
        console.log(`[SingleGameSession] Destroying session for socket ${this.socket.id}, user ${this.userData.user}`);
        this._stopLoops();
        this.isGameRunning = false;
    }
}

export default SingleGameSession;