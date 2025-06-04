// socket_server/game_handlers/eat_food_game_handler.js
// 'eat_food' 게임의 Socket.IO 이벤트 처리 및 세션 관리

import SingleGameSession from '../game_logics/eat_food/single_game_session.js';
import MultiGameSession from '../game_logics/eat_food/multi_game_session.js';

// 이 핸들러 범위 내에서 활성 세션 관리
const activeSingleSessions = new Map();
const activeMultiSessions = new Map();

export default function initializeEatFoodGameHandler(io, socket) {
    console.log(`[EatFoodHandler] Initializing for socket ${socket.id}`);

    // --- 싱글플레이어 게임 관련 이벤트 핸들러 ---
    socket.on('join_single_game', (userData) => {
        console.log(`[EatFoodHandler] Client ${socket.id} requested 'join_single_game'`, userData);
        if (activeSingleSessions.has(socket.id)) {
            activeSingleSessions.get(socket.id).destroy();
            activeSingleSessions.delete(socket.id);
        }
        try {
            const session = new SingleGameSession(socket, userData);
            activeSingleSessions.set(socket.id, session);
        } catch (error) {
            console.error(`[EatFoodHandler] Error creating SingleGameSession for ${socket.id}:`, error);
            socket.emit('server_error', { message: '싱글플레이어 게임 세션 생성 실패.' });
        }
    });

    socket.on('player_move_request', (moveData) => { // 싱글플레이어용
        const session = activeSingleSessions.get(socket.id);
        if (session) {
            session.handlePlayerMove(moveData);
        } else {
            // console.warn(`[EatFoodHandler] 'player_move_request' from ${socket.id} - no active single session.`);
        }
    });

    socket.on('player_eat_attempt', (eatData) => { // 싱글플레이어용
        const session = activeSingleSessions.get(socket.id);
        if (session) {
            session.handlePlayerEatAttempt(eatData);
        } else {
            // console.warn(`[EatFoodHandler] 'player_eat_attempt' from ${socket.id} - no active single session.`);
        }
    });

    // --- 멀티플레이어 게임 관련 이벤트 핸들러 ---
    socket.on('join_multi_room', ({ room, userData }) => {
        if (!activeMultiSessions.has(room)) {
            activeMultiSessions.set(room, new MultiGameSession(io, room));
        }
        activeMultiSessions.get(room).addPlayer(socket, userData);
    });

    socket.on('multi_move', (data) => {
        for (const session of activeMultiSessions.values()) {
            if (session.hasPlayer(socket.id)) {
                session.handlePlayerMove(socket.id, data);
                break;
            }
        }
    });

    socket.on('multi_eat_attempt', (data) => {
        for (const session of activeMultiSessions.values()) {
            if (session.hasPlayer(socket.id)) {
                session.handlePlayerEatAttempt(socket.id, data);
                break;
            }
        }
    });


    // 이 핸들러에 연결된 소켓이 끊어졌을 때 정리 로직
    // (server.js의 메인 disconnect 핸들러에서도 호출될 수 있지만, 여기서 게임 특화 정리 수행)
    const originalDisconnect = socket.listeners('disconnect')[0]; // 기존 disconnect 리스너가 있다면 가져오기
    socket.removeAllListeners('disconnect'); // 기존 리스너 제거 (중복 방지)

    socket.on('disconnect', (reason) => {
        console.log(`[EatFoodHandler] Socket ${socket.id} disconnected. Reason: ${reason}`);
        const singleSession = activeSingleSessions.get(socket.id);
        if (singleSession) {
            singleSession.destroy();
            activeSingleSessions.delete(socket.id);
            console.log(`[EatFoodHandler] SingleGameSession destroyed for ${socket.id}. Total single sessions: ${activeSingleSessions.size}`);
        }
        for (const [room, session] of activeMultiSessions) {
            if (session.hasPlayer(socket.id)) {
                session.removePlayer(socket.id);
                if (session.isEmpty()) activeMultiSessions.delete(room);
                break;
            }
        }

        // 원래의 disconnect 리스너가 있었다면 다시 호출 (다른 일반적인 정리 작업 수행 가능)
        if (originalDisconnect) {
            originalDisconnect.call(socket, reason);
        }
    });
}