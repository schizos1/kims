// static/minigame/js/eat_food_multi.js
// 'eat_food' 게임의 멀티플레이어 모드 전용 JavaScript 로직입니다.
// 서버의 MultiPlayerGameConsumer와 WebSocket 통신을 담당합니다.
// eat_food_common.js가 먼저 로드되어야 합니다.

let ws_multi = null; // 멀티플레이어용 WebSocket 객체
let gameLoopInterval_multi = null; // 멀티플레이어 게임 루프 인터벌
let currentRoomId_multi = null; // 현재 접속한 방 ID

// --- 멀티플레이어 게임 시작 함수 ---
// roomId는 로비나 다른 페이지에서 전달받아야 합니다.
function startGame_multi(roomId) {
    if (!assetsLoaded) { // common.js 변수
        updateSystemMessage("아직 에셋 로딩 중입니다...", true);
        return;
    }
    if (gamePlaying) { // common.js 변수
        console.log("게임이 이미 진행 중입니다. (멀티)");
        // 기존 연결이 있다면 정리 후 새로 시작할지, 아니면 막을지 정책 결정 필요
        // 여기서는 간단히 중복 실행 방지
        if (currentRoomId_multi === roomId && ws_multi && ws_multi.readyState === WebSocket.OPEN) {
            updateSystemMessage("이미 해당 방에 참여 중입니다.", false);
            return;
        }
    }

    currentRoomId_multi = roomId;
    updateSystemMessage(`멀티플레이어 게임 (방: ${roomId}) 시작 준비 중...`, false);

    // UI 초기화 (common.js 함수 사용)
    if (scoreNum) scoreNum.innerText = "0";
    if (foodLeftNum && totalFoodsToWin) foodLeftNum.innerText = totalFoodsToWin.toString();
    if (progressBar) progressBar.style.width = "0%";
    if (resultPopup) resultPopup.style.display = "none";

    // 플레이어 기본 상태 초기화 (common.js의 player 객체 사용)
    player.score = 0;
    player.eatCount = 0;
    player.eating = false;
    player.user = usernameInput.value || `Player_${generateFallbackUUID().substring(0,4)}`;
    
    if (loadedDinoImages && loadedDinoImages.length > 0) {
        let randomIdx = Math.floor(Math.random() * loadedDinoImages.length);
        if (loadedDinoImages[randomIdx]?.complete && loadedDinoImages[randomIdx]?.naturalWidth > 0) {
            player.charImg = loadedDinoImages[randomIdx];
            player.charImgPath = DINO_IMG_PATHS[randomIdx];
        } else {
            player.charImg = loadedDinoImages[0];
            player.charImgPath = DINO_IMG_PATHS[0];
            console.warn("선택된 플레이어 이미지가 유효하지 않아 기본 이미지로 설정됨 (멀티)");
        }
    } else {
        console.error("로드된 플레이어 이미지가 없습니다. (멀티)");
        player.charImgPath = DINO_IMG_PATHS[0];
    }
    
    foods = [];
    npcPlayers = [];
    obstacles = [];
    opponentPlayer = null; // 상대방 정보 초기화

    // WebSocket 연결 설정
    const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    // 멀티플레이어용 WebSocket URL (라우팅 설정에 맞게)
    const wsUrl_multi = wsProtocol + window.location.host + `/ws/minigame/games/eat_food/multi/${roomId}/`; 
    
    console.log("멀티플레이어 WebSocket 연결 시도 중:", wsUrl_multi);
    updateSystemMessage(`서버에 연결 중 (방: ${roomId})...`);

    if (ws_multi && (ws_multi.readyState === WebSocket.OPEN || ws_multi.readyState === WebSocket.CONNECTING)) {
        ws_multi.close();
        console.log("기존 멀티플레이어 WebSocket 연결 닫는 중...");
    }
    ws_multi = new WebSocket(wsUrl_multi);

    ws_multi.onopen = () => {
        console.log(`멀티플레이어 WebSocket 연결 성공! (방: ${roomId})`);
        updateSystemMessage("서버 연결 성공! 게임 참여 요청 중...", false);
        ws_multi.send(JSON.stringify({
            action: "join",
            user: player.user,
            charImgPath: player.charImgPath
        }));
    };

    ws_multi.onmessage = handleServerMessage_multi;

    ws_multi.onclose = (event) => {
        console.log(`멀티플레이어 WebSocket 연결 종료됨 (방: ${roomId}).`, event.reason, `Code: ${event.code}`);
        updateSystemMessage(`서버 연결 끊김 (방: ${roomId}). 문제가 지속되면 페이지를 새로고침하세요.`, true);
        gamePlaying = false;
        if (gameLoopInterval_multi) { clearInterval(gameLoopInterval_multi); gameLoopInterval_multi = null; }
    };

    ws_multi.onerror = (error) => {
        console.error(`멀티플레이어 WebSocket 오류 발생 (방: ${roomId}):`, error);
        updateSystemMessage("WebSocket 연결 오류. 서버 상태를 확인하거나 잠시 후 다시 시도해주세요.", true);
        gamePlaying = false;
        if (gameLoopInterval_multi) { clearInterval(gameLoopInterval_multi); gameLoopInterval_multi = null; }
    };
}

