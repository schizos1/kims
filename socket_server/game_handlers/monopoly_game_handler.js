// /home/schizos/study_site/socket_server/game_handlers/monopoly_game_handler.js

import { startGame, handleAction, getCurrentTurn, removePlayer, getPlayerList } from '../game_logics/monopoly/game.js';

function monopolyGameHandler(namespace, socket) {
  socket.on('join_room', (roomId) => {
    console.log(`[Monopoly] join_room: ${roomId} / ${socket.id}`);
    socket.join(roomId);
    startGame(roomId, socket.id);
    const playerList = getPlayerList(roomId);
    namespace.to(roomId).emit('player_list', playerList);
    namespace.to(roomId).emit('turn_update', { currentTurn: getCurrentTurn(roomId) });
  });

  socket.on('action', (roomId, action) => {
    console.log(`[Monopoly] action from ${socket.id} in ${roomId}:`, action); // 👈 로그 추가
    const res = handleAction(roomId, socket.id, action);
    if (res.success) {
      namespace.to(roomId).emit('game_update', res.state);
      namespace.to(roomId).emit('turn_update', { currentTurn: getCurrentTurn(roomId) });
    } else {
      socket.emit('action_error', { message: res.error || '행동 불가' });
    }
  });

  socket.on('disconnect', () => {
    console.log(`[Monopoly] disconnect: ${socket.id}`);
    removePlayer('monopoly_room', socket.id);
    namespace.to('monopoly_room').emit('player_left', { playerId: socket.id });
    namespace.to('monopoly_room').emit('turn_update', { currentTurn: getCurrentTurn('monopoly_room') });
  });
}

export default monopolyGameHandler;
