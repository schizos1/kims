// socket_server/game_handlers/emoji_battle_game_handler.js

import { EmojiBattleSession } from '../game_logics/emoji_battle/multi_game_session.js';

const activeSessions = new Map();
console.log('[EmojiBattleHandler] Module loaded. Initial activeSessions state:', activeSessions);

export default function initializeEmojiBattleHandler(io, socket) {
    console.log(`[EmojiBattleHandler] Initializing event handlers for new socket connection: ${socket.id} on namespace: ${socket.nsp.name}`);

    // 모든 이벤트 로그
    socket.onAny((event, ...args) => {
        console.log(`[EmojiBattleHandler][${socket.id}] Received event: <<${event}>> with data:`, args);
    });

    // 방 참가
    socket.on('join_emoji_room', ({ room, userData }) => {
        console.log(`[EmojiBattleHandler] ${socket.id} joins '${room}'`);
        if (!activeSessions.has(room)) {
            activeSessions.set(room, new EmojiBattleSession(io, room));
            console.log(`[EmojiBattleHandler] New session created for '${room}'`);
        }
        const session = activeSessions.get(room);
        session.addPlayer(socket, userData);
    });

    // 무기 발사(애니 참고용)
    socket.on('emoji_throw', (data) => {
        for (const session of activeSessions.values()) {
            if (session.hasPlayer(socket.id)) {
                session.handleEmojiThrow(socket.id, data);
                break;
            }
        }
    });

    // 플레이어 이동
    socket.on('emoji_move', (data) => {
        for (const session of activeSessions.values()) {
            if (session.hasPlayer(socket.id)) {
                session.handleEmojiMove(socket.id, data);
                break;
            }
        }
    });

    // 스킬샷 명중 시도: **핵심!**
    socket.on('player_hit_target', (data) => {
        for (const session of activeSessions.values()) {
            if (session.hasPlayer(socket.id)) {
                session.handlePlayerHitTarget(socket.id, data); // 아래 별도 설명
                break;
            }
        }
    });

    // 예상치 못한 명중 시도 방지
    socket.on('emoji_hit', (data) => {
        console.warn(`[EmojiBattleHandler][${socket.id}] Received 'emoji_hit' event directly from client. Ignored for security. Data:`, data);
    });

    // 연결 종료
    socket.on('disconnect', () => {
        for (const [roomName, session] of activeSessions.entries()) {
            if (session.hasPlayer(socket.id)) {
                session.removePlayer(socket.id);
                if (session.isEmpty()) {
                    activeSessions.delete(roomName);
                    console.log(`[EmojiBattleHandler] Session '${roomName}' deleted (empty)`);
                }
                break;
            }
        }
    });
}
