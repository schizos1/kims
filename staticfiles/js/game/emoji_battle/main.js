// static/js/games/emoji_battle/main.js

console.log("emoji_battle main.js loaded");
alert("main.js loaded!");

// ====== Pixi.js 기본 세팅 ======
const app = new PIXI.Application({ width: 800, height: 600, backgroundColor: 0x282828 });
const canvasEl = document.getElementById('emoji-canvas');
app.view.id = "emoji-canvas"; // id 유지
canvasEl.parentNode.replaceChild(app.view, canvasEl);

// === 데모용: 노란 사각형 하나 그려보기 ===
const gfx = new PIXI.Graphics();
gfx.beginFill(0xffcc00);
gfx.drawRect(100, 100, 120, 120);
gfx.endFill();
app.stage.addChild(gfx);

// ====== 사운드(Howler.js) ======
const throwSound = new Howl({ src: ['/static/sound/throw.mp3'] });
const hitSound = new Howl({ src: ['/static/sound/hit.mp3'] });

// ====== Socket.IO 연결 ======
const socket = io();
let myId = null;
let myX = 400;
const MOVE_STEP = 20;
const fieldWidth = 800;

// ====== 서버 이벤트 핸들러 ======
socket.on('connect', () => {
    console.log("[소켓] 연결 성공:", socket.id);
});

socket.on('emoji_start', data => {
    myId = socket.id;
    document.getElementById('emoji-msg').textContent = "게임 시작!";
    // 예시: 시작 위치에 표시 (원한다면 추가 구현)
    console.log('emoji_start 데이터:', data);
});

socket.on('emoji_thrown', data => {
    throwSound.play();
    // Pixi.js로 이모지 투척 연출 구현할 자리!
    console.log('emoji_thrown:', data);
});

socket.on('emoji_hit', data => {
    hitSound.play();
    // 적중 연출 추가 가능
    document.getElementById('emoji-msg').textContent = "명중!";
    console.log('emoji_hit:', data);
});

socket.on('emoji_move', data => {
    if (data.id !== myId) {
        // 상대방 위치 업데이트
        console.log(`상대 ${data.id} 이동: ${data.x}`);
    }
});

socket.on('emoji_game_over', data => {
    document.getElementById('emoji-msg').textContent = (data.winner === myId)
        ? "🎉 승리!" : "😢 패배!";
    console.log('게임 종료:', data);
});

socket.on('emoji_player_left', data => {
    document.getElementById('emoji-msg').textContent = "상대가 나갔습니다.";
});

// ====== 키 입력 이벤트 ======
document.addEventListener('keydown', (e) => {
    if (e.code === 'ArrowLeft') {
        myX = Math.max(0, myX - MOVE_STEP);
        socket.emit('emoji_move', { x: myX });
    } else if (e.code === 'ArrowRight') {
        myX = Math.min(fieldWidth, myX + MOVE_STEP);
        socket.emit('emoji_move', { x: myX });
    } else if (e.code === 'Space') {
        const emojis = ['🥶', '❄️', '🍌', '💖'];
        const rand = emojis[Math.floor(Math.random() * emojis.length)];
        sendThrow(rand);
    }
});

// ====== 함수 ======
function sendThrow(emoji) {
    socket.emit('emoji_throw', { emoji });
}

function reportHit(targetId, emoji) {
    socket.emit('emoji_hit', { target: targetId, emoji });
}

// ====== 최초 진입 안내 메시지 ======
document.getElementById('emoji-msg').textContent = "다른 플레이어가 입장하면 게임이 시작됩니다.";

// ====== 예시: Pixi.js에서 이모지나 플레이어 그리기는 추후 추가 가능 ======
// (아직은 노란 사각형으로 기본 테스트, 실제 게임 로직은 이벤트에 따라 구현)

