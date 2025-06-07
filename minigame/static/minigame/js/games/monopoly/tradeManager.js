// File: /static/minigame/js/games/monopoly/tradeManager.js
// 역할: 플레이어간 부동산/카드/현금 거래

export default class TradeManager {
  // MVP: alert/prompt로 양방향 거래
  static proposeTrade(fromPlayer, toPlayer, offerPropertyIds, requestPropertyIds, offerCash, requestCash, board) {
    // 실제 UI/로직에선 선택 패널로 입력 받음
    // 여기서는 간단한 콘솔/프롬프트
    if (confirm(`${toPlayer.name}, 거래 제안: 
${fromPlayer.name} → 부동산(${offerPropertyIds.join(',')})/현금 ${offerCash}원 ↔ 
${toPlayer.name} → 부동산(${requestPropertyIds.join(',')})/현금 ${requestCash}원
수락하시겠습니까?`)) {
      // 소유권 교환
      offerPropertyIds.forEach(id => {
        board.getTile(id).owner = toPlayer.id;
        fromPlayer.properties = fromPlayer.properties.filter(pid => pid !== id);
        toPlayer.properties.push(id);
      });
      requestPropertyIds.forEach(id => {
        board.getTile(id).owner = fromPlayer.id;
        toPlayer.properties = toPlayer.properties.filter(pid => pid !== id);
        fromPlayer.properties.push(id);
      });
      // 현금 교환
      fromPlayer.cash -= offerCash;
      toPlayer.cash += offerCash;
      toPlayer.cash -= requestCash;
      fromPlayer.cash += requestCash;
      alert('거래 완료!');
    } else {
      alert('거래 거부됨');
    }
  }
}
