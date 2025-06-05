// socket_server/game_logics/eat_food/multi_game_session.js
// Simple two-player session managing points
import * as config from './config.js';
import {
    initializeFoods,
    initializeNpcs,
    initializeObstacles,
    removeFoodById,
    generateFoodItem,
    generateNpcItem
} from './entity_manager.js';
import {
    attemptPlayerMove,
    updateAllNpcs,
    handleNpcPlayerCollisions,
    checkPlayerWinCondition
} from './game_rules.js';
import { checkCircleCircleCollision } from './collision_utils.js';
import { userPoints } from '../user_points.js';
import { recordWin, recordLoss } from '../game_records.js';

class MultiGameSession {
    constructor(io, room) {
        this.io = io;
        this.room = room;
        this.players = new Map();
        this.gameState = { foods: [], npcs: [], obstacles: [] };
        this.loop = null;
        this.obstacleLoop = null;
        this.npcSpawnLoop = null;
        this.usedDinos = new Set();
        this.isRunning = false;
    }

    _ensurePoints(id) {
        if (!userPoints.has(id)) userPoints.set(id, 1000);
    }

    addPlayer(socket, userData) {
        socket.join(this.room);
        this._ensurePoints(socket.id);
        userPoints.set(socket.id, userPoints.get(socket.id) - 50);
        let chosenChar = userData.charImgPath;
        if (!chosenChar) {
            const options = ['dino1.png', 'dino2.png'];
            for (const opt of options) {
                if (!this.usedDinos.has(opt)) { chosenChar = opt; break; }
            }
            if (!chosenChar) { chosenChar = options[Math.floor(Math.random()*2)]; }
        }
        this.usedDinos.add(chosenChar);
        this.players.set(socket.id, {
            socket,
            user: userData.user,
            x: config.CANVAS_WIDTH / 2,
            y: config.CANVAS_HEIGHT / 2,
            score: 0,
            eatCount: 0,
            collisionRadius: config.PLAYER_COLLISION_RADIUS,
            charImgPath: chosenChar
        });
        if (this.players.size === 2 && !this.isRunning) this.startGame();
    }

    hasPlayer(id) { return this.players.has(id); }

    removePlayer(id) {
        const p = this.players.get(id);
        if (p) this.usedDinos.delete(p.charImgPath);
        this.players.delete(id);
        this.io.to(this.room).emit('player_left', { id });
    }

    isEmpty() { return this.players.size === 0; }

    startGame() {
        this.isRunning = true;
        initializeFoods(this.gameState, config.INITIAL_FOOD_COUNT);
        initializeNpcs(this.gameState, config.INITIAL_NPC_COUNT);
        initializeObstacles(this.gameState); // 개수는 설정 범위 내 랜덤
        this.loop = setInterval(() => this._gameLoop(), config.SINGLE_GAME_LOOP_INTERVAL);
        this.obstacleLoop = setInterval(() => initializeObstacles(this.gameState), config.OBSTACLE_REGEN_INTERVAL);
        this.npcSpawnLoop = setInterval(() => {
            const npc = generateNpcItem(this.gameState);
            if (npc) {
                this.gameState.npcs.push(npc);
                const extraFood = generateFoodItem(this.gameState);
                if (extraFood) this.gameState.foods.push(extraFood);
                this.io.to(this.room).emit('npc_spawned', { npc });
            }
        }, config.NPC_SPAWN_INTERVAL);
        this.io.to(this.room).emit('eat_food_start', {
            players: [...this.players.values()].map(p => ({ id: p.socket.id, user: p.user })),
            foods: this.gameState.foods,
            npcs: this.gameState.npcs,
            obstacles: this.gameState.obstacles
        });
    }

    _gameLoop() {
        const now = Date.now();
        updateAllNpcs(this.gameState, now);
        handleNpcPlayerCollisions(this.gameState, now);
        this.io.to(this.room).emit('eat_food_state', {
            players: [...this.players.entries()].map(([id, p]) => ({ id, x: p.x, y: p.y, score: p.score })),
            foods: this.gameState.foods,
            npcs: this.gameState.npcs,
            obstacles: this.gameState.obstacles
        });
    }

    handlePlayerMove(id, data) {
        const player = this.players.get(id);
        if (!player || !this.isRunning) return;
        const result = attemptPlayerMove(player, data.x, data.y, this.gameState);
        player.x = result.x;
        player.y = result.y;
    }

    handlePlayerEatAttempt(id, { foodId }) {
        const player = this.players.get(id);
        if (!player || !this.isRunning) return;
        const food = this.gameState.foods.find(f => f.id === foodId);
        if (food && checkCircleCircleCollision(player.x, player.y, player.collisionRadius, food.x, food.y, food.collision_r)) {
            removeFoodById(this.gameState.foods, foodId);
            const newFood = generateFoodItem(this.gameState);
            if (newFood) this.gameState.foods.push(newFood);
            player.score += food.score;
            player.eatCount += 1;
            if (checkPlayerWinCondition(player)) {
                this._gameOver(player.socket.id);
            }
        }
    }

    _gameOver(winnerId) {
        this.isRunning = false;
        clearInterval(this.loop); clearInterval(this.obstacleLoop); clearInterval(this.npcSpawnLoop);
        userPoints.set(winnerId, (userPoints.get(winnerId) || 0) + 100);
        for (const [pid] of this.players) {
            if (pid === winnerId) recordWin(pid); else recordLoss(pid);
        }
        this.io.to(this.room).emit('eat_food_game_over', { winner: winnerId, points: userPoints.get(winnerId) });
    }

    destroy() {
        clearInterval(this.loop); clearInterval(this.obstacleLoop); clearInterval(this.npcSpawnLoop);
    }
}

export { userPoints };
export default MultiGameSession;
