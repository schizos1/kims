// socket_server/game_logics/emoji_battle/multi_game_session.js (v1.6 개선 - 디버그 로그 추가)

import { HIT_TO_WIN, EMOJI_TYPES } from './config.js';
import { userPoints } from '../user_points.js';
import { recordWin, recordLoss } from '../game_records.js';

const FIELD_WIDTH = 800; // 캔버스 가로 길이와 동일하게 사용

class EmojiBattleSession {
    constructor(io, room) {
        this.io = io;
        this.room = room;
        this.players = new Map();
        this.isRunning = false;
        console.log(`[EmojiBattleSession] New session CREATED for room: ${room}`);
    }

    _ensurePoints(id) {
        if (!userPoints.has(id)) userPoints.set(id, 1000);
    }

    addPlayer(socket, userData) {
        if (!userData || typeof userData.emoji !== 'string') {
            console.error(`[EmojiBattleSession] Invalid userData received from socket ${socket.id}. Aborting addPlayer.`);
            return;
        }

        let player;
        if (this.players.has(socket.id)) {
            console.log(`[EmojiBattleSession] Player ${socket.id} is RE-JOINING room ${this.room}.`);
            player = this.players.get(socket.id);
            player.emoji = userData.emoji; // 캐릭터 변경 허용
            player.socket = socket; // 소켓 객체 갱신
        } else {
            console.log(`[EmojiBattleSession] New player ${socket.id} is JOINING room ${this.room}.`);
            socket.join(this.room);
            this._ensurePoints(socket.id);
            userPoints.set(socket.id, userPoints.get(socket.id) - 50); // 참가비

            let playerX;
            if (this.players.size === 0) {
                playerX = FIELD_WIDTH * 0.2; // 첫 플레이어는 왼쪽
            } else {
                const otherPlayer = this.players.values().next().value;
                playerX = (otherPlayer.x === FIELD_WIDTH * 0.2) ? FIELD_WIDTH * 0.8 : FIELD_WIDTH * 0.2;
            }

            player = {
                socket,
                user: userData.user,
                emoji: userData.emoji,
                hits: 0,
                x: playerX,
                score: 0,
                state: null,
                ready: false 
            };
            this.players.set(socket.id, player);
        }
        
        player.ready = true; 
        console.log(`[EmojiBattleSession] Player ${socket.id} is now ready.`);
        console.log(`[EmojiBattleSession] Player count in room ${this.room}: ${this.players.size}`);

        if (this.players.size === 2 && !this.isRunning) {
            const players = Array.from(this.players.values());
            if (players.every(p => p.ready)) {
                this.startGame();
            } else {
                console.log(`[EmojiBattleSession] Waiting for the other player to be ready.`);
            }
        }
    }

    hasPlayer(id) { return this.players.has(id); }

    removePlayer(id) {
        console.log(`[EmojiBattleSession] removePlayer CALLED for ID: ${id}.`);
        if (this.players.has(id)) {
            this.players.delete(id);
            this.io.to(this.room).emit('emoji_player_left', { id });
            if (this.isRunning) {
                console.log(`[EmojiBattleSession] A player left during the game. Stopping game.`);
                this.isRunning = false;
                this.players.forEach(p => p.ready = false);
            }
        }
    }

    isEmpty() { return this.players.size === 0; }

    startGame() {
        console.log(`[EmojiBattleSession] startGame CALLED for room ${this.room}.`);
        this.isRunning = true;

        this.players.forEach(player => {
            player.hits = 0;
            player.score = 0;
            player.state = null;
            player.ready = false;
        });

        const playersData = [...this.players.entries()].map(([id, p]) => ({
            id,
            user: p.user,
            emoji: p.emoji,
            x: p.x
        }));
        console.log(`[EmojiBattleSession] Emitting 'emoji_start' with players:`, JSON.stringify(playersData));
        this.io.to(this.room).emit('emoji_start', { players: playersData });
    }

    handleEmojiThrow(id, data) {
        if (!this.isRunning) return;
        this.io.to(this.room).emit('emoji_thrown', { 
            id, 
            emoji: data.emoji, 
            x: data.x
        });
    }

    handlePlayerHitTarget(attackerId, data) {
        if (!this.isRunning) return;

        const attacker = this.players.get(attackerId);
        const target = this.players.get(data.target);

        if (!attacker || !target) {
            console.error(`[EmojiBattleSession][DEBUG] Attacker or Target not found. AttackerID: ${attackerId}, TargetID: ${data.target}`);
            return;
        }
        
        console.log(`[EmojiBattleSession][DEBUG] Hit event received. Attacker: ${attackerId}, Emoji: ${data.emoji}`);
        
        // [수정] 명중 및 점수 계산 로직에 상세 디버그 로그 추가
        const emojiInfo = EMOJI_TYPES.find(e => e.emoji === data.emoji);
        const pointsToAdd = emojiInfo?.points || 100;

        console.log(`[EmojiBattleSession][DEBUG] Before calculation - Hits: ${attacker.hits}, Score: ${attacker.score}`);
        console.log(`[EmojiBattleSession][DEBUG] Points to add: ${pointsToAdd}`);

        attacker.hits += 1;
        attacker.score += pointsToAdd;
        
        console.log(`[EmojiBattleSession][DEBUG] After calculation - Hits: ${attacker.hits}, Score: ${attacker.score}`);
        
        if (emojiInfo?.effect) {
             console.log(`[EmojiBattleSession] Applying effect '${emojiInfo.effect}' to target ${data.target}`);
             if (emojiInfo.effect === 'freeze') {
                 target.state = 'frozen';
                 setTimeout(() => { if(target) target.state = null; }, 1500);
             } else if (emojiInfo.effect === 'slip') {
                 target.state = 'slip';
                 setTimeout(() => { if(target) target.state = null; }, 1000);
             }
        }

        const payload = {
            attacker: attackerId,
            target: data.target,
            emoji: data.emoji,
            hits: attacker.hits,
            score: attacker.score,
        };

        console.log(`[EmojiBattleSession][DEBUG] Emitting 'emoji_hit' with payload:`, JSON.stringify(payload));

        this.io.to(this.room).emit('emoji_hit', payload);

        if (attacker.hits >= HIT_TO_WIN) {
            this._gameOver(attackerId);
        }
    }

    handleEmojiMove(id, data) {
        if (!this.isRunning) return;
        const player = this.players.get(id);
        if (!player) return;
        
        player.x = Math.max(0, Math.min(FIELD_WIDTH, data.x));
        this.io.to(this.room).emit('emoji_move', { id, x: player.x });
    }

    _gameOver(winnerId) {
        if (!this.isRunning) return;
        console.log(`[EmojiBattleSession] _gameOver CALLED. Winner: ${winnerId}`);
        this.isRunning = false;

        const winnerData = this.players.get(winnerId);
        if (winnerData) {
            userPoints.set(winnerId, (userPoints.get(winnerId) || 0) + 100);
            recordWin(winnerId, winnerData.user);
        }

        for (const [pid, player] of this.players) {
            if (pid !== winnerId) {
                recordLoss(pid, player.user);
            }
        }

        this.io.to(this.room).emit('emoji_game_over', { winner: winnerId });

        console.log(`[EmojiBattleSession] Session for room ${this.room} is now in post-game state. Waiting for players to get ready for a new game.`);
    }

    destroy() {
        console.log(`[EmojiBattleSession] Session DESTROYED for room: ${this.room}.`);
        this.isRunning = false;
        this.players.clear();
    }
}

export { EmojiBattleSession };