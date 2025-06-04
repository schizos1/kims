// sound.js
const sound = {
  bgm: new Audio("/static/minigame/fishing/sound/bgm.mp3"),
  catch: new Audio("/static/minigame/fishing/sound/catch.mp3"),
  reel: new Audio("/static/minigame/fishing/sound/reel.mp3"),
  miss: new Audio("/static/minigame/fishing/sound/miss.mp3"),
  whoosh: new Audio("/static/minigame/fishing/sound/whoosh.mp3"),
  jackpot: new Audio("/static/minigame/fishing/sound/jackpot.mp3"),
  sparkle: new Audio("/static/minigame/fishing/sound/sparkle.mp3"),
  collection: new Audio("/static/minigame/fishing/sound/collection.mp3"),
  new: new Audio("/static/minigame/fishing/sound/new.mp3"),
  complete: new Audio("/static/minigame/fishing/sound/complete.mp3"),
  celebration: new Audio("/static/minigame/fishing/sound/celebration.mp3"),
  record: new Audio("/static/minigame/fishing/sound/record.mp3"),
  highscore: new Audio("/static/minigame/fishing/sound/highscore.mp3"),
  success: new Audio("/static/minigame/fishing/sound/success.mp3"),
  powerup: new Audio("/static/minigame/fishing/sound/powerup.mp3"),
  upgrade: new Audio("/static/minigame/fishing/sound/upgrade.mp3"),
  levelup: new Audio("/static/minigame/fishing/sound/levelup.mp3"),
  evolve: new Audio("/static/minigame/fishing/sound/evolve.mp3"),
  magic: new Audio("/static/minigame/fishing/sound/magic.mp3"),
};
sound.bgm.loop = true;
document.addEventListener('click', () => {
  sound.bgm.volume = 0.17;
  sound.bgm.play().catch(e => console.error("BGM playback failed:", e));
}, {once:true});
function playSound(key) {
  try {
    if (sound[key]) {
      sound[key].currentTime = 0;
      if (key === 'reel') sound[key].volume = 0.6;
      else sound[key].volume = 1.0;
      sound[key].play().catch(e => console.error(`Error playing sound ${key}:`, e));
    } else {
      console.warn(`Sound key not found: ${key}`);
    }
  } catch(e) {
    console.error(`Error playing sound ${key}:`, e);
  }
}