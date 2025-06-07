const socket = io('http://192.168.31.199:3000/monopoly', // 배포시 실제 IP로

socket.on('connect', () => {
  console.log('✅ 서버와 연결됨!');
  socket.emit('join_game', { username: window.username });
});

socket.on('game_event', (data) => {
  console.log('게임 이벤트 수신:', data);
  // 게임 내에서 처리
});

// 게임 중 이벤트 전송 예시
function sendScore(score) {
  socket.emit('score_update', { username: window.username, score });
}
