document.addEventListener('DOMContentLoaded', () => {
  // 악기 설정
  const INSTRUMENTS = {
    piano: { name: "피아노", type: "triangle", color: "#1e90ff", emoji: "🎹" },
    synth: { name: "신스", type: "square", color: "#e17055", emoji: "🎶" },
    marimba: { name: "마림바", type: "sine", color: "#fdcb6e", emoji: "🎵" },
    organ: { name: "오르간", type: "sawtooth", color: "#6c5ce7", emoji: "🎺" },
    bell: { name: "벨", type: "sine", color: "#00b894", emoji: "🔔" }
  };
  let selectedInstrument = "piano";

  // 악기 선택 이벤트
  const selectEl = document.getElementById('instrument-select');
  if (selectEl) {
    selectEl.addEventListener('change', e => {
      selectedInstrument = e.target.value;
    });
  }

  const canvas = document.getElementById('piano-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  // 피아노 건반 설정 (2옥타브)
  const OCTAVES = 2;
  const BASE_NOTES = ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
  const BASE_BLACKS = ['C#', 'D#', '', 'F#', 'G#', 'A#', ''];
  const WHITE_KEYS = [], BLACK_KEYS = [];
  const NOTE_FREQ = {};
  const NOTE_NAME_TO_FREQ = {
    "C4":261.63,  "C#4":277.18, "D4":293.66, "D#4":311.13, "E4":329.63,
    "F4":349.23,  "F#4":369.99, "G4":392.00, "G#4":415.30, "A4":440.00, "A#4":466.16, "B4":493.88,
    "C5":523.25,  "C#5":554.37, "D5":587.33, "D#5":622.25, "E5":659.26,
    "F5":698.46,  "F#5":739.99, "G5":783.99, "G#5":830.61, "A5":880.00, "A#5":932.33, "B5":987.77
  };
  for (let oct = 4; oct < 4 + OCTAVES; oct++) {
    for (let i = 0; i < BASE_NOTES.length; i++) {
      const note = BASE_NOTES[i] + oct;
      WHITE_KEYS.push(note);
      NOTE_FREQ[note] = NOTE_NAME_TO_FREQ[note];
    }
    for (let i = 0; i < BASE_BLACKS.length; i++) {
      if (BASE_BLACKS[i]) {
        const note = BASE_BLACKS[i] + oct;
        BLACK_KEYS.push(note);
        NOTE_FREQ[note] = NOTE_NAME_TO_FREQ[note];
      } else {
        BLACK_KEYS.push('');
      }
    }
  }
  const WHITE_KEY_WIDTH = 76, WHITE_KEY_HEIGHT = 170;
  const BLACK_KEY_WIDTH = 44, BLACK_KEY_HEIGHT = 100;
  const CORNER_RADIUS = 16;
  let whiteKeyRects = [], blackKeyRects = [];
  let audioCtx = null;
  let lastKeyHighlight = null;
  let particles = [];

  // 건반 그리기 함수(동글동글, 파스텔)
  function drawWhiteKey(x, y, w, h, color="#fff", shadow=true) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(x + CORNER_RADIUS, y);
    ctx.lineTo(x + w - CORNER_RADIUS, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + CORNER_RADIUS);
    ctx.lineTo(x + w, y + h - CORNER_RADIUS);
    ctx.quadraticCurveTo(x + w, y + h, x + w - CORNER_RADIUS, y + h);
    ctx.lineTo(x + CORNER_RADIUS, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - CORNER_RADIUS);
    ctx.lineTo(x, y + CORNER_RADIUS);
    ctx.quadraticCurveTo(x, y, x + CORNER_RADIUS, y);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.shadowColor = shadow ? "#b0b7d6" : "rgba(0,0,0,0)";
    ctx.shadowBlur = shadow ? 16 : 0;
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.strokeStyle = "#e3e7ef";
    ctx.lineWidth = 2;
    ctx.stroke();
    // 광택 효과
    ctx.globalAlpha = 0.16;
    ctx.fillStyle = "#fff";
    ctx.beginPath();
    ctx.moveTo(x+6, y+4);
    ctx.quadraticCurveTo(x + w/2, y+16, x + w-6, y+4);
    ctx.lineTo(x + w-6, y+16);
    ctx.quadraticCurveTo(x + w/2, y+10, x+6, y+16);
    ctx.closePath();
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.restore();
  }
  function drawBlackKey(x, y, w, h, color="#24282e", highlight=false) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(x + 9, y);
    ctx.lineTo(x + w - 9, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + 13);
    ctx.lineTo(x + w, y + h - 13);
    ctx.quadraticCurveTo(x + w, y + h, x + w - 9, y + h);
    ctx.lineTo(x + 9, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - 13);
    ctx.lineTo(x, y + 13);
    ctx.quadraticCurveTo(x, y, x + 9, y);
    ctx.closePath();
    ctx.fillStyle = highlight ? INSTRUMENTS[selectedInstrument].color : color;
    ctx.shadowColor = "#888";
    ctx.shadowBlur = highlight ? 14 : 7;
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.globalAlpha = 0.18;
    ctx.fillStyle = "#fff";
    ctx.fillRect(x + 10, y + 5, w - 20, 10);
    ctx.globalAlpha = 1;
    ctx.restore();
  }

  function drawPiano() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // 배경
    ctx.save();
    ctx.fillStyle = "#f7fafc";
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.restore();
    whiteKeyRects = [];
    blackKeyRects = [];
    // 흰 건반
    for (let i = 0; i < WHITE_KEYS.length; i++) {
      let color = (lastKeyHighlight && lastKeyHighlight.idx===i && lastKeyHighlight.type==="white") ?
          INSTRUMENTS[selectedInstrument].color + "22" : "#fff";
      drawWhiteKey(i * WHITE_KEY_WIDTH, 12, WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT, color);
      whiteKeyRects.push({
        note: WHITE_KEYS[i],
        x: i * WHITE_KEY_WIDTH,
        y: 12,
        w: WHITE_KEY_WIDTH,
        h: WHITE_KEY_HEIGHT
      });
    }
    // 검은 건반
    for (let i = 0; i < BLACK_KEYS.length; i++) {
      if (BLACK_KEYS[i] !== '') {
        let x = i * WHITE_KEY_WIDTH + WHITE_KEY_WIDTH - BLACK_KEY_WIDTH/2;
        let highlight = (lastKeyHighlight && lastKeyHighlight.idx===i && lastKeyHighlight.type==="black");
        drawBlackKey(x, 12, BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT, "#212c35", highlight);
        blackKeyRects.push({
          note: BLACK_KEYS[i],
          x: x,
          y: 12,
          w: BLACK_KEY_WIDTH,
          h: BLACK_KEY_HEIGHT
        });
      } else {
        blackKeyRects.push(null);
      }
    }
    // 파티클(이펙트)
    drawParticles();
  }

  // 재미있는 파티클 이펙트: 별/이모지/원 랜덤
  function addParticle(x, y) {
    let effect = Math.random();
    let emoji = INSTRUMENTS[selectedInstrument].emoji;
    if (effect < 0.33) {
      particles.push({type:'emoji', emoji, x, y, vy: -1.7 - Math.random(), life: 26, alpha: 1, size: 32});
    } else if (effect < 0.66) {
      particles.push({type:'star', x, y, vy: -2.2, life: 20, alpha: 1, color: INSTRUMENTS[selectedInstrument].color});
    } else {
      particles.push({type:'circle', x, y, vy: -1.5, life: 18, alpha: 1, color: INSTRUMENTS[selectedInstrument].color, r: 13+10*Math.random()});
    }
  }
  function drawParticles() {
    for (let p of particles) {
      ctx.save();
      ctx.globalAlpha = p.alpha;
      if (p.type === 'emoji') {
        ctx.font = `${p.size}px serif`;
        ctx.textAlign = "center";
        ctx.fillText(p.emoji, p.x, p.y);
      } else if (p.type === 'star') {
        ctx.strokeStyle = p.color;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        for(let i=0; i<5; i++){
          let angle = Math.PI*2*i/5 - Math.PI/2;
          let x1 = p.x + 13*Math.cos(angle);
          let y1 = p.y + 13*Math.sin(angle);
          ctx.lineTo(x1, y1);
        }
        ctx.closePath();
        ctx.stroke();
      } else if (p.type === 'circle') {
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
        ctx.fill();
      }
      ctx.restore();
    }
  }

  function stepParticles() {
    for (let p of particles) {
      p.y += p.vy;
      p.life--;
      p.alpha *= 0.94;
      if (p.type==='star') p.alpha *= 0.95;
    }
    particles = particles.filter(p => p.life > 0 && p.alpha > 0.05);
  }
  function animate() {
    stepParticles();
    drawPiano();
    requestAnimationFrame(animate);
  }
  animate();

  // 오디오 재생 (악기별)
  function playNote(note) {
    if (!audioCtx)
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const freq = NOTE_FREQ[note];
    if (!freq) return;
    const inst = INSTRUMENTS[selectedInstrument];
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = inst.type;
    osc.frequency.value = freq;
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    // 음색별 볼륨/릴리즈 커스텀
    let vol = 0.4;
    let duration = 0.46;
    if (selectedInstrument === "bell") { vol = 0.27; duration = 0.27; }
    if (selectedInstrument === "organ") { vol = 0.38; duration = 0.75; }
    if (selectedInstrument === "marimba") { vol = 0.3; duration = 0.24; }

    gain.gain.setValueAtTime(vol, audioCtx.currentTime);
    osc.start();
    gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + duration);
    osc.stop(audioCtx.currentTime + duration);

    // 사운드가 끊기면 WebAudio API 버그 대응
    setTimeout(()=>{try{osc.disconnect();gain.disconnect();}catch{}}, (duration+0.1)*1000);
  }

  function highlightKey(idx, type, px, py) {
    lastKeyHighlight = {idx, type};
    addParticle(px, py-24);
    drawPiano();
    setTimeout(() => { lastKeyHighlight = null; drawPiano(); }, 110);
  }

  // 이벤트(마우스/터치)
  canvas.addEventListener('mousedown', e => {
    const {offsetX: x, offsetY: y} = e;
    for (let i=0; i<blackKeyRects.length; i++) {
      let key = blackKeyRects[i];
      if (key && x >= key.x && x < key.x + key.w && y >= key.y && y < key.y + key.h) {
        playNote(key.note); highlightKey(i, "black", x, y); return;
      }
    }
    for (let i=0; i<whiteKeyRects.length; i++) {
      let key = whiteKeyRects[i];
      if (x >= key.x && x < key.x + key.w && y >= key.y && y < key.y + key.h) {
        playNote(key.note); highlightKey(i, "white", x, y); return;
      }
    }
  });

  canvas.addEventListener('touchstart', e => {
    const rect = canvas.getBoundingClientRect();
    const touch = e.touches[0];
    const x = touch.clientX - rect.left;
    const y = touch.clientY - rect.top;
    for (let i=0; i<blackKeyRects.length; i++) {
      let key = blackKeyRects[i];
      if (key && x >= key.x && x < key.x + key.w && y >= key.y && y < key.y + key.h) {
        playNote(key.note); highlightKey(i, "black", x, y); return;
      }
    }
    for (let i=0; i<whiteKeyRects.length; i++) {
      let key = whiteKeyRects[i];
      if (x >= key.x && x < key.x + key.w && y >= key.y && y < key.y + key.h) {
        playNote(key.note); highlightKey(i, "white", x, y); return;
      }
    }
  });
});
