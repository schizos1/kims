// /static/js/games/emoji_battle/main.js

// Emoji Battle 게임 클라이언트 (v2.1 by 토모맨, 배경 선택 제거)
// 멀티세션 게임으로, 점수와 위치를 실시간 동기화하고 PostgreSQL에 기록

// 전역 변수 사용 (PIXI, PIXI.filters, Howl, io는 <script> 태그로 로드됨)
// GSAP는 CDN에서 로드

// PixiJS 애플리케이션 설정
// @type {PIXI.Application}
const app = new PIXI.Application({
  width: 800,
  height: 600,
  backgroundColor: 0x181822,
});
window.__PIXI_DEVTOOLS__ = { app };

// 캔버스 초기화
const canvasEl = document.getElementById('emoji-canvas');
if (canvasEl && canvasEl.parentNode) {
  app.canvas.style.position = 'relative';
  app.canvas.style.zIndex = '1';
  app.canvas.id = 'emoji-canvas';
  canvasEl.parentNode.replaceChild(app.canvas, canvasEl);
} else {
  console.error('PixiJS Setup FAILED: "emoji-canvas" element or its parent not found.');
  alert('치명적 오류: 게임 캔버스를 찾을 수 없습니다.');
}
const stage = app.stage;
stage.sortableChildren = true;

// UI 텍스트 스타일
// @type {Object}
const uiTextStyle = {
  fontFamily: 'Arial Black, Arial, sans-serif',
  stroke: { color: '#222222', width: 6 },
  align: 'center',
};

// 점수 텍스트
let scoreText = new PIXI.Text({
  text: '점수: 0',
  style: { ...uiTextStyle, fontSize: 34, fill: '#ffe958' },
});
scoreText.anchor.set(1, 0);
scoreText.x = app.screen.width - 20;
scoreText.y = 10;
scoreText.zIndex = 100;
stage.addChild(scoreText);

// 히트 텍스트
let hitText = new PIXI.Text({
  text: '히트: 0 / 50',
  style: { ...uiTextStyle, fontSize: 28, fill: '#81fffe' },
});
hitText.x = 20;
hitText.y = 14;
hitText.zIndex = 100;
stage.addChild(hitText);

// 상대 점수 텍스트
let enemyScoreText = new PIXI.Text({
  text: '상대 점수: 0',
  style: { ...uiTextStyle, fontSize: 28, fill: '#ff6b6b' },
});
enemyScoreText.anchor.set(1, 0);
enemyScoreText.x = app.screen.width - 20;
enemyScoreText.y = 50;
enemyScoreText.zIndex = 100;
stage.addChild(enemyScoreText);

// 프로그레스 바
let progBar = new PIXI.Graphics();
progBar.x = 16;
progBar.y = 56;
progBar.zIndex = 99;
stage.addChild(progBar);

// 프로그레스 바 업데이트 함수
// @param {number} hits - 현재 히트 수
function updateProgBar(hits) {
  progBar.clear();
  let pct = Math.min(hits / 50, 1);
  progBar.beginFill(0x2525ff, 0.13);
  progBar.drawRoundedRect(0, 0, 768, 18, 8);
  progBar.endFill();
  if (pct > 0) {
    progBar.beginFill(0xffe958, 0.95);
    progBar.drawRoundedRect(2, 2, 764 * pct, 14, 6);
    progBar.endFill();
  }
  console.log(`Progress bar updated: hits=${hits}, pct=${pct}`);
}
updateProgBar(0);

// 사운드 맵
// @type {Object}
const sounds = {
  throw: new Howl({ src: ['/static/minigame/emoji_battle/sound/throw.mp3'], volume: 0.6 }),
  hit: new Howl({ src: ['/static/minigame/emoji_battle/sound/hit.mp3'], volume: 0.6 }),
  frozen: new Howl({ src: ['/static/minigame/emoji_battle/sound/frozen.mp3'], volume: 0.6 }),
  frozenHit: new Howl({ src: ['/static/minigame/emoji_battle/sound/frozen hit.mp3'], volume: 0.6 }),
  slide: new Howl({ src: ['/static/minigame/emoji_battle/sound/slide.mp3'], volume: 0.6 }),
  win: new Howl({ src: ['/static/minigame/emoji_battle/sound/win.mp3'], volume: 0.7 }),
  lose: new Howl({ src: ['/static/minigame/emoji_battle/sound/lose.mp3'], volume: 0.7 }),
  bgm: new Howl({ src: ['/static/minigame/emoji_battle/sound/bgm.mp3'], volume: 0.25, loop: true }),
};
let bgmStarted = false;

