// /home/schizos/study_site/minigame/static/minigame/js/games/monopoly/main.js

import { initSocket } from './socket.js';
import Phaser from 'phaser';

// 1~6의 주사위 눈 : 프레임 매핑
const faceToFrame = {
  1: 64,
  2: 68,
  3: 128,
  4: 0,
  5: 76,
  6: 72
};

// ▶️ 1. Phaser DiceScene (주사위 2개 + 합산 표시 + 물리효과)
class DiceScene extends Phaser.Scene {
  constructor() {
    super('DiceScene');
    this.diceSprites = [];
    this.pendingResults = [];
    this.animLock = false;
    this.sumText = null;
  }

  preload() {
    this.load.spritesheet('dice', '/static/minigame/monopoly/assets/dice/dice.png', {
      frameWidth: 46,
      frameHeight: 46
    });
  }

  create() {
    // ▶️ 캔버스 넉넉하게!
    // 두 주사위 좌우로 충분히 벌리고, scale은 2.2~2.4
    this.diceSprites = [
      this.add.sprite(60, 64, 'dice', faceToFrame[1]).setScale(2.3),
      this.add.sprite(140, 68, 'dice', faceToFrame[1]).setScale(2.3)
    ];

    this.anims.create({
      key: 'dice_roll',
      frames: this.anims.generateFrameNumbers('dice', { start: 0, end: 143 }),
      frameRate: 40,
      repeat: 0
    });

    // ▶️ 합산 아래로
    this.sumText = this.add.text(100, 125, '', {
      font: 'bold 32px Arial',
      fill: '#1563ff',
      stroke: '#fff',
      strokeThickness: 5
    }).setOrigin(0.5);

    // ▶️ 애니 끝나면 살짝 튕김
    this.diceSprites.forEach((sprite, i) => {
      sprite.on('animationcomplete', () => {
        if (this.pendingResults[i] !== null) {
          sprite.anims.stop();
          sprite.setFrame(faceToFrame[this.pendingResults[i]]);
          this.tweens.add({
            targets: sprite,
            y: (i === 0 ? 64 : 68) - 8,
            scale: 2.1,
            duration: 100,
            yoyo: true,
            ease: 'Back.easeOut',
            onComplete: () => {
              sprite.y = i === 0 ? 64 : 68;
              sprite.scale = 2.3;
              if (
                this.pendingResults[0] !== null &&
                this.pendingResults[1] !== null &&
                this.diceSprites.every((s) => !s.anims.isPlaying)
              ) {
                this.showSum();
                this.animLock = false;
                this.pendingResults = [null, null];
              }
            }
          });
        }
      });
    });
  }

  showSum() {
    const [a, b] = this.pendingResults;
    const sum = (a || 0) + (b || 0);
    this.sumText.setText(sum > 0 ? `합: ${sum}` : '');
    this.sumText.setScale(1.6);
    this.tweens.add({
      targets: this.sumText,
      scale: 1.0,
      duration: 180,
      ease: 'Back.easeOut'
    });
  }

  roll([result1, result2]) {
    if (this.animLock) return;
    this.animLock = true;
    this.pendingResults = [result1 || 1, result2 || 1];
    this.sumText.setText('');
    // 공중에서 살짝 차이로 떨어지기
    this.diceSprites.forEach((sprite, i) => {
      sprite.y = i === 0 ? 14 : 22;
      sprite.scale = 1.4;
      sprite.alpha = 0.7;
      this.tweens.add({
        targets: sprite,
        y: i === 0 ? 64 : 68,
        scale: 2.3,
        alpha: 1,
        ease: 'Quad.easeOut',
        duration: 260 + i * 80,
        onComplete: () => {
          sprite.play('dice_roll');
        }
      });
    });
  }

  setFace([face1, face2]) {
    this.pendingResults = [null, null];
    this.diceSprites[0].setFrame(faceToFrame[face1]);
    this.diceSprites[1].setFrame(faceToFrame[face2]);
    this.sumText.setText(face1 + face2 > 0 ? `합: ${face1 + face2}` : '');
  }
}


// ▶️ 2. Phaser 인스턴스 (120x140, game-container div 필요)
const dicePhaserConfig = {
  type: Phaser.AUTO,
  width: 200,
  height: 160,
  parent: 'game-container',
  scene: [DiceScene],
  transparent: true
};
const diceGame = new Phaser.Game(dicePhaserConfig);
let diceScene;
diceGame.events.on('ready', () => {
  diceScene = diceGame.scene.keys['DiceScene'];
});

// ▶️ 3. 소켓/게임 상태/버튼 연결(기존 구조 유지)
const roomId = 'monopoly_room';
const socket = initSocket(roomId);
let gameState = null;

socket.on('game_update', (state) => {
  gameState = state;
  renderGame(state);
});
socket.on('turn_update', ({ currentTurn }) => {
  document.getElementById('turnInfo').innerText = `현재 턴: ${currentTurn}`;
});
socket.on('action_error', ({ message }) => {
  alert(message);
});

// ▶️ 4. roll 버튼 클릭시 두 개 결과 + roll 연출
document.getElementById('rollBtn').onclick = () => {
  socket.emit('action', roomId, { type: 'roll' });
  // (임시) 두 개 결과 랜덤 (실전: 서버에서 받아서 roll([a, b]) 호출)
  const result1 = Math.floor(Math.random() * 6) + 1;
  const result2 = Math.floor(Math.random() * 6) + 1;
  if (diceScene) diceScene.roll([result1, result2]);
};

// ▶️ 5. 구매/턴 종료 버튼
document.getElementById('buyBtn').onclick = () => {
  socket.emit('action', roomId, { type: 'buy' });
};
document.getElementById('endBtn').onclick = () => {
  socket.emit('action', roomId, { type: 'end' });
};

// ▶️ 6. 화면 표시 함수
function renderGame(state) {
  document.getElementById('gameInfo').innerHTML =
    state.players.map(p =>
      `<div>${p.id} - 위치: ${p.position}, 현금: ${p.cash}, 소유: [${p.properties.join(', ')}]</div>`
    ).join('');
}

// ★ HTML에는 반드시 <div id="game-container"></div> 포함!
// ex)
// <body>
//   ...
//   <div id="game-container"></div>
//   ...
// </body>
