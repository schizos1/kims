// socket_server/game_handlers/fishing_game_handler.js
// Fishing game Socket.IO event handler
import SingleFishingSession from '../game_logics/fishing/single_game_session.js';
import MultiFishingSession from '../game_logics/fishing/multi_game_session.js';

const activeSingleSessions = new Map();
const activeMultiSessions = new Map();

export default function initializeFishingGameHandler(io, socket) {
    socket.on('join_single_fishing', (userData) => {
        if (activeSingleSessions.has(socket.id)) {
            activeSingleSessions.get(socket.id).destroy();
            activeSingleSessions.delete(socket.id);
        }
        const session = new SingleFishingSession(socket, userData);
        activeSingleSessions.set(socket.id, session);
    });

    socket.on('join_fishing_room', ({ room, userData }) => {
        if (!activeMultiSessions.has(room)) {
            activeMultiSessions.set(room, new MultiFishingSession(io, room));
        }
        const session = activeMultiSessions.get(room);
        session.addPlayer(socket, userData);
    });

    socket.on('fishing_move', (data) => {
        const session = activeSingleSessions.get(socket.id) || [...activeMultiSessions.values()].find(s => s.hasPlayer(socket.id));
        if (session) session.handlePlayerMove(socket.id, data);
    });

    socket.on('fishing_action', (data) => {
        const session = activeSingleSessions.get(socket.id) || [...activeMultiSessions.values()].find(s => s.hasPlayer(socket.id));
        if (session) session.handlePlayerAction(socket.id, data);
    });

    socket.on('disconnect', () => {
        if (activeSingleSessions.has(socket.id)) {
            activeSingleSessions.get(socket.id).destroy();
            activeSingleSessions.delete(socket.id);
        }
        for (const [room, session] of activeMultiSessions) {
            if (session.hasPlayer(socket.id)) {
                session.removePlayer(socket.id);
                if (session.isEmpty()) activeMultiSessions.delete(room);
                break;
            }
        }
    });
}