// 게임 상태 변수
let myId = null;
let myX = 400,
  myY = 520;
let enemyX = 400,
  enemyY = 86;
let myEmoji = '🐱',
  enemyEmoji = '🐶';
let mySprite = null,
  enemySprite = null;
let enemyPlayerId = null;

const weaponSpeed = 10;
let myWeapons = [];
let enemyWeapons = [];

let effects = [];
let myScore = 0,
  myHits = 0;
let isFrozen = false,
  frozenTimeout = null;
let isGameStarted = false;
let lastSlideTime = 0;

const MOVE_SPEED = 5;
let keysPressed = {};

let lastFireTime = 0;
const FIRE_COOLDOWN = 320; // ms

// 소켓 연결
const socket = io('http://192.168.31.199:3001/emoji-battle');

// 페이지 초기화 함수
function initializePageContent() {
  const msgEl = document.getElementById('emoji-msg');
  const emojiSelectDiv = document.getElementById('emoji-select');
  const startBtn = document.getElementById('emoji-start-btn');

  if (!msgEl || !emojiSelectDiv || !startBtn) {
    console.error('DOM elements not found:', { msgEl, emojiSelectDiv, startBtn });
    return;
  }

  msgEl.textContent = '캐릭터 선택 후 시작!';
  updateProgBar(0);

  // 캐릭터 선택 이벤트 바인딩
  let emojiSel = null;
  const emojiButtons = document.querySelectorAll('.emoji-btn');
  if (emojiButtons.length === 0) {
    console.error('No .emoji-btn elements found');
    return;
  }
  console.log(`Found ${emojiButtons.length} .emoji-btn elements`);

  emojiButtons.forEach((el) => {
    el.onclick = function () {
      emojiButtons.forEach((e) => e.classList.remove('selected'));
      el.classList.add('selected');
      emojiSel = el.dataset.emoji;
      console.log('Emoji selected:', emojiSel);
      if (emojiSel && startBtn) {
        startBtn.disabled = false;
      }
    };
  });

  if (startBtn) {
    startBtn.onclick = function () {
      if (!emojiSel) {
        msgEl.textContent = '캐릭터를 선택해주세요!';
        console.warn('Start button clicked without emoji selection');
        return;
      }
      myEmoji = emojiSel;
      emojiSelectDiv.classList.add('hidden');
      if (!bgmStarted && sounds.bgm) {
        sounds.bgm.play();
        bgmStarted = true;
        console.log('BGM started');
      }
      initGame();
    };
  }

  // 소켓 이벤트 핸들러
  socket.on('connect', () => {
    myId = socket.id;
    msgEl.textContent = '다른 플레이어가 입장하면 게임이 시작됩니다.';
    isGameStarted = false;
    console.log('Socket connected:', myId);
  });

  socket.on('connect_error', (err) => {
    msgEl.textContent = '서버 연결 실패! 잠시 후 다시 시도해주세요.';
    console.error('Socket connect error:', err);
  });
}

// DOM 로드 완료 후 초기화
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePageContent);
} else {
  initializePageContent();
}

// 게임 상태 초기화 함수
function initGame() {
  if (!socket.connected) {
    const msgEl = document.getElementById('emoji-msg');
    if (msgEl) msgEl.textContent = '서버에 연결되지 않았습니다. 잠시 후 다시 시도해주세요.';
    console.error('Socket not connected');
    return;
  }

  destroyAllSprites();

  myX = app.screen.width / 2;
  myScore = 0;
  myHits = 0;
  isGameStarted = false;
  isFrozen = false;
  enemyPlayerId = null;

  updateProgBar(myHits);
  scoreText.text = `점수: ${myScore}`;
  hitText.text = `히트: ${myHits} / 50`;
  enemyScoreText.text = '상대 점수: 0';
  const msgEl = document.getElementById('emoji-msg');
  if (msgEl) msgEl.textContent = '다른 플레이어가 입장하면 게임이 시작됩니다...';

  socket.emit('join_emoji_room', {
    room: 'emoji_battle',
    userData: { user: 'player', emoji: myEmoji },
  });
}

