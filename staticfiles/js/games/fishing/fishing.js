// ======= 익이 피싱 매니아: 저장 X, 리셋 O 완전체 =======

// 1. 사운드 세팅
const sound = {
  bgm:        new Audio("/static/minigame/fishing/sound/bgm.mp3"),
  catch:      new Audio("/static/minigame/fishing/sound/catch.mp3"),
  reel:       new Audio("/static/minigame/fishing/sound/reel.mp3"),
  miss:       new Audio("/static/minigame/fishing/sound/miss.mp3"),
  whoosh:     new Audio("/static/minigame/fishing/sound/whoosh.mp3"),
  jackpot:    new Audio("/static/minigame/fishing/sound/jackpot.mp3"),
  sparkle:    new Audio("/static/minigame/fishing/sound/sparkle.mp3"),
  collection: new Audio("/static/minigame/fishing/sound/collection.mp3"),
  new:        new Audio("/static/minigame/fishing/sound/new.mp3"),
  complete:   new Audio("/static/minigame/fishing/sound/complete.mp3"),
  celebration:new Audio("/static/minigame/fishing/sound/celebration.mp3"),
  record:     new Audio("/static/minigame/fishing/sound/record.mp3"),
  highscore:  new Audio("/static/minigame/fishing/sound/highscore.mp3"),
  success:    new Audio("/static/minigame/fishing/sound/success.mp3"),
  powerup:    new Audio("/static/minigame/fishing/sound/powerup.mp3"),
  upgrade:    new Audio("/static/minigame/fishing/sound/upgrade.mp3"),
  levelup:    new Audio("/static/minigame/fishing/sound/levelup.mp3"),
  evolve:     new Audio("/static/minigame/fishing/sound/evolve.mp3"),
  magic:      new Audio("/static/minigame/fishing/sound/magic.mp3"),
};
sound.bgm.loop = true;
document.addEventListener('click', () => { sound.bgm.volume = 0.17; sound.bgm.play(); }, {once:true});
function playSound(key) {
  try { if (sound[key]) { sound[key].currentTime = 0; sound[key].play(); }} catch(e){}
}

// 2. 게임 데이터: 저장 없음
let score = 0;
let rodLevel = 0;
let collection = {};

// 3. 물고기/낚싯대 정보 (희귀/글로우/이펙트/사운드까지)
const fishList = [
  { emoji:'🐟', name:'도미', point:5 },
  { emoji:'🐠', name:'열대어', point:7 },
  { emoji:'🦑', name:'오징어', point:8 },
  { emoji:'🦀', name:'꽃게', point:10 },
  { emoji:'🐡', name:'복어', point:12 },
  { emoji:'🦞', name:'랍스터', point:14 },
  { emoji:'🦐', name:'새우', point:9 },
  { emoji:'🐬', name:'돌고래', point:13 },
  { emoji:'🐳', name:'고래', point:17 },
  { emoji:'🐋', name:'대왕고래', point:21 },
  { emoji:'🐚', name:'소라', point:7 },
  { emoji:'🦦', name:'수달', point:12 },
  { emoji:'🦈', name:'상어', point:23 },
  { emoji:'🦭', name:'물범', point:16 },
  { emoji:'🐊', name:'악어', point:18 },
  { emoji:'🦩', name:'홍학', point:11 },
  { emoji:'🪼', name:'해파리', point:10 },
  { emoji:'🦧', name:'바다원숭이', point:14 },
  { emoji:'🐙', name:'문어', point:15 },
  { emoji:'🪸', name:'산호', point:10 },
  { emoji:'🪝', name:'낚싯바늘', point:8 },
  { emoji:'🐢', name:'바다거북', point:16 },
  { emoji:'🐸', name:'개구리', point:6 },
  // --- 희귀 물고기들 (희귀, 글로우, 이펙트, 사운드) ---
  { emoji:'🐟', name:'무지개 도미', point:22, glow:'rainbow', sound:'sparkle', effect:'rainbow', rare:true },
  { emoji:'🐠', name:'별빛 열대어', point:19, glow:'cyan', sound:'sparkle', effect:'star', rare:true },
  { emoji:'🦀', name:'황금 꽃게', point:24, glow:'gold', sound:'jackpot', effect:'gold', rare:true },
  { emoji:'🐬', name:'핑크 돌고래', point:25, glow:'pink', sound:'sparkle', effect:'star', rare:true },
  { emoji:'🐋', name:'빛나는 대왕고래', point:32, glow:'cyan', sound:'celebration', effect:'celebrate', rare:true },
  { emoji:'🦈', name:'전설의 상어', point:40, rare:true, glow:'silver', sound:'jackpot', effect:'shake' },
  { emoji:'👑', name:'왕물고기', point:60, rare:true, glow:'gold', sound:'jackpot', effect:'firework' },
  { emoji:'💎', name:'보석물고기', point:80, rare:true, glow:'rainbow', sound:'celebration', effect:'firework' },
  { emoji:'👻', name:'유령물고기', point:90, rare:true, glow:'cyan', sound:'magic', effect:'ghost' },
  { emoji:'🐸', name:'익이의 슈퍼개구리', point:100, rare:true, glow:'green', sound:'celebration', effect:'star' },
  { emoji:'🦖', name:'공룡 물고기', point:120, rare:true, glow:'red', sound:'celebration', effect:'firework' },
];

