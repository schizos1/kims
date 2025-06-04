// main.js
window.onload = function() {
  if (!canvas || !canvas.getContext) {
    console.error("Canvas not initialized properly");
    alert("Canvas is not supported or not found. Please check your browser.");
    return;
  }
  console.log("Game initializing...");
  renderRodStatus();
  drawFishingRod();
  waitBite();
  renderCollection();
  animate();
};
function animate() {
  updateBoat();
  updateBgFish();
  drawFishingRod();
  requestAnimationFrame(animate);
}
document.getElementById('upgrade-btn').onclick = function() {
  let next = window.rodUpgrades[window.rodLevel+1];
  if (next && (window.score || 0) >= next.need) {
    window.rodLevel++;
    playSound(window.rodUpgrades[window.rodLevel].sound || "upgrade");
    renderRodStatus();
    checkUpgradeSplash();
  }
};
document.getElementById('reset-btn').onclick = function() {
  window.score = 0; window.rodLevel = 0; window.collection = {};
  renderRodStatus(); renderCollection();
};