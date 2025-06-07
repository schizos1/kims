// File: /static/minigame/js/games/monopoly/mortgageManager.js
// 역할: 저당 설정/해제(자금 조달/임대료 정지 등)

export default class MortgageManager {
  // 저당 설정
  static mortgage(player, tile) {
    if (tile.owner !== player.id || tile.mortgaged) {
      alert('저당 불가(이미 저당이거나 소유주 아님)');
      return;
    }
    if (tile.houseCount > 0) {
      alert('건물이 있으면 먼저 모두 매각해야 저당 가능!');
      return;
    }
    tile.mortgaged = true;
    player.cash += tile.price * 0.5; // 땅값의 50%
    alert(`${tile.name}을(를) 저당 설정! 현금 +${tile.price * 0.5}원`);
  }

  // 저당 해제
  static redeem(player, tile) {
    if (tile.owner !== player.id || !tile.mortgaged) {
      alert('저당 해제 불가(본인 소유가 아니거나 저당 상태 아님)');
      return;
    }
    const amount = tile.price * 0.55; // 원금+이자(5%)
    if (player.cash < amount) {
      alert('현금 부족! 저당 해제 불가');
      return;
    }
    tile.mortgaged = false;
    player.cash -= amount;
    alert(`${tile.name} 저당 해제! 현금 -${amount}원`);
  }
}
