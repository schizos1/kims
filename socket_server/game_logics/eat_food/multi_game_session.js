// socket_server/game_logics/eat_food/multi_game_session.js
// Simple two-player session managing points
import * as config from './config.js';
import {
    initializeFoods,
    initializeNpcs,
    initializeObstacles,
    removeFoodById,
    generateFoodItem
} from './entity_manager.js';
import {
    attemptPlayerMove,
    updateAllNpcs,
    handleNpcPlayerCollisions,
    checkPlayerWinCondition
} from './game_rules.js';
import { checkCircleCircleCollision } from './collision_utils.js';

const userPoints = new Map();

class MultiGameSession {
    constructor(io, room) {
        this.io = io;
        this.room = room;
        this.players = new Map();
        this.gameState = { foods: [], npcs: [], obstacles: [] };
        this.loop = null;
        this.obstacleLoop = null;
        this.isRunning = false;
    }

    _ensurePoints(id) {
        if (!userPoints.has(id)) userPoints.set(id, 1000);
    }

    addPlayer(socket, userData) {
        socket.join(this.room);
        this._ensurePoints(socket.id);
        userPoints.set(socket.id, userPoints.get(socket.id) - 50);
        this.players.set(socket.id, {
            socket,
            user: userData.user,
            x: config.CANVAS_WIDTH / 2,
            y: config.CANVAS_HEIGHT / 2,
            score: 0,
            eatCount: 0,
            collisionRadius: config.PLAYER_COLLISION_RADIUS,
            charImgPath: userData.charImgPath || 'dino1.png'
        });
        if (this.players.size === 2 && !this.isRunning) this.startGame();
    }

    hasPlayer(id) { return this.players.has(id); }

    removePlayer(id) {
        this.players.delete(id);
        this.io.to(this.room).emit('player_left', { id });
    }

    isEmpty() { return this.players.size === 0; }

    startGame() {
        this.isRunning = true;
        initializeFoods(this.gameState, config.INITIAL_FOOD_COUNT);
        initializeNpcs(this.gameState, config.INITIAL_NPC_COUNT);
        initializeObstacles(this.gameState, config.OBSTACLE_COUNT);
        this.loop = setInterval(() => this._gameLoop(), config.SINGLE_GAME_LOOP_INTERVAL);
        this.obstacleLoop = setInterval(() => initializeObstacles(this.gameState, config.OBSTACLE_COUNT), config.OBSTACLE_REGEN_INTERVAL);
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
        clearInterval(this.loop); clearInterval(this.obstacleLoop);
        userPoints.set(winnerId, (userPoints.get(winnerId) || 0) + 100);
        this.io.to(this.room).emit('eat_food_game_over', { winner: winnerId, points: userPoints.get(winnerId) });
    }

    destroy() {
        clearInterval(this.loop); clearInterval(this.obstacleLoop);
    }
}

export { userPoints };
export default MultiGameSession;