const rodUpgrades = [
  { name:'나무 막대기', color:'#cbb294', emoji:'🌲', bonus:1, need:0, effect:null, sound:'reel' },
  { name:'은빛 낚싯대', color:'#6bc5ff', emoji:'🎣', bonus:1.1, need:60, effect:null, sound:'reel' },
  { name:'익이의 반짝이 낚싯대', color:'#7fffd4', emoji:'✨', bonus:1.3, need:160, effect:'sparkle', sound:'upgrade' },
  { name:'무지개 낚싯대', color:'#ffb6b9', emoji:'🌈', bonus:1.5, need:320, effect:'rainbow', sound:'upgrade' },
  { name:'용왕의 황금낚싯대', color:'#fbc531', emoji:'👑', bonus:1.8, need:480, effect:'gold', sound:'jackpot' },
  { name:'마법사 낚싯대', color:'#9c88ff', emoji:'🔮', bonus:2.2, need:800, effect:'magic', sound:'magic' },
  { name:'전설의 익이낚싯대', color:'#fd79a8', emoji:'🦸', bonus:3.5, need:1200, effect:'firework', sound:'celebration' }
];

// 4. 캔버스/게임 루프
const canvas = document.getElementById('fishing-canvas');
const ctx = canvas.getContext('2d');

// 보트/낚싯대 좌우 이동
let boatX = canvas.width/2, boatDir = 1, boatSpeed = 2.2, boatY = canvas.height-38, boatEmoji = '🦦';
let isBiting = false;

// 5. 배경/보트/낚싯대/찌 그리기
function drawLakeBG() {
  let gradSky = ctx.createLinearGradient(0, 0, 0, 120);
  gradSky.addColorStop(0, "#e8f6ff");
  gradSky.addColorStop(1, "#c9eafc");
  ctx.fillStyle = gradSky;
  ctx.fillRect(0, 0, canvas.width, 120);
  let gradLake = ctx.createLinearGradient(0, 120, 0, canvas.height);
  gradLake.addColorStop(0, "#b6e2ff");
  gradLake.addColorStop(1, "#81d4fa");
  ctx.fillStyle = gradLake;
  ctx.fillRect(0, 120, canvas.width, canvas.height-120);
  ctx.globalAlpha = 0.13;
  for(let y=140;y<canvas.height;y+=36){
    ctx.beginPath();
    ctx.arc(canvas.width/2-90, y, 220, Math.PI*0.4, Math.PI*0.6, false);
    ctx.arc(canvas.width/2+90, y, 220, Math.PI*0.4, Math.PI*0.6, false);
    ctx.strokeStyle = "#fff";
    ctx.lineWidth = 5;
    ctx.stroke();
  }
  ctx.globalAlpha = 1.0;
}
function drawFishingRod() {
  drawLakeBG();
  // 보트/낚싯대/찌
  ctx.font = '44px serif'; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(boatEmoji, boatX, boatY);
  ctx.strokeStyle = "#888"; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(boatX, boatY-18); ctx.lineTo(boatX, 90); ctx.stroke();
  ctx.font = '28px serif'; ctx.fillText('🟠', boatX, 90 + (isBiting ? 13 : 0));
  ctx.font = '32px serif'; ctx.fillText('🌊🌊🌊', canvas.width/2-56, 118);
  if (isBiting) {
    ctx.font = 'bold 22px sans-serif'; ctx.fillStyle = '#ff6600';
    ctx.fillText('터치!', boatX, 50);
    ctx.fillStyle = '#333';
  }
}

// 6. 보트 자동 이동
function updateBoat() {
  // 난이도(업글/점수마다 점점 빨라짐)
  boatSpeed = 2.2 + rodLevel*0.55 + Math.floor(score/300)*0.37;
  boatX += boatSpeed * boatDir;
  if (boatX < 80) { boatX = 80; boatDir = 1; }
  if (boatX > canvas.width-80) { boatX = canvas.width-80; boatDir = -1; }
  drawFishingRod();
  requestAnimationFrame(updateBoat);
}

