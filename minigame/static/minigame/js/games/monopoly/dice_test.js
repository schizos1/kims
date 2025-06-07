// /static/minigame/js/games/monopoly/dice.js

export default class Dice {
  constructor(scene, x, y) {
    this.scene = scene;
    // Phaser에서 'dice' 스프라이트 시트는 main.js나 scene에서 preload() 해야 함!
    this.sprite = scene.add.sprite(x, y, 'dice', 0);

    scene.anims.create({
      key: 'dice_roll',
      frames: scene.anims.generateFrameNumbers('dice', { start: 0, end: 143 }),
      frameRate: 40,
      repeat: 0
    });
  }

  roll() {
    // 주사위 애니메이션 실행
    this.sprite.play('dice_roll');
    // 실제로는 애니메이션이 끝나고 원하는 프레임(1~6면)을 setFrame으로 고정해줘야 함!
  }

  showResult(faceNum) {
    // 예시: faceNum=4라면 4번 면이 위로 오는 프레임 인덱스를 setFrame()
    // 일단 임의로 7번 프레임을 1로, 23번을 2로 가정
    const mapping = { 1: 7, 2: 23, 3: 41, 4: 62, 5: 91, 6: 110 };
    this.sprite.setFrame(mapping[faceNum]);
  }
}
