// File: /static/minigame/js/games/monopoly/buildingManager.js
// 역할: 주택/호텔 건설, 매각, 균등건설 등 규칙 처리

export default class BuildingManager {
  // 집 짓기 (도시 전체 색깔 독점 후, 현금 확인 등 검증)
  static buildHouse(player, tile, board) {
    if (tile.owner !== player.id) {
      alert('소유한 부동산만 건설할 수 있습니다.');
      return;
    }
    // 색깔 독점 확인
    const colorTiles = board.tiles.filter(t => t.color === tile.color && t.type === 'property');
    const isMonopoly = colorTiles.every(t => t.owner === player.id);
    if (!isMonopoly) {
      alert('해당 색상군을 모두 소유해야 건설 가능!');
      return;
    }
    if (tile.houseCount >= 5) {
      alert('호텔(5)까지 이미 건설 완료!');
      return;
    }
    const cost = tile.price * 0.5; // 모노폴리 표준(집 1채: 땅값의 절반)
    if (player.cash < cost) {
      alert('현금 부족!');
      return;
    }
    player.cash -= cost;
    tile.houseCount += 1;
    alert(`${tile.name}에 집${tile.houseCount <= 4 ? tile.houseCount + '채' : '/호텔'} 건설!`);
  }

  // 집/호텔 매각
  static sellHouse(player, tile) {
    if (tile.owner !== player.id || tile.houseCount === 0) {
      alert('건설된 집/호텔 없음');
      return;
    }
    tile.houseCount -= 1;
    player.cash += tile.price * 0.5 * 0.5; // 건설비의 50%에 매각
    alert(`${tile.name}에서 집/호텔 1개 매각!`);
  }
}
