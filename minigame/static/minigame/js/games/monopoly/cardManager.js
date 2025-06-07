// File: /static/minigame/js/games/monopoly/cardManager.js
// 역할: 카드덱 생성, 카드효과 실행

export default class CardManager {
  static chanceDeck = [
    { text: "출발로 이동 후 월급 받기", action: (gm, p) => { p.position = 0; p.cash += 200; } },
    { text: "감옥으로 이동", action: (gm, p) => { p.position = 10; p.inJail = true; } },
    { text: "수리비 100원 납부", action: (gm, p) => { p.cash -= 100; } },
    { text: "다른 플레이어에게 50원씩 지급", action: (gm, p, ps) => { ps.filter(x=>x!==p).forEach(x=>{ p.cash-=50; x.cash+=50; }); } },
    { text: "은행에서 150원 받기", action: (gm, p) => { p.cash += 150; } },
    // ...필요한 만큼 추가
  ];

  static communityDeck = [
    { text: "병원비 100원 납부", action: (gm, p) => { p.cash -= 100; } },
    { text: "출발로 이동 후 월급 받기", action: (gm, p) => { p.position = 0; p.cash += 200; } },
    { text: "감옥에서 탈출 카드(미구현)", action: (gm, p) => { /* TODO */ } },
    { text: "은행에서 200원 받기", action: (gm, p) => { p.cash += 200; } },
    // ...필요한 만큼 추가
  ];

  static drawCard(type, gameManager, player, players) {
    const deck = (type === 'chance') ? this.chanceDeck : this.communityDeck;
    const card = deck[Math.floor(Math.random() * deck.length)];
    alert(`[${type === 'chance' ? '찬스' : '공공기금'}]\n${card.text}`);
    card.action(gameManager, player, players);
  }
}
