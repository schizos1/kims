// /home/schizos/study_site/socket_server/game_logics/monopoly/game.js

const games = new Map();

/**
 * 방에 플레이어 입장 (없으면 새로 만들고, 있으면 중복 추가X)
 */
function startGame(roomId, playerId) {
  if (!games.has(roomId)) {
    games.set(roomId, {
      players: [{ id: playerId, position: 0, cash: 1500, properties: [], bankrupt: false }],
      currentTurn: 0,
      turnOrder: [playerId],
      lastAction: null,
    });
  } else {
    const game = games.get(roomId);
    if (!game.players.some(p => p.id === playerId)) {
      game.players.push({ id: playerId, position: 0, cash: 1500, properties: [], bankrupt: false });
      game.turnOrder.push(playerId);
    }
  }
}

/**
 * 행동 처리 (이동/구매/임대료/턴종료 등)
 */
function handleAction(roomId, playerId, action) {
  const game = games.get(roomId);
  if (!game) return { success: false, error: '게임 없음' };
  if (game.turnOrder.length === 0) return { success: false, error: '플레이어 없음' };

  // 현재 턴 체크
  if (game.turnOrder[game.currentTurn] !== playerId) {
    return { success: false, error: '당신의 턴이 아닙니다' };
  }

  const player = game.players.find(p => p.id === playerId);
  if (!player) return { success: false, error: '플레이어 정보 없음' };

  if (action.type === 'roll') {
    // 주사위 결과
    const steps = Math.floor(Math.random() * 6) + 1;
    player.position = (player.position + steps) % 40;
    game.lastAction = { playerId, type: 'roll', steps, position: player.position };
    // (이동 후 구매/임대료/이벤트는 프론트에서 buy 등 emit로 분기)
    return { success: true, state: game };
  }

  if (action.type === 'buy') {
    // 현재 위치의 땅 구매 (예시: 가격 100, 실제로는 타일 참조)
    const price = 100;
    if (player.cash >= price) {
      player.cash -= price;
      player.properties.push(player.position);
      game.lastAction = { playerId, type: 'buy', pos: player.position };
      game.currentTurn = (game.currentTurn + 1) % game.turnOrder.length;
      return { success: true, state: game };
    } else {
      return { success: false, error: '현금 부족' };
    }
  }

  if (action.type === 'end') {
    game.currentTurn = (game.currentTurn + 1) % game.turnOrder.length;
    game.lastAction = { playerId, type: 'end' };
    return { success: true, state: game };
  }

  // ... 경매, 임대료, 건설, 저당 등 차례대로 추가
  return { success: false, error: '지원하지 않는 행동' };
}

/**
 * 현재 턴의 소켓 id 반환
 */
function getCurrentTurn(roomId) {
  const game = games.get(roomId);
  return game ? game.turnOrder[game.currentTurn] : null;
}

/**
 * 플레이어 퇴장/연결 해제
 */
function removePlayer(roomId, playerId) {
  const game = games.get(roomId);
  if (game) {
    // 턴 순서에서 제거
    const playerIdx = game.turnOrder.indexOf(playerId);
    if (playerIdx !== -1) {
      game.turnOrder.splice(playerIdx, 1);
      // 현재 턴이 마지막을 벗어나면 0으로
      if (game.currentTurn >= game.turnOrder.length) {
        game.currentTurn = 0;
      }
    }
    // 플레이어 목록에서도 제거
    game.players = game.players.filter(p => p.id !== playerId);
    // 모두 나가면 게임 삭제 (선택)
    if (game.players.length === 0) {
      games.delete(roomId);
    }
  }
}

/**
 * 플레이어 리스트 반환
 */
function getPlayerList(roomId) {
  const game = games.get(roomId);
  return game ? game.players.map(p => ({ playerId: p.id, position: p.position })) : [];
}

export {
  startGame,
  handleAction,
  getCurrentTurn,
  removePlayer,
  getPlayerList,
  games,
};
