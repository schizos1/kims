import { startGame, updatePlayer } from '../game_logics/monopoly/game.js';

/**
 * 모노폴리 게임의 Socket.IO 이벤트를 초기화합니다.
 * @param {Namespace} namespace - Socket.IO 네임스페이스
 * @param {Socket} socket - 클라이언트 소켓
 */
function initializeMonopolyGameHandler(namespace, socket) {
  console.log(`[MonopolyHandler] Initializing handler for socket ${socket.id}`);

  // 방 참가 이벤트
  socket.on('join_room', (roomId) => {
    socket.join(roomId);
    console.log(`[MonopolyHandler] ${socket.id} joined room ${roomId}`);
    startGame(roomId, socket.id);
    namespace.to(roomId).emit('player_joined', { playerId: socket.id, position: 0 });
  });

  // 주사위 굴리기 이벤트
  socket.on('roll_dice', (roomId, result) => {
    console.log(`[MonopolyHandler] ${socket.id} rolled dice: ${result} in room ${roomId}`);
    updatePlayer(roomId, socket.id, result);
    namespace.to(roomId).emit('dice_rolled', { playerId: socket.id, result });
  });

  // 연결 해제 이벤트
  socket.on('disconnect', () => {
    console.log(`[MonopolyHandler] ${socket.id} disconnected`);
  });
}

export default initializeMonopolyGameHandler;