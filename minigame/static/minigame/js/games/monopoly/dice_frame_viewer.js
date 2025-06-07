import Phaser from 'phaser';

const config = {
  type: Phaser.AUTO,
  width: 300,
  height: 350,
  parent: 'dice-frame-viewer',
  backgroundColor: '#eee',
  scene: {
    preload,
    create,
  },
};

let diceSprite, frameText;
let curFrame = 0;
const totalFrames = 144; // 16x9 시트

function preload() {
  this.load.spritesheet('dice', '/static/minigame/monopoly/assets/dice/dice.png', {
    frameWidth: 46,
    frameHeight: 46,
  });
}

function create() {
  diceSprite = this.add.sprite(150, 150, 'dice', curFrame).setScale(3.5); // 훨씬 크게
  frameText = this.add.text(25, 260, `Frame: ${curFrame}`, {
    font: '32px Arial',
    fill: '#222',
  });

  // 프레임 갱신 함수
  function updateFrame(n) {
    curFrame = (n + totalFrames) % totalFrames;
    diceSprite.setFrame(curFrame);
    frameText.setText(`Frame: ${curFrame}`);
  }

  // window 전역 키 이벤트(씬 포커스 이슈 우회)
  window.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') updateFrame(curFrame - 1);
    if (e.key === 'ArrowRight') updateFrame(curFrame + 1);
    if (e.key === 'ArrowUp') updateFrame(curFrame - 16);
    if (e.key === 'ArrowDown') updateFrame(curFrame + 16);
  });

  // 마우스 휠도 지원
  window.addEventListener('wheel', (e) => {
    if (e.deltaY > 0) updateFrame(curFrame + 1);
    if (e.deltaY < 0) updateFrame(curFrame - 1);
  });
}

// Phaser 인스턴스는 window.onload 필요 없이 바로 생성
new Phaser.Game(config);
