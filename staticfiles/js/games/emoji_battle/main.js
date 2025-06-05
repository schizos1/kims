// static/js/games/emoji_battle/main.js
// Pixi.js와 Howler.js를 사용한 간단한 클라이언트 로직 (개요)

const app = new PIXI.Application({ width: 800, height: 600 });
document.getElementById('emoji-canvas').replaceWith(app.view);

const throwSound = new Howl({ src: ['/static/sound/throw.mp3'] });
const hitSound = new Howl({ src: ['/static/sound/hit.mp3'] });

const socket = io();
let myId = null;

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
