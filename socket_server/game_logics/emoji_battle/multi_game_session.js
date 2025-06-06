// socket_server/game_logics/emoji_battle/multi_game_session.js

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
        console.log(`[EmojiBattleSession] New session CREATED for room: ${room}`); // 세션 생성 로그
    }

    _ensurePoints(id) {
        if (!userPoints.has(id)) userPoints.set(id, 1000);
    }

    addPlayer(socket, userData) {
        console.log(`[EmojiBattleSession] addPlayer CALLED - Socket ID: ${socket.id}, UserData: ${JSON.stringify(userData)}, Room: ${this.room}, Current players BEFORE add: ${this.players.size}`);
        socket.join(this.room);
        this._ensurePoints(socket.id);
        userPoints.set(socket.id, userPoints.get(socket.id) - 50); // 참가비 등

        // 플레이어 x 위치 설정: 첫 플레이어는 왼쪽(20%), 두번째 플레이어는 오른쪽(80%)
        // this.players.size 를 players.set 이전에 참조하므로, 첫 플레이어는 size 0, 두번째는 size 1 기준으로 x 할당
        const playerX = this.players.size === 0 ? FIELD_WIDTH * 0.2 : FIELD_WIDTH * 0.8;

        this.players.set(socket.id, {
            socket,
            user: userData.user,
            emoji: userData.emoji, // ⭐️ 반드시 저장!
            hits: 0,
            x: playerX,
            score: 0,
            state: null
        });
        console.log(`[EmojiBattleSession] Player ${socket.id} ADDED to room ${this.room}. Player X: ${playerX}. Current players AFTER add: ${this.players.size}`);

        if (this.players.size === 2 && !this.isRunning) {
            console.log(`[EmojiBattleSession] Conditions MET for startGame in room ${this.room} (Players: ${this.players.size}, isRunning: ${this.isRunning}). Calling startGame().`);
            this.startGame();
        } else {
            console.log(`[EmojiBattleSession] Conditions NOT MET for startGame in room ${this.room}. Players: ${this.players.size}, isRunning: ${this.isRunning}`);
        }
    }

    hasPlayer(id) { return this.players.has(id); }

    removePlayer(id) {
        console.log(`[EmojiBattleSession] removePlayer CALLED for ID: ${id} in room ${this.room}. Current players BEFORE remove: ${this.players.size}`);
        const playerExists = this.players.has(id);
        this.players.delete(id);
        if (playerExists) {
            console.log(`[EmojiBattleSession] Player ${id} REMOVED from room ${this.room}. Current players AFTER remove: ${this.players.size}`);
            this.io.to(this.room).emit('emoji_player_left', { id });
            // 남은 플레이어가 있을 경우 게임을 중단하거나 대기 상태로 만들 수 있음 (여기서는 isRunning 플래그만 관리)
            if (this.players.size < 2 && this.isRunning) {
                console.log(`[EmojiBattleSession] Not enough players to continue game in room ${this.room}. Setting isRunning to false.`);
                this.isRunning = false; // 예: 게임 강제 종료 또는 일시정지
            }
        } else {
            console.log(`[EmojiBattleSession] Player ${id} NOT FOUND in room ${this.room} for removal.`);
        }
    }

    isEmpty() { return this.players.size === 0; }

    startGame() {
        console.log(`[EmojiBattleSession] startGame CALLED for room ${this.room}. Setting isRunning to true.`);
        this.isRunning = true;
        const playersData = [...this.players.entries()].map(([id, p]) => ({
            id,
            user: p.user,
            emoji: p.emoji, // ⭐️ 포함!
            x: p.x
        }));
        console.log(`[EmojiBattleSession] Emitting 'emoji_start' to room ${this.room} with players:`, JSON.stringify(playersData));
        this.io.to(this.room).emit('emoji_start', {
            players: playersData
        });
    }

    handleEmojiThrow(id, data) {
        if (!this.isRunning) {
            // console.log(`[EmojiBattleSession] handleEmojiThrow IGNORED in room ${this.room} - Game not running. Player: ${id}`);
            return;
        }
        // console.log(`[EmojiBattleSession] handleEmojiThrow from player ${id} in room ${this.room}:`, data);
        this.io.to(this.room).emit('emoji_thrown', { id, emoji: data.emoji });
    }

    handleEmojiHit(attackerId, data) {
        if (!this.isRunning) {
            // console.log(`[EmojiBattleSession] handleEmojiHit IGNORED in room ${this.room} - Game not running. Attacker: ${attackerId}`);
            return;
        }
        const attacker = this.players.get(attackerId);
        if (!attacker) {
            console.error(`[EmojiBattleSession] Attacker ${attackerId} NOT FOUND in room ${this.room} for handleEmojiHit.`);
            return;
        }
        // console.log(`[EmojiBattleSession] handleEmojiHit by attacker ${attackerId} in room ${this.room}:`, data);

        const emojiInfo = EMOJI_TYPES.find(e => e.emoji === data.emoji);
        const addScore = emojiInfo?.points || 100;
        attacker.hits += 1;
        attacker.score += addScore;

        // 상태효과
        if (emojiInfo?.effect === 'freeze') {
            attacker.state = 'frozen';
            setTimeout(() => { attacker.state = null; }, 1000);
        } else if (emojiInfo?.effect === 'slip') {
            attacker.state = 'slip';
            setTimeout(() => { attacker.state = null; }, 1000);
        } else {
            attacker.state = null; // 다른 효과가 없으면 null로 초기화
        }

        this.io.to(this.room).emit('emoji_hit', {
            attacker: attackerId,
            target: data.target,
            emoji: data.emoji,
            hits: attacker.hits,
            score: attacker.score,
            state: attacker.state,
        });

        // 승리조건 (동시 달성시 점수 비교)
        if (this.players.size === 2) { // 플레이어가 2명일 때만 승리 조건 체크
            const arr = [...this.players.values()]; // 값만 가져와서 사용
            const p1 = arr[0];
            const p2 = arr[1];
            // ID를 가져오기 위해 Map.entries() 사용 또는 players Map에서 ID를 따로 관리
            const p1Id = [...this.players.keys()][0];
            const p2Id = [...this.players.keys()][1];


            if (p1.hits >= HIT_TO_WIN || p2.hits >= HIT_TO_WIN) {
                let winnerId;
                if (p1.hits >= HIT_TO_WIN && p2.hits >= HIT_TO_WIN) { // 동시 달성
                    winnerId = p1.score >= p2.score ? p1Id : p2Id; // 점수 높은 쪽이 승리 (같으면 p1)
                } else { // 한 쪽만 달성
                    winnerId = p1.hits >= HIT_TO_WIN ? p1Id : p2Id;
                }
                console.log(`[EmojiBattleSession] Game Over condition met in room ${this.room}. Winner determined: ${winnerId}`);
                this._gameOver(winnerId);
            }
        }
    }

    handleEmojiMove(id, data) {
        if (!this.isRunning) {
            // console.log(`[EmojiBattleSession] handleEmojiMove IGNORED in room ${this.room} - Game not running. Player: ${id}`);
            return;
        }
        const player = this.players.get(id);
        if (!player) {
            console.error(`[EmojiBattleSession] Player ${id} NOT FOUND in room ${this.room} for handleEmojiMove.`);
            return;
        }
        const newX = Math.max(0, Math.min(FIELD_WIDTH, data.x)); // 필드 경계 체크
        player.x = newX;
        // console.log(`[EmojiBattleSession] handleEmojiMove from player ${id} in room ${this.room}. New X: ${player.x}`);
        this.io.to(this.room).emit('emoji_move', { id, x: player.x });
    }

    _gameOver(winnerId) {
        console.log(`[EmojiBattleSession] _gameOver CALLED for room ${this.room}. Winner: ${winnerId}. Setting isRunning to false.`);
        this.isRunning = false;
        // 승자 포인트 지급 및 전적 기록
        const winnerData = this.players.get(winnerId);
        if (winnerData) {
            userPoints.set(winnerId, (userPoints.get(winnerId) || 0) + 100); // 승리 포인트
            recordWin(winnerId, winnerData.user); // 승리 기록
        }

        for (const [pid,player] of this.players) {
            if (pid !== winnerId) {
                recordLoss(pid, player.user); // 패배 기록
            }
        }

        this.io.to(this.room).emit('emoji_game_over', {
            winner: winnerId,
            // points: userPoints.get(winnerId) // 필요시 승자 포인트 정보 전달
        });
        // 여기서 세션을 바로 삭제하거나 초기화할 수도 있음
        // 예: activeSessions.delete(this.room) 호출 주체는 핸들러
    }

    destroy() {
        console.log(`[EmojiBattleSession] Session DESTROYED for room: ${this.room}. Setting isRunning to false.`);
        this.isRunning = false;
        this.players.clear(); // 플레이어 정보 초기화
        // 이 외에 필요한 정리 작업 수행
    }
}

export { EmojiBattleSession };