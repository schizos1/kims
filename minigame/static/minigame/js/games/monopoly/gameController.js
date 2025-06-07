// File: /static/minigame/js/games/monopoly/gameController.js
// 역할: 게임 시작~종료까지 모든 턴/행동/이벤트를 순서대로 실행(테스트/디버그용)

import GameManager from './gameManager.js';
import BuildingManager from './buildingManager.js';
import MortgageManager from './mortgageManager.js';
import TradeManager from './tradeManager.js';
import PopupManager from './popupManager.js';

// (테스트용) 샘플 플레이어명
const playerNames = ['철수', '영희', '민수'];

class GameController {
  constructor() {
    this.gm = new GameManager(null, playerNames);
    this._setup();
  }

  _setup() {
    alert('서울판 모노폴리 시작!');
    this.nextStep();
  }

  nextStep() {
    const gm = this.gm;
    const player = gm.getCurrentPlayer();

    // 감옥 로직 (간단 처리)
    if (player.inJail) {
      if (player.jailTurns < 2) {
        player.jailTurns++;
        alert(`${player.name}는 감옥에 ${player.jailTurns}턴째!`);
        gm.nextTurn();
        return this.nextStep();
      } else {
        player.inJail = false;
        player.jailTurns = 0;
        player.cash -= 50;
        alert(`${player.name}가 3턴 만에 50원 내고 감옥에서 나옴!`);
      }
    }

    // 1. 주사위
    PopupManager.alert(`▶ [${player.name}]의 차례! (현금: ${player.cash}원)`);
    const dice = gm.rollDice();
    if (!dice) return;
    PopupManager.alert(`주사위: ${dice[0]}, ${dice[1]} (합: ${gm.dice.getSum()})`);

    // 2. 이동
    const pos = gm.movePlayer();
    PopupManager.alert(`이동 후 위치: ${pos} (${gm.board.getTile(pos).name})`);

    // 3. 칸 이벤트(구매/임대료/경매/세금/카드/감옥)
    gm.handleLanding(() => {
      // 4. 파산/탈락 체크
      gm.checkBankruptPlayers();

      // 5. 추가 행동(건설/매각/저당/거래)
      this.postTurnActions(player);

      // 6. 다음 턴 진행
      setTimeout(() => this.nextStep(), 1200);
    });
  }

  // 턴 종료 후 추가 행동(집 짓기, 매각, 저당, 거래 등)
  postTurnActions(player) {
    if (player.bankrupt) return;
    // 건설 예시(실제로는 UI에서 버튼으로 처리)
    const build = PopupManager.confirm(`[${player.name}] 집(호텔) 건설 시도?`);
    if (build) {
      const buildable = player.properties.map(id => this.gm.board.getTile(id)).filter(t => t.houseCount < 5);
      if (buildable.length) {
        const tileName = PopupManager.prompt(`건설할 부동산명? [${buildable.map(t=>t.name).join(', ')}]`, buildable[0].name);
        const tile = buildable.find(t => t.name === tileName);
        if (tile) BuildingManager.buildHouse(player, tile, this.gm.board);
      }
    }
    // 저당 예시
    const mortgage = PopupManager.confirm(`[${player.name}] 부동산 저당 시도?`);
    if (mortgage) {
      const mortgageable = player.properties.map(id => this.gm.board.getTile(id)).filter(t => !t.mortgaged && t.houseCount===0);
      if (mortgageable.length) {
        const tileName = PopupManager.prompt(`저당할 부동산명? [${mortgageable.map(t=>t.name).join(', ')}]`, mortgageable[0].name);
        const tile = mortgageable.find(t => t.name === tileName);
        if (tile) MortgageManager.mortgage(player, tile);
      }
    }
    // 거래 예시(최소화)
    const trade = PopupManager.confirm(`[${player.name}] 다른 플레이어와 거래 시도?`);
    if (trade) {
      const others = this.gm.players.filter(p => p.id !== player.id && !p.bankrupt);
      if (others.length) {
        const targetName = PopupManager.prompt(`거래 대상자 선택? [${others.map(o=>o.name).join(', ')}]`, others[0].name);
        const target = others.find(p => p.name === targetName);
        if (target) {
          const myProps = player.properties;
          const theirProps = target.properties;
          const offer = PopupManager.prompt('내가 줄 부동산 번호(,로 구분)', myProps.join(','));
          const req = PopupManager.prompt('상대에게 요청할 부동산 번호(,로 구분)', theirProps.join(','));
          const offerCash = Number(PopupManager.prompt('내가 줄 현금', '0'));
          const reqCash = Number(PopupManager.prompt('상대에게 요청할 현금', '0'));
          TradeManager.proposeTrade(
            player,
            target,
            offer ? offer.split(',').map(Number).filter(n=>!isNaN(n)) : [],
            req ? req.split(',').map(Number).filter(n=>!isNaN(n)) : [],
            offerCash, reqCash, this.gm.board
          );
        }
      }
    }
  }
}

window.onload = () => {
  new GameController();
};
