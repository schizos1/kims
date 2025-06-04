// socket_server/game_logics/fishing/single_game_session.js
// Very simple placeholder logic for single player fishing game
import * as config from './config.js';

class SingleFishingSession {
    constructor(socket, userData) {
        this.socket = socket;
        this.userData = userData;
        this.isRunning = false;
        this._start();
    }

    _start() {
        this.isRunning = true;
        this.socket.emit('fishing_start', { user: this.userData.user });
    }

    handlePlayerMove(socketId, data) {
        // placeholder: echo movement
        this.socket.emit('fishing_state', { x: data.x, y: data.y });
    }

    handlePlayerAction(socketId, data) {
        // placeholder for cast/reel actions
        this.socket.emit('fishing_action_result', { success: true });
    }

    destroy() {
        this.isRunning = false;
    }
}

export default SingleFishingSession;