// 7. 입질/잡기/놓침/물고기 효과
function startBite() {
  isBiting = true;
  drawFishingRod();
  playSound('reel');
  // 1~1.2초(난이도) 안에 클릭해야 잡힘
  let biteTime = 1200 - rodLevel*60 - Math.floor(score/400)*40;
  if(biteTime<650) biteTime=650;
  setTimeout(() => {
    if (isBiting) {
      isBiting = false;
      drawFishingRod();
      showMissSplash();
      playSound('miss');
      setTimeout(waitBite, 1100);
    }
  }, biteTime);
}
function waitBite() {
  isBiting = false;
  drawFishingRod();
  setTimeout(startBite, 1600 + Math.random()*1600); // 1.6~3.2초 랜덤
}
canvas.onclick = function() {
  if (isBiting) {
    isBiting = false;
    drawFishingRod();
    spawnFish();
  }
};
function spawnFish() {
  const fish = fishList[Math.floor(Math.random()*fishList.length)];
  onCatchFish(fish);
  showBigCatch(fish);
  setTimeout(waitBite, 1300);
}

// 8. 잡기 효과, 놓침 효과
function showBigCatch(fish) {
  const fishDiv = document.createElement('div');
  let extraStyle = '';
  if(fish.glow) extraStyle += `text-shadow:0 0 30px ${fish.glow==='rainbow'?'#fa0,#0af,#fff':fish.glow};`;
  let rareBadge = fish.rare ? '<span style="font-size:1.5em;margin-left:7px;">👑</span>' : '';
  let effectAnim = '';
  if(fish.effect==='rainbow')      effectAnim = '<div style="font-size:2em;">🌈</div>';
  else if(fish.effect==='firework')effectAnim = '<div style="font-size:2em;">🎆🎇</div>';
  else if(fish.effect==='gold')    effectAnim = '<div style="font-size:2em;">✨💰✨</div>';
  else if(fish.effect==='star')    effectAnim = '<div style="font-size:2em;">🌟⭐️✨</div>';
  else if(fish.effect==='celebrate')effectAnim = '<div style="font-size:2em;">🎉🎊</div>';
  else if(fish.effect==='ghost')   effectAnim = '<div style="font-size:2em;">👻💨</div>';
  else if(fish.effect==='plasma')  effectAnim = '<div style="font-size:2em;">⚡️🟣⚡️</div>';
  else if(fish.effect==='cosmic')  effectAnim = '<div style="font-size:2em;">🛸🌌</div>';
  fishDiv.innerHTML = `
    <span style="font-size:5.3em;${extraStyle}">${fish.emoji}${rareBadge}</span>
    <div style="font-size:1.7em;color:#16a;font-weight:bold;">${fish.name}</div>
    ${effectAnim}
  `;
  fishDiv.style.position = 'fixed';
  fishDiv.style.top = '38%'; fishDiv.style.left = '50%';
  fishDiv.style.transform = 'translate(-50%,-50%)';
  fishDiv.style.zIndex = 9988;
  fishDiv.style.background = 'rgba(250,255,250,0.97)';
  fishDiv.style.padding = '1.1em 1.7em';
  fishDiv.style.borderRadius = '1.8em';
  fishDiv.style.boxShadow = '0 4px 36px #ffe066a6';
  if(fish.rare) fishDiv.style.border = "4px solid #f7b731";
  if(fish.glow==='rainbow') fishDiv.style.background="linear-gradient(90deg,#fff7ef,#fffbe9,#ffe9fd,#eafffd,#fff7ef)";
  document.body.appendChild(fishDiv);
  setTimeout(()=>{ fishDiv.remove(); }, 1200);
}
function showMissSplash() {
  const splash = document.createElement('div');
  splash.innerHTML = '<div style="font-size:2.3em;font-weight:bold;color:#38f;">놓쳤어요!<br>🐟💨</div>';
  splash.style.position = 'fixed';
  splash.style.top = '41%'; splash.style.left = '50%';
  splash.style.transform = 'translate(-50%,-50%)';
  splash.style.zIndex = 9979;
  splash.style.background = 'rgba(220,235,255,0.95)';
  splash.style.padding = '1.5em 2.7em';
  splash.style.borderRadius = '1.5em';
  splash.style.boxShadow = '0 8px 44px #b0dcffaa';
  document.body.appendChild(splash);
  setTimeout(()=>{ splash.remove(); }, 900);
}

