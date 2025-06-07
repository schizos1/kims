// File: /static/minigame/js/games/monopoly/socket.js

import { io } from 'socket.io-client';

export function initSocket(roomId) {
  const socket = io('http://192.168.31.199:3000/monopoly');
  socket.on('connect', () => {
    socket.emit('join_room', roomId);
  });
  return socket;
}
