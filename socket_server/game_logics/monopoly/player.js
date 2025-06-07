// File: /static/minigame/js/games/monopoly/player.js
// 역할: 플레이어(말) 상태/자산/위치/카드/파산 등 관리

export default class Player {
  constructor(id, name, startPos = 0) {
    this.id = id;
    this.name = name;
    this.position = startPos;
    this.cash = 1500;
    this.properties = [];
    this.cards = [];
    this.inJail = false;
    this.jailTurns = 0;
    this.bankrupt = false;
  }

  move(steps, boardSize = 40) {
    this.position = (this.position + steps) % boardSize;
  }
}
