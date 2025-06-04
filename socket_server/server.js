// socket_server/server.js
// 메인 Node.js 서버 (Express + Socket.IO) - 모듈화된 게임 핸들러 구조

import express from 'express';
import http from 'http';
import { Server as SocketIOServer } from 'socket.io';
import path from 'path';
import { fileURLToPath } from 'url';

// 'eat_food' 게임 핸들러 import
import initializeEatFoodGameHandler from './game_handlers/eat_food_game_handler.js';

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

const PORT = process.env.PORT || 3001; // 이전과 동일하게 3001번 포트 사용

// --- 정적 파일 제공 설정 ---
// 1. public 폴더 (HTML 파일 등 클라이언트가 직접 접근하는 파일)
// socket_server/public 디렉토리를 루트 URL ('/')로 제공
app.use(express.static(path.join(__dirname, 'public')));
console.log(`Serving static files from: ${path.join(__dirname, 'public')} at /`);


// 2. Django의 static 폴더와 유사한 역할 (클라이언트 JS, CSS, 이미지 등)
// /static URL 경로로 요청이 오면, 사용자님의 Django 프로젝트 내 static 폴더에서 파일을 찾음
// 사용자님의 경로: /home/schizos/study_site/minigame/static/
// __dirname 은 현재 socket_server 폴더입니다.
// socket_server 폴더에서 study_site/minigame/static 폴더까지의 상대 경로를 정확히 지정해야 합니다.
// 예: socket_server가 study_site의 하위 폴더라면 '..'을 사용하여 상위로 이동합니다.
// /home/schizos/study_site/socket_server -> /home/schizos/study_site -> /home/schizos/study_site/minigame/static
const djangoStaticPath = path.join(__dirname, '..', 'minigame', 'static'); // 경로 확인 및 수정 필요!
app.use('/static', express.static(djangoStaticPath));
console.log(`Serving Django static files from: ${djangoStaticPath} at /static`);


// --- HTML 페이지 라우팅 (선택 사항) ---
// 클라이언트가 특정 URL로 접속 시 해당 HTML 파일을 보내줍니다.
// Django 템플릿을 직접 사용하는 것이 아니므로, Node.js가 서비스할 HTML 파일이 public 폴더에 있어야 합니다.
// 예시: /play-single 로 접속 시 public/single_eat_food.html 제공
app.get('/play-single-eat-food', (req, res) => {
    // 이전에 만들어둔 싱글플레이어용 HTML 파일 이름으로 변경해주세요.
    // 예: single_player_game.html 또는 single_eat_food.html
    res.sendFile(path.join(__dirname, 'public', 'single_player_game.html'));
});

app.get('/play-multi-eat-food', (req, res) => {
    // 멀티플레이어용 HTML 파일 이름으로 변경해주세요.
    res.sendFile(path.join(__dirname, 'public', 'multi_player_game.html'));
});


// --- Socket.IO 연결 처리 ---
io.on('connection', (socket) => {
    console.log(`[MainServer] New client connected: ${socket.id}`);

    // 'eat_food' 게임 관련 이벤트 처리를 전용 핸들러에 위임
    // initializeEatFoodGameHandler는 export default 함수이므로 바로 호출
    initializeEatFoodGameHandler(io, socket);

    // 만약 다른 게임(예: 'another_game')이 있다면, 해당 게임의 핸들러도 유사하게 호출
    // socket.on('request_game_type', (gameType) => {
    //     if (gameType === 'eat_food') {
    //         initializeEatFoodGameHandler(io, socket);
    //     } else if (gameType === 'another_game') {
    //         // initializeAnotherGameHandler(io, socket);
    //     }
    // });

    // server.js 레벨의 공통 disconnect 처리는 game_handler 내부의 disconnect가 우선 처리된 후 필요시 수행
    // 현재 eat_food_game_handler.js 에서 disconnect를 이미 처리하고 있으므로,
    // 여기서는 추가적인 공통 정리 작업이 필요할 때만 로직을 추가합니다.
    // socket.on('disconnect', (reason) => {
    //     console.log(`[MainServer] Client ${socket.id} disconnected (handled by main server if needed). Reason: ${reason}`);
    // });

    socket.on('error', (error) => {
        console.error(`[MainServer] Socket error from ${socket.id}:`, error);
    });
});

server.listen(PORT, () => {
    console.log(`🚀 Game Server (Node.js) is running on http://localhost:${PORT}`);
    console.log(`Access single player game (example): http://localhost:${PORT}/play-single-eat-food`);
});
