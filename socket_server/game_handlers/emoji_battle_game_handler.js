// socket_server/game_handlers/emoji_battle_game_handler.js
// 이모지 배틀 게임의 Socket.IO 이벤트 처리

import EmojiBattleSession from '../game_logics/emoji_battle/multi_game_session.js';

const activeSessions = new Map();

export default function initializeEmojiBattleHandler(io, socket) {
    socket.on('join_emoji_room', ({ room, userData }) => {
        if (!activeSessions.has(room)) {
            activeSessions.set(room, new EmojiBattleSession(io, room));
        }
        activeSessions.get(room).addPlayer(socket, userData);
    });

    socket.on('emoji_throw', (data) => {
        for (const session of activeSessions.values()) {
            if (session.hasPlayer(socket.id)) {
                session.handleEmojiThrow(socket.id, data);
                break;
            }
        }
    });

    socket.on('emoji_hit', (data) => {
        for (const session of activeSessions.values()) {
            if (session.hasPlayer(socket.id)) {
                session.handleEmojiHit(socket.id, data);
                break;
            }
        }
    });

    socket.on('disconnect', () => {
        for (const [room, session] of activeSessions) {
            if (session.hasPlayer(socket.id)) {
                session.removePlayer(socket.id);
                if (session.isEmpty()) activeSessions.delete(room);
                break;
            }
        }
    });
}