// 9. 업그레이드 안내/실행
function checkUpgradeSplash() {
  if (rodLevel < rodUpgrades.length-1 &&
      score >= rodUpgrades[rodLevel+1].need) {
    showUpgradeSplash();
  }
}
let splashActive = false;
function showUpgradeSplash() {
  if(splashActive) return;
  splashActive = true;
  const splash = document.createElement('div');
  splash.innerHTML = '<div style="font-size:2.2em; font-weight:bold; color:#ffb100;">낚싯대 업그레이드 가능!<br>✨🎣✨</div>';
  splash.style.position = 'fixed';
  splash.style.top = '42%'; splash.style.left = '50%';
  splash.style.transform = 'translate(-50%,-50%)';
  splash.style.zIndex = 9999;
  splash.style.background = 'rgba(255,255,224,0.96)';
  splash.style.padding = '2em 3em';
  splash.style.borderRadius = '2em';
  splash.style.boxShadow = '0 8px 44px #ffe066a8';
  document.body.appendChild(splash);
  playSound("levelup");
  setTimeout(()=>{ splash.remove(); splashActive = false; }, 1600);
}
function upgradeRod() {
  if (rodLevel < rodUpgrades.length-1 && score >= rodUpgrades[rodLevel+1].need) {
    score -= rodUpgrades[rodLevel+1].need;
    rodLevel++;
    playSound(rodUpgrades[rodLevel].sound || "upgrade");
    showUpgradeEffect(rodUpgrades[rodLevel]);
    renderStatus();
  }
}
document.getElementById('upgrade-btn').onclick = upgradeRod;

// 10. 도감/점수/업글 UI (저장X, 리셋만)
function renderStatus() {
  document.getElementById('score').innerText = score + " pt";
  document.getElementById('rod').innerText = rodUpgrades[rodLevel].emoji + " " + rodUpgrades[rodLevel].name;
  renderCollection();
  checkUpgradeSplash();
}
function renderCollection() {
  const col = document.getElementById('collection');
  col.innerHTML = '';
  fishList.forEach(fish => {
    let owned = collection[fish.name];
    let glowStyle = fish.glow ? `text-shadow:0 0 13px ${fish.glow==='rainbow'?'#fa0,#0af,#fff':fish.glow};` : '';
    let rareBadge = fish.rare ? '<span style="font-size:1.3em;margin-left:3px;">👑</span>' : '';
    let effectBadge = '';
    if(fish.effect==='rainbow') effectBadge = '<span class="fish-badge" style="background:linear-gradient(90deg,#ffda,#aaf,#fff);color:#c44;">무지개</span>';
    else if(fish.effect==='gold') effectBadge = '<span class="fish-badge" style="background:#ffd700;color:#b06;">황금</span>';
    else if(fish.effect==='star') effectBadge = '<span class="fish-badge" style="background:#88f;color:#fff;">별빛</span>';
    else if(fish.effect==='firework') effectBadge = '<span class="fish-badge" style="background:#fa0;color:#fff;">불꽃</span>';
    else if(fish.effect==='celebrate') effectBadge = '<span class="fish-badge" style="background:#1fd;color:#095;">축하</span>';
    else if(fish.effect==='ghost') effectBadge = '<span class="fish-badge" style="background:#ccc;color:#558;">유령</span>';
    else if(fish.effect==='plasma') effectBadge = '<span class="fish-badge" style="background:#b5f;color:#fff;">플라즈마</span>';
    else if(fish.effect==='cosmic') effectBadge = '<span class="fish-badge" style="background:#18dcff;color:#fff;">우주</span>';
    let div = document.createElement('div');
    div.className = 'fish-col' + (owned ? ' owned':'');
    div.innerHTML = `<span style="font-size:2em;${glowStyle}">${fish.emoji}${rareBadge}</span>
      <div class="fish-name">${fish.name}</div>
      ${effectBadge}
      ${owned?'<div class="fish-badge">획득!</div>':''}
    `;
    col.appendChild(div);
  });
}
function onCatchFish(fish) {
  score += Math.floor(fish.point * rodUpgrades[rodLevel].bonus);
  playSound(fish.sound || "catch");
  if (!collection[fish.name]) {
    collection[fish.name] = true;
    playSound("new");
  }
  renderStatus();
}
function showUpgradeEffect(upgrade) {
  ctx.save();
  ctx.font = "32px serif";
  ctx.globalAlpha = 0.87;
  ctx.fillStyle = upgrade.color || "#fa0";
  ctx.fillText("낚싯대 업그레이드!", canvas.width/2, 70);
  ctx.restore();
}

// 11. 리셋 버튼
document.getElementById('reset-btn').onclick = function() {
  score = 0; rodLevel = 0; collection = {};
  renderStatus();
};

// 12. 게임 시작
window.onload = function() {
  renderStatus();
  drawFishingRod();
  updateBoat();
  waitBite();
};
// (BGM은 이미 첫 클릭시 자동 재생)