// 모든 스프라이트 제거 함수
function destroyAllSprites() {
  if (mySprite && mySprite.parent) {
    stage.removeChild(mySprite);
    mySprite.destroy({ children: true });
    mySprite = null;
  }
  if (enemySprite && enemySprite.parent) {
    stage.removeChild(enemySprite);
    enemySprite.destroy({ children: true });
    enemySprite = null;
  }
  myWeapons.forEach((w) => {
    if (w.parent) stage.removeChild(w);
    w.destroy({ children: true });
  });
  myWeapons = [];
  enemyWeapons.forEach((w) => {
    if (w.parent) stage.removeChild(w);
    w.destroy({ children: true });
  });
  enemyWeapons = [];
  effects.forEach((eff) => {
    if (eff.sprite && eff.sprite.parent) stage.removeChild(eff.sprite);
    if (eff.sprite.destroy) eff.sprite.destroy({ children: true });
  });
  effects = [];
}

// 게임 시작 이벤트 처리
socket.on('emoji_start', (data) => {
  try {
    if (!myId) return;
    let players = data.players;
    if (!Array.isArray(players) || players.length !== 2) return;
    let meFromServer = players.find((p) => p.id === myId);
    let enemyFromServer = players.find((p) => p.id !== myId);

    myEmoji = meFromServer.emoji;
    myX = meFromServer.x;
    enemyEmoji = enemyFromServer.emoji;
    enemyX = enemyFromServer.x;
    enemyPlayerId = enemyFromServer.id;

    drawPlayers();
    isGameStarted = true;
    const msgEl = document.getElementById('emoji-msg');
    if (msgEl) msgEl.textContent = '게임 시작!';
    console.log('Game started:', { myId, myEmoji, enemyEmoji });
  } catch (error) {
    const msgEl = document.getElementById('emoji-msg');
    if (msgEl) msgEl.textContent = '오류! 게임 시작 불가. 콘솔 확인.';
    console.error('emoji_start error:', error);
  }
});

// 플레이어 스프라이트 그리기 함수
function drawPlayers() {
  if (mySprite && mySprite.parent) {
    stage.removeChild(mySprite);
    mySprite.destroy({ children: true });
    mySprite = null;
  }
  if (enemySprite && enemySprite.parent) {
    stage.removeChild(enemySprite);
    enemySprite.destroy({ children: true });
    enemySprite = null;
  }
  const playerTextStyle = {
    fontSize: 70,
    fill: '#FFFFFF',
    stroke: { color: '#000000', width: 5 },
    align: 'center',
  };
  mySprite = new PIXI.Text({
    text: myEmoji,
    style: playerTextStyle,
  });
  mySprite.name = 'MyPlayerSprite';
  mySprite.anchor.set(0.5);
  mySprite.x = myX;
  mySprite.y = myY;
  mySprite.zIndex = 10;
  stage.addChild(mySprite);

  enemySprite = new PIXI.Text({
    text: enemyEmoji,
    style: playerTextStyle,
  });
  enemySprite.name = 'EnemyPlayerSprite';
  enemySprite.anchor.set(0.5);
  enemySprite.x = enemyX;
  enemySprite.y = enemyY;
  enemySprite.zIndex = 10;
  stage.addChild(enemySprite);
  console.log('Players drawn:', { myX, enemyX });
}

// 충돌 감지 함수
// @param {PIXI.Text} r1 - 첫 번째 스프라이트
// @param {PIXI.Text} r2 - 두 번째 스프라이트
// @returns {boolean} - 충돌 여부
function hitTestRectangle(r1, r2) {
  if (!r1 || !r2 || !r1.getBounds || !r2.getBounds || !r1.parent || !r2.parent) return false;
  const bounds1 = r1.getBounds(true),
    bounds2 = r2.getBounds(true);
  return (
    bounds1.x < bounds2.x + bounds2.width &&
    bounds1.x + bounds1.width > bounds2.x &&
    bounds1.y < bounds2.y + bounds2.height &&
    bounds1.y + bounds1.height > bounds2.y
  );
}