// --- 서버 메시지 처리 함수 (멀티플레이어용) ---
function handleServerMessage_multi(event) {
    // console.log("DEBUG (Client Multi): Received message from server:", event.data);
    const data = JSON.parse(event.data);
    // console.log("DEBUG (Client Multi): Parsed data:", data);

    switch (data.action) {
        case "connection_established":
            updateSystemMessage(data.message, false);
            break;
        case "game_start_info":
            console.log("DEBUG (Client Multi): Received game_start_info:", data);
            // 서버에서 전체 게임 상태 (모든 플레이어, 음식, NPC, 장애물)를 받음
            if (data.players && data.players.length > 0) {
                // 현재 클라이언트의 플레이어 정보 업데이트
                const myPlayerData = data.players.find(p => p.id === ws_multi.url.split('/')[ws_multi.url.split('/').length-2] || p.user === player.user); // 서버에서 id를 channel_name으로 준다면
                // 실제로는 join 응답이나, 초기 state에서 자신의 고유 ID를 받아 저장해두고 비교해야 함.
                // 여기서는 임시로 user 이름으로 구분하거나, 서버가 player.id를 채널명으로 보내준다고 가정
                // SinglePlayerConsumer의 경우 player.id = self.channel_name 이었음. Multi에서는 서버가 players 리스트에 각자 id를 줄 것.
                // 임시로, join 시 보낸 유저 이름으로 식별. 서버에서 channel_name 기반의 id를 내려주는게 더 정확.
                // 혹은, 서버가 state_update 시 'my_player_data' 와 'other_players_data'를 구분해서 주는 것도 방법.

                // 우선은 현재 player 객체에 서버 데이터 할당 (플레이어 식별 로직 필요)
                // 이 부분은 서버의 응답에 따라 플레이어 식별 방법을 명확히 해야 함.
                // 여기서는 첫번째 플레이어를 '나'라고 가정하거나, 서버가 'player' 필드에 '나'의 정보를,
                // 'opponents' 필드에 다른 플레이어 정보를 주는 것을 기대할 수 있음.
                // 현재 broadcast_game_start_info는 'players_in_game'으로 모든 플레이어 리스트를 줌.
                // 이 리스트에서 '나'와 '상대'를 구분해야 함.
                
                // 서버에서 내려온 players_in_game에서 현재 클라이언트의 플레이어 객체 찾기
                // channel_name은 클라이언트가 알 수 없으므로, join 시 보낸 user 이름이나 서버가 부여한 id로 찾아야 함.
                // 여기서는 game_start_info에 포함된 player.id (서버의 channel_name)를 클라이언트가 모른다는 가정 하에
                // User 이름으로 찾거나, 서버가 첫번째 player 객체를 현재 클라이언트에게 맞춰 보내준다고 가정.
                // 더 좋은 방법: join 응답으로 player.id (channel_name)를 받고 저장해둔다.

                let foundSelf = false;
                data.players_in_game.forEach(p_data => {
                    if (p_data.user === player.user) { // 가장 간단한 방법 (유저 이름 중복 없어야 함)
                        player.id = p_data.id; // 서버가 준 ID (channel_name) 저장
                        player.x = p_data.x;
                        player.y = p_data.y;
                        player.score = p_data.score;
                        player.eatCount = p_data.eatCount;
                        // charImgPath는 join 시 보낸 것이므로, 서버가 변경하지 않았다면 유지.
                        foundSelf = true;
                    } else {
                        // 첫번째 '다른' 플레이어를 opponentPlayer로 설정 (2인 게임 가정)
                        if (!opponentPlayer) {
                            opponentPlayer = { user: p_data.user, x: p_data.x, y: p_data.y, score: p_data.score, charImgPath: p_data.charImgPath };
                            // 상대방 이미지 로드 (common.js의 loadedDinoImages 활용)
                            if (opponentPlayer.charImgPath) {
                                opponentPlayer.charImg = loadedDinoImages.find(img => img.src.endsWith(opponentPlayer.charImgPath));
                            }
                        }
                    }
                });
                if (!foundSelf) console.warn("Game start: 현재 플레이어 정보를 서버 응답에서 찾지 못했습니다.");

            }
            foods = data.initial_foods.map(serverFood => {
                const foodProto = FOOD_INFO.find(fi => fi.name === serverFood.name);
                return {...serverFood, imageObject: foodProto ? foodProto.imageObject : null };
            });
            npcPlayers = data.initial_npcs.map(mapServerNpcToClientNpc_common);
            obstacles = data.initial_obstacles.map(mapServerObstacleToClientNpc_common);
            
            if (data.total_foods_to_win) totalFoodsToWin = data.total_foods_to_win;
            
            gamePlaying = true;
            if (sounds.bgm) { sounds.bgm.currentTime = 0; sounds.bgm.play().catch(e => {}); }
            if (sounds.sndStart) sounds.sndStart.play().catch(e => {});

            updateGameUI();
            if (gameLoopInterval_multi) clearInterval(gameLoopInterval_multi);
            gameLoopInterval_multi = setInterval(mainGameLoop_multi, 33); // 약 30FPS
            updateSystemMessage(`멀티플레이어 게임 시작! (방: ${currentRoomId_multi})`, false);
            break;

        case "state_update":
            if (data.players && data.players.length > 0) {
                let foundSelfInUpdate = false;
                let foundOpponentInUpdate = false;
                opponentPlayer = null; // 일단 초기화하고 현재 상태에서 다시 찾음 (플레이어 변동 가능성)

                data.players.forEach(p_data => {
                    if (p_data.id === player.id) { // 저장된 나의 ID로 비교
                        player.x = p_data.x;
                        player.y = p_data.y;
                        player.score = p_data.score;
                        player.eatCount = p_data.eatCount;
                        foundSelfInUpdate = true;
                    } else {
                        // 2인 게임 기준, 내가 아닌 다른 플레이어를 opponentPlayer로
                        if (!opponentPlayer) {
                            opponentPlayer = { id: p_data.id, user: p_data.user, x: p_data.x, y: p_data.y, score: p_data.score, charImgPath: p_data.charImgPath };
                            if (opponentPlayer.charImgPath) {
                                opponentPlayer.charImg = loadedDinoImages.find(img => img.src.endsWith(opponentPlayer.charImgPath));
                            }
                            foundOpponentInUpdate = true;
                        }
                        // 3인 이상 게임이면 opponentPlayer를 배열로 관리해야 함
                    }
                });
                if (!foundSelfInUpdate) console.warn("State update: 현재 플레이어 정보를 서버 응답에서 찾지 못했습니다.");
                // if (!foundOpponentInUpdate && data.players.length > 1) console.log("State update: 상대방 정보를 찾았으나, 이미 opponentPlayer가 있거나 다른 조건.");
            }
            if (data.foods) {
                foods = data.foods.map(serverFood => {
                    const foodProto = FOOD_INFO.find(fi => fi.name === serverFood.name);
                    return {...serverFood, imageObject: foodProto ? foodProto.imageObject : null };
                });
            }
            if (data.npcs) npcPlayers = data.npcs.map(mapServerNpcToClientNpc_common);
            if (data.obstacles) obstacles = data.obstacles.map(mapServerObstacleToClientNpc_common);
            
            updateGameUI();
            break;

        case "game_over":
            console.log("DEBUG (Client Multi): Received gameOver:", data);
            // data.winner는 승리한 플레이어의 user 이름
            endGame_multi(data.winner === player.user, data.winner);
            break;
        
        case "system_message":
            updateSystemMessage(`[안내] ${data.message}`);
            break;
        case "chat_message":
            updateSystemMessage(`[${data.user}] ${data.message}`); // 채팅 메시지 표시
            break;
        case "error":
            updateSystemMessage(`[서버 오류] ${data.message}`, true);
            break;
        default:
            console.warn("멀티플레이어 서버로부터 알 수 없는 액션 수신:", data.action, data);
    }
}


