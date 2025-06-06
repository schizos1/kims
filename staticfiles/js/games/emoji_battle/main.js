// static/js/games/emoji_battle/main.js
// Pixi.js와 Howler.js를 사용한 간단한 클라이언트 로직 (개요)

const app = new PIXI.Application({ width: 800, height: 600 });
document.getElementById('emoji-canvas').replaceWith(app.view);

const throwSound = new Howl({ src: ['/static/sound/throw.mp3'] });
const hitSound = new Howl({ src: ['/static/sound/hit.mp3'] });

const socket = io();
let myId = null;
let myX = 400;
const MOVE_STEP = 20;
const fieldWidth = 800;

socket.on('emoji_start', data => {
    myId = socket.id;
});

socket.on('emoji_thrown', data => {
    throwSound.play();
});

socket.on('emoji_hit', data => {
    hitSound.play();
});

function sendThrow(emoji) {
    socket.emit('emoji_throw', { emoji });
}

function reportHit(targetId, emoji) {
    socket.emit('emoji_hit', { target: targetId, emoji });
}

socket.on('emoji_move', data => {
    if (data.id !== myId) {
        // TODO: 상대방 위치 업데이트 (간단한 데모에서는 로그만)
        console.log(`Player ${data.id} moved to ${data.x}`);
    }
});

document.addEventListener('keydown', (e) => {
    if (e.code === 'ArrowLeft') {
        myX = Math.max(0, myX - MOVE_STEP);
        socket.emit('emoji_move', { x: myX });
    } else if (e.code === 'ArrowRight') {
        myX = Math.min(fieldWidth, myX + MOVE_STEP);
        socket.emit('emoji_move', { x: myX });
    } else if (e.code === 'Space') {
        const emojis = ['ice', 'snow', 'banana', 'heart'];
        const rand = emojis[Math.floor(Math.random() * emojis.length)];
        sendThrow(rand);
    }
});