// 무기 발사 함수
function fireMyWeapon() {
  if (!mySprite || !mySprite.parent || isFrozen || !isGameStarted) return;
  let now = Date.now();
  if (now - lastFireTime < FIRE_COOLDOWN) return;
  lastFireTime = now;

  // config.js의 EMOJI_TYPES와 동기화
  const weaponEmojis = ['🥶', '❄️', '🍌', '💖', '🍎', '🍔', '🍕'];
  const emoji = weaponEmojis[Math.floor(Math.random() * weaponEmojis.length)];
  const weaponTextStyle = {
    fontSize: 42,
    fill: '#FFFF88',
    stroke: { color: '#333300', width: 2 },
  };
  let weapon = new PIXI.Text({
    text: emoji,
    style: weaponTextStyle,
  });
  weapon.name = `MyWeapon_${emoji}`;
  weapon.anchor.set(0.5);
  weapon.x = mySprite.x;
  weapon.y = mySprite.y - mySprite.height / 2 - 5;
  weapon.isPlayerWeapon = true;
  weapon.emojiType = emoji;
  weapon.zIndex = 5;
  stage.addChild(weapon);
  myWeapons.push(weapon);

  // 발사 이펙트
  let expandMidX = app.screen.width / 2;
  let expandMidY = mySprite.y - 180 + (Math.random() - 0.5) * 30;
  let expandScale = 2 + (Math.random() - 0.5) * 0.15;
  let timeline = gsap.timeline();
  if (Math.random() < 0.03) {
    expandMidX += (Math.random() - 0.5) * 320;
    expandScale *= 1.35 + Math.random() * 0.25;
  }
  timeline
    .to(weapon, {
      x: expandMidX,
      y: expandMidY,
      scale: expandScale,
      duration: 0.18,
      ease: 'back.out(2)',
    })
    .to(weapon, {
      x: enemySprite ? enemySprite.x : expandMidX,
      y: enemySprite ? enemySprite.y : 80,
      scale: 1,
      duration: 0.23,
      ease: 'power1.in',
    });

  if (sounds.throw && sounds.throw.state() === 'loaded') sounds.throw.play();
  socket.emit('emoji_throw', { emoji: emoji, x: weapon.x, y: weapon.y });
  console.log('Weapon fired:', { emoji, x: weapon.x });
}

// 상대방 무기 생성 이벤트 처리
socket.on('emoji_thrown', (data) => {
  if (data.id === myId || !isGameStarted) return;
  if (!enemySprite || !enemySprite.parent) return;
  const weaponTextStyle = {
    fontSize: 42,
    fill: '#FF8C66',
    stroke: { color: '#330000', width: 2 },
  };
  let weapon = new PIXI.Text({
    text: data.emoji,
    style: weaponTextStyle,
  });
  weapon.name = `EnemyWeapon_${data.emoji}`;
  weapon.anchor.set(0.5);
  weapon.x = data.x;
  weapon.y = enemySprite.y + enemySprite.height / 2 + 5;
  weapon.isPlayerWeapon = false;
  weapon.emojiType = data.emoji;
  weapon.zIndex = 5;
  stage.addChild(weapon);
  enemyWeapons.push(weapon);
  console.log('Enemy weapon received:', data);
});

// 명중 이벤트 처리
socket.on('emoji_hit', (data) => {
  if (!isGameStarted) return;
  console.log('emoji_hit received:', data);
  let hitTargetSprite = data.target === myId ? mySprite : enemySprite;
  let hitEffectEmoji = data.emoji;
  if (!hitTargetSprite || !hitTargetSprite.parent) {
    console.warn('Hit target sprite invalid:', { target: data.target, sprite: hitTargetSprite });
    return;
  }

  // 이모지 효과 및 사운드 처리
  if (hitEffectEmoji === '🥶' || hitEffectEmoji === '❄️') {
    frozenEffect(hitTargetSprite);
    if (sounds.frozenHit && sounds.frozenHit.state() === 'loaded') sounds.frozenHit.play();
    if (sounds.frozen && sounds.frozen.state() === 'loaded') sounds.frozen.play();
  } else if (hitEffectEmoji === '🍌') {
    slideEffect(hitTargetSprite);
    if (sounds.slide && sounds.slide.state() === 'loaded') sounds.slide.play();
  } else {
    if (sounds.hit && sounds.hit.state() === 'loaded') sounds.hit.play();
  }
  showHitEffect(hitTargetSprite);

  // 점수 업데이트
  if (data.attacker === myId) {
    if (typeof data.score !== 'number' || typeof data.hits !== 'number') {
      console.error('Invalid score/hits data:', data);
      return;
    }
    myScore = data.score;
    myHits = data.hits;
    scoreText.text = `점수: ${myScore}`;
    hitText.text = `히트: ${myHits} / 50`;
    updateProgBar(myHits);
    console.log(`My score updated: score=${myScore}, hits=${myHits}`);
  }
  // 상대방 점수 업데이트
  if (typeof data.opponentScore === 'number') {
    enemyScoreText.text = `상대 점수: ${data.opponentScore}`;
    console.log(`Opponent score updated: ${data.opponentScore}`);
  } else {
    console.warn('Opponent score missing in payload:', data);
  }
});

