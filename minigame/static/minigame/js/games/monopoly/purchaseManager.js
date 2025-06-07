// File: /static/minigame/js/games/monopoly/purchaseManager.js
// 역할: 구매/매입 등 처리

export default class PurchaseManager {
  static promptBuy(player, tile, callback) {
    const buy = confirm(`${player.name}, ${tile.name}을(를) ${tile.price}원에 구매하시겠습니까?`);
    callback(buy);
  }

  static buyTile(player, tile) {
    if (player.cash >= tile.price) {
      player.cash -= tile.price;
      tile.owner = player.id;
      player.properties.push(tile.id);
      alert(`${player.name}이(가) ${tile.name}을(를) 구매했습니다!`);
    } else {
      alert(`현금 부족!`);
    }
  }
}
