// lake_bg.js
const canvas = document.getElementById('fishing-canvas');
if (!canvas) {
  console.error("Canvas element not found");
} else {
  canvas.width = 800;
  canvas.height = 600;
}
const ctx = canvas ? canvas.getContext('2d') : null;
let bgFishList = [];
for(let i=0;i<12;i++) {
  bgFishList.push({
    emoji: ["🐟","🐠","🦑","🦀","🐡","🦞","🦐","🐬","🐳","🐋","🦈","🐙","🐚","🦦","🌊","✨"][Math.floor(Math.random()*16)],
    x: Math.random()*800,
    y: 140 + Math.random()*180,
    dx: (Math.random()-0.5)*2.5+1.5,
    flip: Math.random()<0.5,
    speed: Math.random()*1.2+0.6,
    glow: Math.random()<0.3 ? ["#ff0","#0ff","#f0f"][Math.floor(Math.random()*3)] : null
  });
}
let waveAngle = 0;
let skyColorAngle = 0;
function drawLakeBG() {
  if (!ctx) return;
  let r = Math.floor(180 + Math.sin(skyColorAngle) * 50);
  let g = Math.floor(200 + Math.sin(skyColorAngle + 2) * 55);
  let b = Math.floor(220 + Math.sin(skyColorAngle + 4) * 35);
  let gradSky = ctx.createLinearGradient(0, 0, 0, 120);
  gradSky.addColorStop(0, `rgb(${r}, ${g}, ${b})`);
  gradSky.addColorStop(0.5, "#87cefa");
  gradSky.addColorStop(1, "#ffebcc");
  ctx.fillStyle = gradSky;
  ctx.fillRect(0, 0, 800, 120);
  let gradLake = ctx.createLinearGradient(0, 120, 0, 600);
  gradLake.addColorStop(0, "#87cefa");
  gradLake.addColorStop(0.4, "#40c4ff");
  gradLake.addColorStop(0.7, "#0288d1");
  gradLake.addColorStop(1, "#01579b");
  ctx.fillStyle = gradLake;
  ctx.fillRect(0, 120, 800, 600-120);
  ctx.globalAlpha = 0.2;
  for(let y=140;y<600;y+=25){
    ctx.beginPath();
    let waveShift = Math.sin(y/50 + waveAngle) * 15;
    ctx.arc(800/2-90 + waveShift, y, 230, Math.PI*0.35, Math.PI*0.65, false);
    ctx.arc(800/2+90 + waveShift, y, 230, Math.PI*0.35, Math.PI*0.65, false);
    ctx.strokeStyle = "rgba(255,255,255,0.8)";
    ctx.lineWidth = 6;
    ctx.stroke();
  }
  ctx.globalAlpha = 1.0;
  bgFishList.forEach(f => {
    ctx.save();
    ctx.font = "2.2em serif";
    ctx.globalAlpha = 0.75;
    ctx.translate(f.x, f.y);
    if(f.flip) ctx.scale(-1,1);
    if(f.glow) {
      ctx.shadowColor = f.glow;
      ctx.shadowBlur = 15;
    }
    ctx.fillText(f.emoji, 0, 0);
    ctx.restore();
  });
}
function updateBgFish() {
  bgFishList.forEach(f => {
    f.x += f.dx * f.speed;
    if (f.x < 16) { f.x = 16; f.dx *= -1; f.flip = !f.flip; }
    if (f.x > 800-16) { f.x = 800-16; f.dx *= -1; f.flip = !f.flip; }
    f.y += (Math.random()-0.5)*0.8;
    if(Math.random()<0.01) f.emoji = ["🐟","🐠","🦑","🦀","🐡","🦞","🦐","🐬","🐳","🐋","🦈","🐙","🐚","🦦","🌊","✨"][Math.floor(Math.random()*16)];
  });
  waveAngle += 0.02;
  skyColorAngle += 0.01;
}