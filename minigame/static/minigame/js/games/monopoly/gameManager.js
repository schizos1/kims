// File: /static/minigame/js/games/monopoly/gameManager.js
// 역할: 게임 전체 상태/플로우/이벤트 관리

import Board from './board.js';
import Player from './player.js';
import Dice from './dice.js';
import PurchaseManager from './purchaseManager.js';
import RentManager from './rentManager.js';
import AuctionManager from './auctionManager.js';
import CardManager from './cardManager.js';

export default class GameManager {
  constructor(scene, playerNames) {
    this.scene = scene;
    this.board = new Board(scene);
    this.players = playerNames.map((name, idx) => new Player(idx, name));
    this.dice = new Dice();
    this.currentTurn = 0;
    this.phase = 'roll';
  }

  getCurrentPlayer() {
    return this.players[this.currentTurn];
  }

  nextTurn() {
    this.currentTurn = (this.currentTurn + 1) % this.players.length;
    this.phase = 'roll';
  }

  rollDice() {
    if (this.phase !== 'roll') return null;
    const result = this.dice.roll();
    this.phase = 'move';
    return result;
  }

  movePlayer() {
    if (this.phase !== 'move') return null;
    const player = this.getCurrentPlayer();
    const steps = this.dice.getSum();
    player.move(steps, this.board.tiles.length);
    this.phase = 'resolve';
    return player.position;
  }

  handleLanding(callback = () => {}) {
  const player = this.getCurrentPlayer();
  const tile = this.board.getTile(player.position);

  switch(tile.type) {
    case 'property':
    case 'railroad':
    case 'utility':
      if (!tile.owner) {
        PurchaseManager.promptBuy(player, tile, (buy) => {
          if (buy) {
            PurchaseManager.buyTile(player, tile);
            this.phase = 'end';
            callback();
          } else {
            // **경매로 분기**
            AuctionManager.startAuction(this.players, tile, () => {
              this.phase = 'end';
              callback();
            });
          }
        });
      } else if (tile.owner !== player.id) {
        RentManager.payRent(player, tile, this.players);
        this.phase = 'end';
        callback();
      } else {
        this.phase = 'end';
        callback();
      }
      break;
    case 'tax':
      player.cash -= tile.price;
      alert(`${player.name} 세금 ${tile.price}원 납부!`);
      this.phase = 'end';
      callback();
      break;
    case 'community':
      CardManager.drawCard('community', this, player, this.players);
      this.phase = 'end';
      callback();
      break;
    case 'chance':
      CardManager.drawCard('chance', this, player, this.players);
      this.phase = 'end';
      callback();
      break;
    case 'go_to_jail':
      alert(`${player.name} 감옥으로!`);
      player.position = 10;
      player.inJail = true;
      player.jailTurns = 0;
      this.phase = 'end';
      callback();
      break;
    default:
      this.phase = 'end';
      callback();
      break;
    }
  }

  endPhase() {
    this.phase = 'roll';
    this.nextTurn();
  }
}
checkBankruptPlayers() {
  this.players.forEach(p => {
    if (p.cash < 0 && !p.bankrupt) {
      p.bankrupt = true;
      // 부동산 모두 은행/채권자에게 넘기기
      p.properties.forEach(id => {
        const t = this.board.getTile(id);
        t.owner = null; // 경매나 다음 주인에 이전
      });
      p.properties = [];
      alert(`${p.name} 파산 및 탈락!`);
    }
  });
  // 남은 플레이어 1명이면 우승
  const alive = this.players.filter(p => !p.bankrupt);
  if (alive.length === 1) {
    alert(`${alive[0].name} 우승!`);
    // 게임종료
  }
}