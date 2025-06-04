// rod.js
let boatX = 800/2, boatDir = 1, boatSpeed = 2.2, boatY = 600-38, boatEmoji = '🦦';
let bobberAngle = 0;
function drawFishingRod(highlight, x, y) {
  drawLakeBG();
  if (!ctx) return;
  ctx.font = '44px serif'; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(boatEmoji, boatX, boatY);
  ctx.strokeStyle = "#888"; ctx.lineWidth = 4;
  ctx.beginPath();
  let lineStartY = window.isReeling ? boatY - 18 - window.reelProgress * (boatY - 108) : boatY - 18;
  ctx.moveTo(boatX, lineStartY); ctx.lineTo(boatX, 90); ctx.stroke();
  let isHot = window.isBiting;
  let arcR = isHot ? 62 + Math.sin(bobberAngle) * 5 : 36 + Math.sin(bobberAngle) * 3;
  let fontSize = isHot ? 74 + Math.sin(bobberAngle) * 6 : 42 + Math.sin(bobberAngle) * 4;
  let glow = isHot ? "0 0 20px #f33, 0 0 38px #ff8282, 0 0 24px #ff3030" : "0 0 8px #d1a, 0 0 2px #fff";
  if (isHot) {
    ctx.save();
    ctx.beginPath();
    ctx.arc(boatX, 103, arcR, 0, 2*Math.PI);
    ctx.fillStyle = "rgba(255,44,44,0.34)";
    ctx.shadowColor = "#f44";
    ctx.shadowBlur = 25;
    ctx.fill();
    ctx.restore();
  }
  ctx.save();
  ctx.font = "28px serif";
  ctx.fillStyle = "#555";
  ctx.fillText('⛵', boatX, 120);
  ctx.restore();
  ctx.save();
  ctx.font = `${fontSize}px serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.shadowColor = isHot ? "#ff2b2b" : "#f7bc82";
  ctx.shadowBlur = isHot ? 33 : 9;
  ctx.fillStyle = isHot ? "#ff3030" : "#ffb000";
  let fishY = window.isReeling ? boatY - window.reelProgress * (boatY - 90) : 90 + (isHot?15:0);
  ctx.fillText(window.isReeling && window.caughtFish ? window.caughtFish.emoji : '🟠', boatX, fishY);
  ctx.restore();
  ctx.font = "32px serif";
  ctx.fillStyle = "#333";
  let waveOffset = Math.sin(waveAngle) * 10;
  ctx.fillText('🌊🌊🌊🌊🌊', 800/2-70 + waveOffset, 118);
  if (highlight && x && y) {
    ctx.font = "24px serif"; ctx.fillStyle = "#f33";
    ctx.fillText("✖️", x, y-12); ctx.fillStyle = "#333";
  }
  if (isHot) {
    ctx.font = 'bold 27px sans-serif'; ctx.fillStyle = '#ff6600';
    ctx.shadowColor = "#fff"; ctx.shadowBlur = 5;
    ctx.fillText('터치!', boatX, 50);
    ctx.shadowBlur = 0;
    ctx.fillStyle = "#333";
  }
  if (window.missMessage && !window.isReeling) {
    showMissSplash(window.missMessage);
    window.missMessage = null;
  }
  bobberAngle += 0.1;
  if (window.isReeling) {
    window.reelProgress += 0.008;
    if (window.reelProgress > 1) window.reelProgress = 1;
  }
}
function updateBoat() {
  boatSpeed = 1.4 + window.rodLevel*0.37 + Math.floor(window.score/300)*0.19;
  boatX += boatSpeed * boatDir;
  if (boatX < 80) { boatX = 80; boatDir = 1; }
  if (boatX > 800-80) { boatX = 800-80; boatDir = -1; }
}
function renderRodStatus() {
  const scoreElement = document.getElementById('score');
  if (scoreElement) {
    scoreElement.innerText = (window.score || 0) + " pt";
  } else {
    console.error("Score element not found");
  }
  const rodElement = document.getElementById('rod');
  if (rodElement) {
    rodElement.innerText = window.rodUpgrades[window.rodLevel].emoji + " " + window.rodUpgrades[window.rodLevel].name;
  } else {
    console.error("Rod element not found");
  }
}