// --- 서버 데이터 매핑 함수 (common.js로 이동했거나, 여기에 중복 정의되어 있다면 common.js 것 사용) ---
// common.js에 mapServerNpcToClientNpc_common, mapServerObstacleToClientNpc_common 이 있다고 가정.

// --- 플레이어 액션 서버 전송 함수 ---
function sendMoveToServer_multi(newX, newY) {
    if (ws_multi && ws_multi.readyState === WebSocket.OPEN && gamePlaying) {
        ws_multi.send(JSON.stringify({
            action: "move",
            player: { x: newX, y: newY } // 서버는 이 메시지를 보낸 채널을 통해 플레이어를 식별
        }));
    }
}

function sendEatAttemptToServer_multi(foodId) {
    if (ws_multi && ws_multi.readyState === WebSocket.OPEN && gamePlaying) {
        const foodTarget = foods.find(f => f.id === foodId);
        if (foodTarget) {
            player.eating = true;
            setTimeout(() => { player.eating = false; }, 500);
        }
        ws_multi.send(JSON.stringify({ action: "eatAttempt", foodId: foodId }));
    }
}

function sendChatMessage_multi() {
    const chatInput = document.getElementById("chat-input"); // HTML에 채팅 입력창 ID 가정
    if (chatInput && ws_multi && ws_multi.readyState === WebSocket.OPEN) {
        const message = chatInput.value.trim();
        if (message) {
            ws_multi.send(JSON.stringify({ action: "chat", message: message }));
            chatInput.value = "";
        }
    }
}