// 게임 루프
app.ticker.add((delta) => {
  if (!isGameStarted) return;
  const actualMoveSpeed = MOVE_SPEED * delta;
  let moved = false;
  if (mySprite && mySprite.parent) {
    if (keysPressed['ArrowLeft']) {
      myX = Math.max(mySprite.width / 2, myX - actualMoveSpeed);
      moved = true;
    }
    if (keysPressed['ArrowRight']) {
      myX = Math.min(app.screen.width - mySprite.width / 2, myX + actualMoveSpeed);
      moved = true;
    }
    if (moved) {
      mySprite.x = myX;
      socket.emit('emoji_move', { x: myX });
      console.log('Player moved:', { myX });
    }
  }
  for (let i = myWeapons.length - 1; i >= 0; i--) {
    let weapon = myWeapons[i];
    if (!weapon || !weapon.parent) {
      myWeapons.splice(i, 1);
      continue;
    }
    weapon.y -= weaponSpeed * delta;
    if (weapon.y < -weapon.height) {
      stage.removeChild(weapon);
      weapon.destroy();
      myWeapons.splice(i, 1);
    } else if (enemySprite && enemySprite.parent && enemyPlayerId && hitTestRectangle(weapon, enemySprite)) {
      socket.emit('player_hit_target', {
        target: enemyPlayerId,
        emoji: weapon.emojiType,
      });
      stage.removeChild(weapon);
      weapon.destroy();
      myWeapons.splice(i, 1);
      console.log('Hit detected:', { target: enemyPlayerId, emoji: weapon.emojiType });
    }
  }
  for (let i = enemyWeapons.length - 1; i >= 0; i--) {
    let weapon = enemyWeapons[i];
    if (!weapon || !weapon.parent) {
      enemyWeapons.splice(i, 1);
      continue;
    }
    weapon.y += weaponSpeed * delta;
    if (weapon.y > app.screen.height + weapon.height) {
      stage.removeChild(weapon);
      weapon.destroy();
      enemyWeapons.splice(i, 1);
    }
  }
  for (let i = effects.length - 1; i >= 0; i--) {
    const eff = effects[i];
    if (!eff.sprite || !eff.sprite.parent) {
      if (eff.sprite && eff.sprite.destroy) eff.sprite.destroy({ children: true });
      effects.splice(i, 1);
      continue;
    }
    eff.sprite.x += eff.vx * delta;
    eff.sprite.y += eff.vy * delta;
    eff.vy += 0.5 * delta;
    eff.life -= delta * 30;
    if (eff.life <= 0) {
      stage.removeChild(eff.sprite);
      eff.sprite.destroy({ children: true });
      effects.splice(i, 1);
    }
  }
});

