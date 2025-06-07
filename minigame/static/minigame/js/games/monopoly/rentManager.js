// File: /static/minigame/js/games/monopoly/rentManager.js
// 역할: 임대료 징수

export default class RentManager {
  static payRent(player, tile, players) {
    const rent = Array.isArray(tile.rent) ? tile.rent[0] : tile.rent;
    const owner = players.find(p => p.id === tile.owner);
    if (!owner) return;
    if (player.cash >= rent) {
      player.cash -= rent;
      owner.cash += rent;
      alert(`${player.name} → ${owner.name}에게 임대료 ${rent}원 지급!`);
    } else {
      alert(`${player.name} 파산! (임대료 ${rent}원 지급 불가)`);
      // TODO: 파산 처리
    }
  }
}