// --- 게임 루프 (멀티플레이어용) ---
function mainGameLoop_multi() {
    if (!gamePlaying) {
        if (gameLoopInterval_multi) clearInterval(gameLoopInterval_multi);
        return;
    }
    draw(); // common.js의 그리기 함수 호출
}

// --- 플레이어 입력 처리 ---
function onPlayerMove_multi(event) {
    if (!gamePlaying || !ctx || !canvas || !ws_multi || ws_multi.readyState !== WebSocket.OPEN) return;
    
    let rect = canvas.getBoundingClientRect();
    let scaleX = canvas.width / rect.width;
    let scaleY = canvas.height / rect.height;
    let targetX = (event.clientX - rect.left) * scaleX;
    let targetY = (event.clientY - rect.top) * scaleY;

    sendMoveToServer_multi(targetX, targetY);

    if (!player.eating) {
        for (let food of foods) {
            if (eat_food_logic && typeof eat_food_logic.check_circle_circle_collision === 'function') {
                 if (eat_food_logic.check_circle_circle_collision(targetX, targetY, player.collisionRadius, food.x, food.y, food.collision_r)) {
                    sendEatAttemptToServer_multi(food.id);
                    break; 
                }
            } else if (typeof circleCircleCollision === 'function') { // common.js의 함수 사용
                 if (circleCircleCollision({x:targetX, y:targetY, r:player.collisionRadius}, food)) {
                    sendEatAttemptToServer_multi(food.id);
                    break;
                 }
            }
        }
    }
}

// --- 멀티플레이어 게임 종료 처리 ---
function endGame_multi(isCurrentPlayerWinner, winnerName) {
    if (gameLoopInterval_multi) {
        clearInterval(gameLoopInterval_multi);
        gameLoopInterval_multi = null;
    }
    // WebSocket 연결은 서버의 gameOver 메시지 이후 서버측에서 닫거나, 여기서 명시적으로 닫을 수 있음
    // if (ws_multi && ws_multi.readyState === WebSocket.OPEN) {
    // ws_multi.close(); 
    // }
    
    // common.js의 opponentPlayer가 winnerName과 일치하는지 등으로 상대 승리 여부도 판단 가능
    // 여기서는 현재 플레이어가 이겼는지 여부(isCurrentPlayerWinner)만 사용.
    // showResultPopup은 opponentPlayer 정보를 참조하므로, winnerName을 직접 전달할 필요는 없음.
    commonEndGameTasks(isCurrentPlayerWinner); // common.js의 공통 종료 처리 호출
    updateSystemMessage(`${winnerName}님이 승리했습니다! (방: ${currentRoomId_multi})`, false);
}


// --- 페이지 로드 후 설정 ---
document.addEventListener('DOMContentLoaded', () => {
    // common.js에서 initializeAndPreloadAssets()는 이미 호출됨.
    // 멀티플레이어용 시작 버튼 (또는 로비에서 방 ID와 함께 이 함수를 호출하는 로직)
    // 예시: HTML에 <button id="start-multi-button" data-roomid="testroom1">멀티플레이 시작</button> 가정
    const startMultiButton = document.getElementById("start-multi-button"); 
    if (startMultiButton) {
        startMultiButton.onclick = () => {
            const roomId = startMultiButton.dataset.roomid || generateFallbackUUID().substring(0,6); // 방 ID를 버튼에서 가져오거나 임의 생성
            startGame_multi(roomId);
        };
    }
    
    if (canvas) {
        canvas.addEventListener("mousemove", onPlayerMove_multi);
    }

    // 채팅 보내기 버튼 이벤트 리스너
    const chatSendButton = document.getElementById("chat-send-button"); // HTML에 버튼 ID 가정
    if (chatSendButton) {
        chatSendButton.onclick = sendChatMessage_multi;
    }
    const chatInput = document.getElementById("chat-input");
    if (chatInput) {
        chatInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault(); // 기본 엔터 행동(폼 제출 등) 방지
                sendChatMessage_multi();
            }
        });
    }

    // 전역으로 노출
    window.startGame_multi = startGame_multi; 
});

console.log("eat_food_multi.js 로드 완료");