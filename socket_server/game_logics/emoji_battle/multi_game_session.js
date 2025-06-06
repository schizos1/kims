// socket_server/game_logics/emoji_battle/multi_game_session.js
// 두 명이 이모지를 주고받아 50회 맞히면 승리하는 게임 세션

import { HIT_TO_WIN } from './config.js';
import { userPoints } from '../user_points.js';
import { recordWin, recordLoss } from '../game_records.js';

const FIELD_WIDTH = 800; // 캔버스 가로 길이와 동일하게 사용

class EmojiBattleSession {
    constructor(io, room) {
        this.io = io;
        this.room = room;
        this.players = new Map();
        this.isRunning = false;
    }

    _ensurePoints(id) {
        if (!userPoints.has(id)) userPoints.set(id, 1000);
    }

    addPlayer(socket, userData) {
        socket.join(this.room);
        this._ensurePoints(socket.id);
        userPoints.set(socket.id, userPoints.get(socket.id) - 50);
        const startX = this.players.size === 0 ? FIELD_WIDTH * 0.2 : FIELD_WIDTH * 0.8;
        this.players.set(socket.id, { socket, user: userData.user, hits: 0, x: startX });
        if (this.players.size === 2 && !this.isRunning) this.startGame();
    }

    hasPlayer(id) { return this.players.has(id); }

    removePlayer(id) {
        this.players.delete(id);
        this.io.to(this.room).emit('emoji_player_left', { id });
    }

    isEmpty() { return this.players.size === 0; }

    startGame() {
        this.isRunning = true;
        this.io.to(this.room).emit('emoji_start', {
            players: [...this.players.entries()].map(([id, p]) => ({ id, user: p.user, x: p.x }))
        });
    }

    handleEmojiThrow(id, data) {
        if (!this.isRunning) return;
        this.io.to(this.room).emit('emoji_thrown', { id, emoji: data.emoji });
    }

    handleEmojiHit(attackerId, data) {
        if (!this.isRunning) return;
        const attacker = this.players.get(attackerId);
        if (!attacker) return;
        attacker.hits += 1;
        this.io.to(this.room).emit('emoji_hit', { attacker: attackerId, target: data.target, emoji: data.emoji, hits: attacker.hits });
        if (attacker.hits >= HIT_TO_WIN) {
            this._gameOver(attackerId);
        }
    }

    handleEmojiMove(id, data) {
        if (!this.isRunning) return;
        const player = this.players.get(id);
        if (!player) return;
        const newX = Math.max(0, Math.min(FIELD_WIDTH, data.x));
        player.x = newX;
        this.io.to(this.room).emit('emoji_move', { id, x: player.x });
    }

    _gameOver(winnerId) {
        this.isRunning = false;
        userPoints.set(winnerId, (userPoints.get(winnerId) || 0) + 100);
        for (const [pid] of this.players) {
            if (pid === winnerId) recordWin(pid); else recordLoss(pid);
        }
        this.io.to(this.room).emit('emoji_game_over', { winner: winnerId, points: userPoints.get(winnerId) });
    }

    destroy() {
        this.isRunning = false;
    }
}

export default EmojiBattleSession;
