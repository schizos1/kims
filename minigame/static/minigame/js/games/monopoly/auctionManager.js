// File: /static/minigame/js/games/monopoly/auctionManager.js
// 역할: 경매(참여자 입력 받아 낙찰자 결정)

export default class AuctionManager {
  static startAuction(players, tile, callback) {
    // MVP: 모든 플레이어 콘솔/프롬프트로 입찰, 가장 높은 금액으로 낙찰
    let maxBid = 0, winner = null;
    players.forEach(player => {
      if (player.bankrupt) return;
      const bid = prompt(`${player.name}, ${tile.name} 경매! 입찰가(현금: ${player.cash}) 입력, 패스는 0 입력`, '0');
      const bidValue = parseInt(bid, 10);
      if (bidValue > maxBid && bidValue <= player.cash) {
        maxBid = bidValue;
        winner = player;
      }
    });
    if (winner) {
      winner.cash -= maxBid;
      tile.owner = winner.id;
      winner.properties.push(tile.id);
      alert(`${winner.name}님이 ${maxBid}원에 ${tile.name}을(를) 낙찰!`);
    } else {
      alert('낙찰자 없음(모두 패스)');
    }
    callback && callback();
  }
}