// 명중 이펙트 함수
// @param {PIXI.Text} targetSprite - 명중된 스프라이트
function showHitEffect(targetSprite) {
  if (!targetSprite || !targetSprite.parent) return;
  targetSprite.filters = [
    new PIXI.filters.GlowFilter({ color: 0xff4d4d, distance: 15, outerStrength: 1.5, quality: 0.2 }),
  ];
  gsap.to(targetSprite.scale, {
    x: 1.1,
    y: 1.1,
    yoyo: true,
    repeat: 1,
    duration: 0.08,
    onComplete: () => {
      if (targetSprite && targetSprite.filters) targetSprite.filters = [];
    },
  });
  for (let i = 0; i < 10; i++) {
    let part = new PIXI.Graphics();
    part.name = `Particle_${i}`;
    part.beginFill(0xffe958 + Math.floor(Math.random() * 0x000888));
    part.drawCircle(0, 0, 1 + Math.random() * 2);
    part.x = targetSprite.x + (Math.random() - 0.5) * 15;
    part.y = targetSprite.y + (Math.random() - 0.5) * 15;
    part.zIndex = 15;
    stage.addChild(part);
    let angle = Math.random() * Math.PI * 2;
    let speed = 2 + Math.random() * 3;
    let vx = Math.cos(angle) * speed;
    let vy = Math.sin(angle) * speed;
    effects.push({ sprite: part, vx, vy, life: 15 + Math.random() * 10 });
  }
  const hitTextStyle = {
    fontSize: 34,
    fill: '#ff1111',
    stroke: { color: '#ffffff', width: 4 },
    fontWeight: 'bold',
    dropShadow: true,
    dropShadowColor: '#000000',
    dropShadowAlpha: 0.6,
    dropShadowDistance: 2,
  };
  let hitFx = new PIXI.Text({
    text: 'HIT!',
    style: hitTextStyle,
  });
  hitFx.name = 'HitText';
  hitFx.anchor.set(0.5);
  hitFx.x = targetSprite.x;
  hitFx.y = targetSprite.y - targetSprite.height / 2 - 5;
  hitFx.zIndex = 101;
  stage.addChild(hitFx);
  gsap.to(hitFx, {
    y: hitFx.y - 20,
    alpha: 0,
    duration: 0.5,
    ease: 'power1.out',
    onComplete: () => {
      if (hitFx.parent) {
        stage.removeChild(hitFx);
        hitFx.destroy();
      }
    },
  });
}

// 프로즌 이펙트 함수
// @param {PIXI.Text} sprite - 대상 스프라이트
function frozenEffect(sprite) {
  if (!sprite || !sprite.parent) return;
  sprite.filters = [
    new PIXI.filters.GlowFilter({ color: 0x20f4ff, distance: 12, outerStrength: 1.8, quality: 0.2 }),
  ];
  sprite.alpha = 0.7;
  if (sprite === mySprite) {
    isFrozen = true;
    if (frozenTimeout) clearTimeout(frozenTimeout);
    frozenTimeout = setTimeout(() => {
      if (mySprite && mySprite.parent) {
        mySprite.filters = [];
        mySprite.alpha = 1;
      }
      isFrozen = false;
    }, 1500);
  }
  if (sounds.frozen && sounds.frozen.state() === 'loaded') sounds.frozen.play();
}

// 슬라이드 이펙트 함수
// @param {PIXI.Text} sprite - 대상 스프라이트
function slideEffect(sprite) {
  if (!sprite || !sprite.parent) return;
  if (Date.now() - lastSlideTime < 700) return;
  lastSlideTime = Date.now();
  const isMySprite = sprite === mySprite;
  const slideTargetX = sprite.x + (Math.random() < 0.5 ? -50 : 50);
  const finalX = Math.max(sprite.width / 2, Math.min(app.screen.width - mySprite.width / 2, slideTargetX));
  const rotationAmount = finalX > sprite.x ? 0.15 : -0.15;
  gsap.to(sprite, {
    x: finalX,
    rotation: rotationAmount,
    duration: 0.1,
    ease: 'power1.out',
    onComplete: () => {
      if (isMySprite) {
        myX = sprite.x;
        socket.emit('emoji_move', { x: myX });
      }
      if (sprite && sprite.parent) gsap.to(sprite, { rotation: 0, duration: 0.1 });
    },
  });
  if (sounds.slide && sounds.slide.state() === 'loaded') sounds.slide.play();
}

// 상대방 이동 이벤트 처리
socket.on('emoji_move', (data) => {
  if (data.id === myId || !isGameStarted) return;
  if (enemySprite && enemySprite.parent) {
    gsap.to(enemySprite, { x: data.x, duration: 0.05 });
    enemyX = data.x;
    console.log('Enemy moved:', { x: enemyX });
  }
});

