/**
 * Socket.IO 클라이언트를 초기화하고 이벤트를 설정합니다.
 * @param {string} roomId - 게임 방 ID
 * @returns {Socket} 초기화된 Socket.IO 클라이언트
 */
import { io } from 'socket.io-client';

export function initSocket(roomId) {
  // Socket.IO 서버에 연결 (모노폴리 네임스페이스)
  const socket = io('http://192.168.31.199:3000/monopoly', {
    reconnection: true,
    reconnectionAttempts: 5
  });

  socket.on('connect', () => {
    console.log('Connected to socket server:', socket.id);
    socket.emit('join_room', roomId);
  });

  socket.on('connect_error', (error) => {
    console.error('Socket connection error:', error);
  });

  socket.on('player_joined', (data) => {
    console.log('Player joined:', data.playerId);
  });

  return socket;
}