/**
 * 모노폴리 게임 메인 로직
 */
import Phaser from 'phaser';
import { Howl } from 'howler';
import { initSocket } from './socket.js';
import Board from './board.js';
import Player from './player.js';
import Dice from './dice.js';

/** Phaser 게임 설정 */
const config = {
  type: Phaser.AUTO,
  width: window.innerWidth,
  height: window.innerHeight,
  parent: 'game-container',
  scene: {
    preload: preload,
    create: create,
    update: update
  }
};

/** 게임 인스턴스 */
const game = new Phaser.Game(config);

/** 글로벌 변수 */
let socket, board, players, dice, bgm, bgmPlayed = false, currentTurn = null, turnText;

/**
 * 에셋을 로드합니다.
 * @param {Phaser.Scene} scene - 현재 Phaser 장면
 */
function preload() {
  this.load.audio('bgm', '/static/minigame/monopoly/assets/bgm.mp3');
  this.load.image('board', '/static/minigame/monopoly/assets/board.png');
  this.load.image('player_token', '/static/minigame/monopoly/assets/player_token.png');
}

/**
 * 게임 객체를 초기화합니다.
 * @param {Phaser.Scene} scene - 현재 Phaser 장면
 */
function create() {
  // 동적 roomId
  const roomId = window.roomId || 'monopoly_room';
  
  // 소켓 초기화
  socket = initSocket(roomId);

  // 보드 초기화
  board = new Board(this);

  // 플레이어 초기화
  players = [];
  socket.on('player_joined', (data) => {
    console.log(`[Main.js] Player joined: ${data.playerId}`);
    // 기존 플레이어 제거
    players.forEach(p => p.sprite.destroy());
    players = [];
    // 새로운 플레이어 목록 추가
    data.playerList.forEach(player => {
      players.push(new Player(this, player.playerId, player.position));
    });
  });

  // 주사위 초기화
  dice = new Dice(this);

  // BGM 설정 (Howler.js)
  bgm = new Howl({
    src: ['/static/minigame/monopoly/assets/bgm.mp3'],
    loop: true,
    volume: 0.5
  });

  // 턴 텍스트 초기화
  turnText = this.add.text(10, 10, 'Current Turn: Waiting', { fontSize: '20px', color: '#ffffff' });

  // 턴 업데이트 처리
  socket.on('turn_update', (data) => {
    currentTurn = data.currentTurn;
    console.log(`[Main.js] Current turn: ${currentTurn}`);
    turnText.setText(`Current Turn: ${currentTurn || 'Waiting'}`);
  });

  // 잘못된 턴 알림
  socket.on('invalid_turn', (data) => {
    console.log(`[Main.js] ${data.message}`);
    const errorText = this.add.text(window.innerWidth / 2 - 100, window.innerHeight / 2, data.message, { fontSize: '24px', color: '#ff0000', align: 'center' });
    setTimeout(() => {
      errorText.destroy();
    }, 2000);
  });

  // 플레이어 퇴장 처리
  socket.on('player_left', (data) => {
    console.log(`[Main.js] Player left: ${data.playerId}`);
    players = players.filter(p => p.id !== data.playerId);
    players.forEach(p => p.sprite.destroy());
    players.forEach(p => p.initSprite());
  });

  // 사용자 액션 후 이벤트
  this.input.on('pointerdown', () => {
    if (!bgmPlayed) {
      console.log('[Main.js] Playing BGM');
      bgm.play();
      bgmPlayed = true;
    }
    if (currentTurn === socket.id) {
      const result = dice.roll();
      console.log(`[Main.js] Emitting roll_dice: ${result} to room ${roomId}`);
      socket.emit('roll_dice', roomId, result);
    }
  });

  // 주사위 결과 처리
  socket.on('dice_rolled', (data) => {
    console.log(`[Main.js] Received dice_rolled: ${data.result} for player ${data.playerId}`);
    const player = players.find(p => p.id === data.playerId);
    if (player) {
      player.move(data.result);
    }
  });
}

/**
 * 게임 상태를 업데이트합니다.
 * @param {number} time - 현재 시간
 * @param {number} delta - 프레임 간 시간 차이
 */
function update(time, delta) {
  players.forEach(player => player.move(0)); // 임시 업데이트
}