// socket_server/server.js
// 메인 Node.js 서버 (Express + Socket.IO) - 네임스페이스 사용

import express from 'express';
import http from 'http';
import { Server as SocketIOServer } from 'socket.io';
import path from 'path';
import { fileURLToPath } from 'url';

// 게임 핸들러 import
import initializeEatFoodGameHandler from './game_handlers/eat_food_game_handler.js';
import initializeFishingGameHandler from './game_handlers/fishing_game_handler.js';
import initializeEmojiBattleHandler from './game_handlers/emoji_battle_game_handler.js';
import initializeMonopolyGameHandler from './game_handlers/monopoly_game_handler.js';

// ES 모듈 환경에서 __dirname, __filename 설정
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = http.createServer(app);
const io = new SocketIOServer(server, {
    cors: {
        origin: "*", // 실제 배포 시 특정 도메인 제한 권장
        methods: ["GET", "POST"]
    }
});

const PORT = process.env.PORT || 3000; // 포트 3001 -> 3000

// --- 정적 파일 제공 설정 ---
app.use(express.static(path.join(__dirname, 'public')));
console.log(`Serving static files from: ${path.join(__dirname, 'public')} at /`);

const djangoStaticPath = path.join(__dirname, '..', 'minigame', 'static');
app.use('/static', express.static(djangoStaticPath));
console.log(`Serving Django static files from: ${djangoStaticPath} at /static`);

// --- HTML 페이지 라우팅 ---
app.get('/play-single-eat-food', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'single_player_game.html'));
});

app.get('/play-multi-eat-food', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'multi_player_game.html'));
});

app.get('/play-emoji-battle', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'emoji_battle_page.html'));
});

// --- Socket.IO 네임스페이스 설정 ---
const emojiBattleNamespace = io.of('/emoji-battle');
const eatFoodNamespace = io.of('/eat-food');
const fishingNamespace = io.of('/fishing');
const monopolyNamespace = io.of('/monopoly'); // 모노폴리 네임스페이스 추가

console.log("Socket.IO Namespaces configured: /emoji-battle, /eat-food, /fishing, /monopoly");

// 이모지 배틀 네임스페이스
emojiBattleNamespace.on('connection', (socket) => {
    console.log(`[EmojiBattleNamespace] Client ${socket.id} connected.`);
    initializeEmojiBattleHandler(emojiBattleNamespace, socket);
    socket.on('error', (error) => {
        console.error(`[EmojiBattleNamespace] Socket error from ${socket.id}:`, error);
    });
});

// 먹이 먹기 네임스페이스
eatFoodNamespace.on('connection', (socket) => {
    console.log(`[EatFoodNamespace] Client ${socket.id} connected.`);
    initializeEatFoodGameHandler(eatFoodNamespace, socket);
    socket.on('error', (error) => {
        console.error(`[EatFoodNamespace] Socket error from ${socket.id}:`, error);
    });
});

// 낚시 네임스페이스
fishingNamespace.on('connection', (socket) => {
    console.log(`[FishingNamespace] Client ${socket.id} connected.`);
    initializeFishingGameHandler(fishingNamespace, socket);
    socket.on('error', (error) => {
        console.error(`[FishingNamespace] Socket error from ${socket.id}:`, error);
    });
});

// 모노폴리 네임스페이스
monopolyNamespace.on('connection', (socket) => {
    console.log(`[MonopolyNamespace] Client ${socket.id} connected.`);
    initializeMonopolyGameHandler(monopolyNamespace, socket);
    socket.on('error', (error) => {
        console.error(`[MonopolyNamespace] Socket error from ${socket.id}:`, error);
    });
});

server.listen(PORT, () => {
    console.log(`🚀 Game Server (Node.js) is running on http://localhost:${PORT}`);
    console.log(`➡️  Emoji Battle available on namespace: http://localhost:${PORT}/emoji-battle`);
    console.log(`➡️  Eat Food available on namespace: http://localhost:${PORT}/eat-food`);
    console.log(`➡️  Fishing available on namespace: http://localhost:${PORT}/fishing`);
    console.log(`➡️  Monopoly available on namespace: http://localhost:${PORT}/monopoly`);
});