const games = new Map();

/**
 * 새 게임을 시작합니다.
 * @param {string} roomId - 방 ID
 * @param {string} playerId - 플레이어 ID
 */
function startGame(roomId, playerId) {
  if (!games.has(roomId)) {
    games.set(roomId, {
      players: [{ id: playerId, position: 0, cash: 1500, properties: [] }],
      currentTurn: 0
    });
  } else {
    games.get(roomId).players.push({ id: playerId, position: 0, cash: 1500, properties: [] });
  }
}

/**
 * 주사위 결과를 처리합니다.
 * @param {string} roomId - 방 ID
 * @param {string} playerId - 플레이어 ID
 * @param {number} result - 주사위 결과
 */
function updatePlayer(roomId, playerId, result) {
  const game = games.get(roomId);
  const player = game.players.find(p => p.id === playerId);
  if (player) {
    player.position = (player.position + result) % 40;
  }
}

export { startGame, updatePlayer };