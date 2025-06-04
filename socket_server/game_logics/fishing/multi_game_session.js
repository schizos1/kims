// socket_server/game_logics/fishing/multi_game_session.js
import * as config from './config.js';

class MultiFishingSession {
    constructor(io, room) {
        this.io = io;
        this.room = room;
        this.players = new Map();
        this.isRunning = false;
    }

    addPlayer(socket, userData) {
        socket.join(this.room);
        this.players.set(socket.id, { socket, user: userData.user });
        if (this.players.size === 2 && !this.isRunning) {
            this.startGame();
        }
    }

    hasPlayer(id) {
        return this.players.has(id);
    }

    removePlayer(id) {
        this.players.delete(id);
        this.io.to(this.room).emit('fishing_player_left', { id });
    }

    isEmpty() {
        return this.players.size === 0;
    }

    startGame() {
        this.isRunning = true;
        this.io.to(this.room).emit('fishing_start', { room: this.room });
    }

    handlePlayerMove(id, data) {
        if (!this.isRunning) return;
        this.io.to(this.room).emit('fishing_state', { id, x: data.x, y: data.y });
    }

    handlePlayerAction(id, data) {
        if (!this.isRunning) return;
        this.io.to(this.room).emit('fishing_action_result', { id, success: true });
    }
}

export default MultiFishingSession;
