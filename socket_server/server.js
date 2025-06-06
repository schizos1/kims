// socket_server/server.js
// 메인 Node.js 서버 (Express + Socket.IO) - 네임스페이스 사용으로 수정

import express from 'express';
import http from 'http';
import { Server as SocketIOServer } from 'socket.io';
import path from 'path';
import { fileURLToPath } from 'url';

// 게임 핸들러 import
import initializeEatFoodGameHandler from './game_handlers/eat_food_game_handler.js';
import initializeFishingGameHandler from './game_handlers/fishing_game_handler.js';
import initializeEmojiBattleHandler from './game_handlers/emoji_battle_game_handler.js';

// import { userPoints as eatFoodUserPoints } from './game_logics/eat_food/multi_game_session.js'; // 필요시 해당 핸들러 내부 또는 다른 방식으로 관리
// import { userPoints as globalUserPoints } from './game_logics/user_points.js'; // 필요시 해당 핸들러 내부 또는 다른 방식으로 관리

// ES 모듈 환경에서 __dirname, __filename 설정
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = http.createServer(app);
const io = new SocketIOServer(server, {
    cors: {
        origin: "*", // 실제 배포 시에는 특정 도메인으로 제한하는 것이 좋습니다.
        methods: ["GET", "POST"]
    }
});

const PORT = process.env.PORT || 3001;

// 간단한 포인트 조회 API (이 부분은 userPoints 임포트 방식에 따라 달라질 수 있음)
// app.get('/points/:id', (req, res) => {
//     const id = req.params.id;
//     // res.json({ id, points: globalUserPoints.get(id) || 0 }); // 어떤 userPoints를 사용할지 결정 필요
//     res.json({ id, points: 0 }); // 임시 응답
// });

// --- 정적 파일 제공 설정 ---
app.use(express.static(path.join(__dirname, 'public')));
console.log(`Serving static files from: ${path.join(__dirname, 'public')} at /`);

const djangoStaticPath = path.join(__dirname, '..', 'minigame', 'static');
app.use('/static', express.static(djangoStaticPath));
console.log(`Serving Django static files from: ${djangoStaticPath} at /static`);


// --- HTML 페이지 라우팅 (선택 사항, 기존과 동일) ---
app.get('/play-single-eat-food', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'single_player_game.html'));
});

app.get('/play-multi-eat-food', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'multi_player_game.html'));
});
// 이모지 배틀 게임을 위한 HTML 라우팅 예시 (public 폴더에 해당 파일이 있다고 가정)
app.get('/play-emoji-battle', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'emoji_battle_page.html')); // 실제 HTML 파일명으로 변경
});


// --- Socket.IO 네임스페이스 설정 및 연결 처리 ---
const emojiBattleNamespace = io.of('/emoji-battle');
const eatFoodNamespace = io.of('/eat-food');
const fishingNamespace = io.of('/fishing'); // 예시

console.log("Socket.IO Namespaces configured: /emoji-battle, /eat-food, /fishing");

// 이모지 배틀 게임 네임스페이스 (/emoji-battle)
emojiBattleNamespace.on('connection', (socket) => {
    console.log(`[EmojiBattleNamespace] Client ${socket.id} connected.`);
    // EmojiBattle 핸들러 초기화 시, 해당 네임스페이스(emojiBattleNamespace) 객체를 전달합니다.
    initializeEmojiBattleHandler(emojiBattleNamespace, socket);

    socket.on('error', (error) => {
        console.error(`[EmojiBattleNamespace] Socket error from ${socket.id}:`, error);
    });
    // disconnect는 initializeEmojiBattleHandler 내부에서 이미 처리하고 있으므로 여기서는 생략 가능
});

// 먹이 먹기 게임 네임스페이스 (/eat-food)
eatFoodNamespace.on('connection', (socket) => {
    console.log(`[EatFoodNamespace] Client ${socket.id} connected.`);
    initializeEatFoodGameHandler(eatFoodNamespace, socket);

    socket.on('error', (error) => {
        console.error(`[EatFoodNamespace] Socket error from ${socket.id}:`, error);
    });
});

// 낚시 게임 네임스페이스 (/fishing) - 예시
fishingNamespace.on('connection', (socket) => {
    console.log(`[FishingNamespace] Client ${socket.id} connected.`);
    initializeFishingGameHandler(fishingNamespace, socket);

    socket.on('error', (error) => {
        console.error(`[FishingNamespace] Socket error from ${socket.id}:`, error);
    });
});

// 이전의 기본 네임스페이스 핸들러는 주석 처리 또는 삭제
/*
io.on('connection', (socket) => {
    console.log(`[MainServer] New client connected: ${socket.id} (This default handler is now disabled)`);
    // initializeEatFoodGameHandler(io, socket); // 네임스페이스로 이동됨
    // initializeFishingGameHandler(io, socket); // 네임스페이스로 이동됨
    // initializeEmojiBattleHandler(io, socket); // 네임스페이스로 이동됨
    socket.on('error', (error) => {
        console.error(`[MainServer] Socket error from ${socket.id}:`, error);
    });
});
*/

server.listen(PORT, () => {
    console.log(`🚀 Game Server (Node.js) is running on http://localhost:${PORT}`);
    console.log(`➡️  Emoji Battle available on namespace: http://localhost:${PORT}/emoji-battle`);
    console.log(`➡️  Eat Food available on namespace: http://localhost:${PORT}/eat-food`);
    console.log(`➡️  Fishing available on namespace: http://localhost:${PORT}/fishing`);
    // console.log(`Access single player game (example): http://localhost:${PORT}/play-single-eat-food`);
});