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
let socket, board, players, dice, bgm, bgmPlayed = false;

/**
 * 에셋을 로드합니다.
 * @param {Phaser.Scene} scene - 현재 Phaser 장면
 */
function preload() {
  this.load.audio('bgm', '/static/minigame/monopoly/assets/bgm.mp3');
  // TODO: 실제 에셋 추가
  // this.load.image('board', '/static/minigame/monopoly/assets/board.png');
  // this.load.image('player_token', '/static/minigame/monopoly/assets/player_token.png');
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
    players.push(new Player(this, data.playerId, data.position));
  });

  // 주사위 초기화
  dice = new Dice(this);

  // BGM 설정 (Howler.js)
  bgm = new Howl({
    src: ['/static/minigame/monopoly/assets/bgm.mp3'],
    loop: true,
    volume: 0.5
  });

  // 사용자 액션 후 BGM 재생
  this.input.on('pointerdown', () => {
    if (!bgmPlayed) {
      console.log('[Main.js] Playing BGM');
      bgm.play();
      bgmPlayed = true;
    }
    // 주사위 굴리기
    const result = dice.roll();
    console.log(`[Main.js] Emitting roll_dice: ${result} to room ${roomId}`);
    socket.emit('roll_dice', roomId, result);
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