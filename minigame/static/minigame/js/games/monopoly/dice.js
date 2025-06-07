// /static/minigame/js/games/monopoly/dice.js

import Phaser from 'phaser';

// 주사위 결과(1~6) → 프레임 인덱스 매핑표
const diceFaceToFrame = {
  1: 64,
  2: 68,
  3: 128,
  4: 0,
  5: 76,
  6: 72
};

export class DiceScene extends Phaser.Scene {
  constructor() {
    super('DiceScene');
    this.diceSprite = null;
    this.resultValue = null; // 고정할 눈값(1~6)
  }

  preload() {
    this.load.spritesheet('dice', '/static/minigame/monopoly/assets/dice/dice.png', {
      frameWidth: 46,
      frameHeight: 46
    });
  }

  create() {
    this.diceSprite = this.add.sprite(60, 60, 'dice', diceFaceToFrame[1]); // 처음엔 1면
    this.anims.create({
      key: 'dice_roll',
      frames: this.anims.generateFrameNumbers('dice', { start: 0, end: 143 }),
      frameRate: 40,
      repeat: 0
    });

    // 애니메이션이 끝나면 resultValue에 맞는 프레임으로 고정
    this.diceSprite.on('animationcomplete', () => {
      if (this.resultValue) {
        this.diceSprite.setFrame(diceFaceToFrame[this.resultValue]);
        this.resultValue = null;
      }
    });
  }

  /** 주사위 굴리기 (결과값: 1~6 입력) */
  roll(resultValue = 1) {
    this.resultValue = resultValue;
    this.diceSprite.play('dice_roll');
  }

  /** 강제로 원하는 면으로 고정하고 싶을 때 */
  setFace(face) {
    this.resultValue = null;
    this.diceSprite.setFrame(diceFaceToFrame[face]);
  }
}
