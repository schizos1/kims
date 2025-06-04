// fishing_logic.js
window.score = 0;
window.rodLevel = 0;
window.collection = {};
window.isBiting = false;
window.isReeling = false;
window.caughtFish = null;
window.reelProgress = 0;
window.missMessage = null;
window.rodUpgrades = [
  { name:'나무 막대기', color:'#cbb294', emoji:'🌲', bonus:1, need:0, effect:null, sound:'reel' },
  { name:'은빛 낚싯대', color:'#6bc5ff', emoji:'🎣', bonus:1.1, need:60, effect:null, sound:'reel' },
  { name:'익이의 반짝이 낚싯대', color:'#7fffd4', emoji:'✨', bonus:1.3, need:160, effect:'sparkle', sound:'upgrade' },
  { name:'무지개 낚싯대', color:'#ffb6b9', emoji:'🌈', bonus:1.5, need:320, effect:'rainbow', sound:'upgrade' },
  { name:'용왕의 황금낚싯대', color:'#fbc531', emoji:'👑', bonus:1.8, need:480, effect:'gold', sound:'jackpot' },
  { name:'마법사 낚싯대', color:'#9c88ff', emoji:'🔮', bonus:2.2, need:800, effect:'magic', sound:'magic' },
  { name:'전설의 익이낚싯대', color:'#fd79a8', emoji:'🦸', bonus:3.5, need:1200, effect:'firework', sound:'celebration' }
];
window.fishList = [
  { name:'멸치', emoji:'🐟', point:10, rare:false, effect:null, sound:'catch' },
  { name:'정어리', emoji:'🐠', point:15, rare:false, effect:null, sound:'catch' },
  { name:'무지개 송어', emoji:'🐟', point:50, rare:true, effect:'rainbow', sound:'sparkle' },
  { name:'황금 잉어', emoji:'🐠', point:80, rare:true, effect:'gold', sound:'jackpot' }
];

function waitBite() {
  window.isBiting = false;
  window.isReeling = false;
  window.caughtFish = null;
  window.reelProgress = 0;
  window.missMessage = null;
  drawFishingRod();
  setTimeout(startBite, 5000 + Math.random()*5000);
}
function startBite() {
  window.isBiting = true;
  drawFishingRod();
  let biteTime = 1700 - window.rodLevel*70 - Math.floor(window.score/500)*40;
  if(biteTime<1000) biteTime=1000;
  setTimeout(() => {
    if (window.isBiting) {
      window.isBiting = false;
      drawFishingRod();
      showMissSplash("놓쳤어요!");
      playSound('miss');
      setTimeout(waitBite, 1100);
    }
  }, biteTime);
}
canvas.onclick = function(e) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const clickX = (e.clientX - rect.left) * scaleX;
  const clickY = (e.clientY - rect.top) * scaleY;
  const dx = clickX - boatX;
  const dy = clickY - 103;
  const dist = Math.sqrt(dx*dx + dy*dy);
  let arcR = window.isBiting ? 62 : 36;
  if (dist < arcR && window.isBiting) {
    spawnFishWithRodCheck();
  } else {
    window.isBiting = false;
    if (!window.isReeling) {
      showMissSplash(window.isBiting ? "포인트를 정확히 눌러야 해요!" : "타이밍이 아니에요! 놓쳤어요~");
      playSound("miss");
    }
    drawFishingRod(true, clickX, clickY);
    setTimeout(waitBite, 950);
  }
};
function spawnFishWithRodCheck() {
  window.isBiting = false;
  const fish = window.fishList[Math.floor(Math.random()*window.fishList.length)];
  window.isReeling = true;
  window.caughtFish = fish;
  window.reelProgress = 0;
  playSound("reel");
  showBigCatch(fish);
  setTimeout(() => {
    window.isReeling = false;
    if (fish.rare && window.rodLevel < minRodLevelFor(fish.name)) {
      window.missMessage = "낚싯대를 업그레이드 하세요!";
      playSound("whoosh");
    } else {
      const points = Math.floor(fish.point * window.rodUpgrades[window.rodLevel].bonus);
      window.score = (window.score || 0) + points;
      onCatchFish(fish);
      checkUpgradeSplash();
    }
    setTimeout(waitBite, 1300);
  }, fish.rare ? 4000 : 2000);
}
function minRodLevelFor(name) {
  if (name.includes("전설")||name.includes("왕")||name.includes("보석")||name.includes("공룡")||name.includes("슈퍼")) return 5;
  if (name.includes("무지개")||name.includes("빛나")||name.includes("황금")||name.includes("유령")||name.includes("별빛")||name.includes("핑크")) return 3;
  return 0;
}
function onCatchFish(fish) {
  playSound(fish.sound || "catch");
  if (!window.collection[fish.name]) {
    window.collection[fish.name] = true;
    playSound("new");
  }
  renderRodStatus();
  renderCollection();
}
function showMissSplash(msg="놓쳤어요!") {
  const splash = document.createElement('div');
  splash.innerHTML = `<div style="font-size:2.3em;font-weight:bold;color:#38f;">${msg}<br>🐟💨</div>`;
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
function renderCollection() {
  const col = document.getElementById('collection');
  if (!col) {
    console.error("Collection element not found");
    return;
  }
  col.innerHTML = '';
  window.fishList.forEach(fish => {
    let owned = window.collection[fish.name];
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
function checkUpgradeSplash() {
  let next = window.rodUpgrades[window.rodLevel+1];
  if (!next) return;
  if ((window.score || 0) >= next.need) {
    const splash = document.createElement('div');
    splash.innerHTML = `<div style="font-size:2.0em;font-weight:bold;color:#f80;">낚싯대 업그레이드 가능!<br>${next.emoji} ${next.name}</div>`;
    splash.style.position = 'fixed';
    splash.style.top = '44%'; splash.style.left = '50%';
    splash.style.transform = 'translate(-50%,-50%)';
    splash.style.zIndex = 9981;
    splash.style.background = 'rgba(255, 255, 223, 0.96)';
    splash.style.padding = '1.2em 2.4em';
    splash.style.borderRadius = '1.7em';
    splash.style.boxShadow = '0 8px 28px #ffd83366';
    document.body.appendChild(splash);
    playSound("upgrade");
    setTimeout(()=>{ splash.remove(); }, 1400);
  }
}
function showBigCatch(fish) {
  const splash = document.createElement('div');
  const points = Math.floor(fish.point * window.rodUpgrades[window.rodLevel].bonus);
  splash.innerHTML = `<div style="font-size:2.5em;font-weight:bold;color:#2a8;">${fish.emoji} ${fish.name} 잡는 중!</div>`;
  splash.style.position = 'fixed';
  splash.style.top = '41%'; splash.style.left = '50%';
  splash.style.transform = 'translate(-50%,-50%)';
  splash.style.zIndex = 9980;
  splash.style.background = 'rgba(220,255,235,0.95)';
  splash.style.padding = '1.5em 2.7em';
  splash.style.borderRadius = '1.5em';
  splash.style.boxShadow = '0 8px 44px #b0ffccaa';
  document.body.appendChild(splash);
  setTimeout(()=>{ splash.remove(); }, 1200);
}