// /home/schizos/study_site/minigame/static/minigame/js/games/monopoly/main.js

import { initSocket } from './socket.js';

const roomId = 'monopoly_room'; // or 고유방번호

const socket = initSocket(roomId);

// 상태 저장
let gameState = null;

// 서버에서 전체 상태 받으면 화면 반영
socket.on('game_update', (state) => {
  gameState = state;
  renderGame(state);
});
socket.on('turn_update', ({ currentTurn }) => {
  document.getElementById('turnInfo').innerText = `현재 턴: ${currentTurn}`;
});
socket.on('action_error', ({ message }) => {
  alert(message);
});

// 버튼 연결
document.getElementById('rollBtn').onclick = () => {
  console.log('emit:', roomId, { type: 'roll' }); // ← 테스트용 출력
  socket.emit('action', roomId, { type: 'roll' });
};
document.getElementById('buyBtn').onclick = () => {
  socket.emit('action', roomId, { type: 'buy' });
};
document.getElementById('endBtn').onclick = () => {
  socket.emit('action', roomId, { type: 'end' });
};

// 화면 표시 예시
function renderGame(state) {
  // 예시: 플레이어 현황, 위치, 현금 표시
  document.getElementById('gameInfo').innerHTML =
    state.players.map(p =>
      `<div>${p.id} - 위치: ${p.position}, 현금: ${p.cash}, 소유: [${p.properties.join(', ')}]</div>`
    ).join('');
  // 추가로 보드, 내 소유, 최근 행동 등 표시 확장 가능
}
