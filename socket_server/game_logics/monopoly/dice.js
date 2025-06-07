// File: /static/minigame/js/games/monopoly/dice.js
// 역할: 주사위(2개) 굴림 및 결과 반환

export default class Dice {
  constructor() {
    this.result = [0, 0];
  }

  roll() {
    this.result = [
      Math.floor(Math.random() * 6) + 1,
      Math.floor(Math.random() * 6) + 1
    ];
    return this.result;
  }

  getSum() {
    return this.result[0] + this.result[1];
  }

  isDouble() {
    return this.result[0] === this.result[1];
  }
}