// 게임 종료 이벤트 처리
socket.on('emoji_game_over', async function(data) {
  isGameStarted = false;
  const msgEl = document.getElementById('emoji-msg');
  if (msgEl) msgEl.textContent = '게임 종료!';
  destroyAllSprites();
  if (sounds.bgm && bgmStarted) sounds.bgm.fade(0.25, 0, 800);

  // Django API로 점수 저장
  try {
    const response = await fetch('/api/update_score/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({
        user_id: myId,
        score: myScore,
        hits: myHits,
        game: 'emoji_battle',
        result: data.winner === myId ? 'win' : 'loss',
      }),
    });
    if (!response.ok) throw new Error('Score save failed');
    console.log('Score saved to DB:', { score: myScore, hits: myHits, result: data.winner === myId ? 'win' : 'loss' });
  } catch (error) {
    console.error('Error saving game:', error);
  }

  const resultPopup = document.getElementById('game-result-popup');
  const resultImg = document.getElementById('result-img');
  const resultText = document.getElementById('result-text');

  setTimeout(() => {
    if (resultPopup) resultPopup.style.display = 'flex';
    if (data.winner === myId) {
      if (resultText) resultText.textContent = '🎉 성공! 🎉';
      if (resultImg) {
        resultImg.src = '/static/minigame/emoji_battle/img/victory.png';
        resultImg.style.display = '';
      }
      if (sounds.win && sounds.win.state() === 'loaded') sounds.win.play();
    } else {
      if (resultText) resultText.textContent = '😢 패배... 😢';
      if (resultImg) {
        resultImg.src = '/static/minigame/emoji_battle/img/defeat.png';
        resultImg.style.display = '';
      }
      if (sounds.lose && sounds.lose.state() === 'loaded') sounds.lose.play();
    }
  }, 800);
});

// 상대방 이탈 이벤트 처리
socket.on('emoji_player_left', (data) => {
  isGameStarted = false;
  const msgEl = document.getElementById('emoji-msg');
  if (msgEl) msgEl.textContent = '상대가 나갔습니다. 잠시 후 초기화됩니다.';
  const resultPopup = document.getElementById('game-result-popup');
  if (resultPopup) resultPopup.style.display = 'none';
  if (sounds.bgm && bgmStarted) sounds.bgm.fade(0.25, 0, 500);
  setTimeout(resetGameScreen, 1500);
});

// 키 입력 이벤트
document.addEventListener('keydown', (e) => {
  if (!isGameStarted || isFrozen) return;
  if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
    keysPressed[e.key] = true;
  } else if (e.key === 'Space' && !e.repeat) {
    fireMyWeapon();
  }
});
document.addEventListener('keyup', (e) => {
  if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
    delete keysPressed[e.key];
  }
});

// 게임 화면 리셋 함수
function resetGameScreen() {
  destroyAllNodes();
  myScore = 0;
  myHitsPoints = 0;
  scoreText.text = '점수: 0';
  hitText.text = '히트: 0 / 50';
  enemyScoreText.text = '상대 점수: 0';
  updateProgBar(0);
  const msgEl = document.getElementById('emojiMsg');
  const emojiSelectDiv = document.getElementById('emoji-select');
  const resultPopup = document.getElementById('game-result-popup');
  if (msgEl) msgEl.textContent = '캐릭터 선택 후 시작!';
  if (!emojiSelectDiv) emojiSelectDiv.classList.remove('hidden');
  if (resultPopup) resultPopup.style.display = 'none';
  isGameStarted = false;
  isFrozen = false;
  enemyPlayerId = null;
  keysPressed = {};
  if (sounds.bgm && bgmStarted) {
    sounds.bgm.stop();
    bgmStarted = false;
  }
});

// 팝업 클릭 시 리셋
const resultGamePopup = document.getElementById('game-result-popup');
if (resultPopup) {
  resultGamePopup.onclick = function() {
    resetGameScreen();
  };
};

// CSRF token 가져오기 함수
// @param {string} name - 쿠키 이름
// @returns {string|null} - 쿠키 값
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

window.onerror = function(message, source, lineno, colno, error) {
  const msgEl = document.getElementById('emoji-msg');
  if (msgEl) msgEl.textContent = '치명적인 오류 발생! 콘솔 확인.';
  console.error('Global error:', message, source, lineno, colno, error);
};