// static/minigame/js/eat_food_single.js
// 'eat_food' 게임의 싱글플레이어 모드 전용 JavaScript 로직입니다.
// 서버의 SinglePlayerGameConsumer와 WebSocket 통신을 담당합니다.
// eat_food_common.js가 먼저 로드되어야 합니다.

let ws_single = null; // 싱글플레이어용 WebSocket 객체
let gameLoopInterval_single = null; // 싱글플레이어 게임 루프 인터벌

// --- 싱글플레이어 게임 시작 함수 ---
function startGame_single() {
    console.log("DEBUG_SINGLE_JS: startGame_single() function CALLED!");

    // common.js에서 설정된 window.assetsLoaded 값을 확인
    if (!window.assetsLoaded) { 
        updateSystemMessage("아직 에셋 로딩 중입니다...", true); // common.js 함수
        console.log("DEBUG_SINGLE_JS: Assets not loaded yet (checked window.assetsLoaded). Aborting startGame_single.");
        return;
    }
    if (gamePlaying) { // common.js 변수
        console.log("DEBUG_SINGLE_JS: Game is already playing. Aborting startGame_single.");
        return;
    }

    updateSystemMessage("싱글플레이어 게임 시작 준비 중...", false);  // common.js 함수

    // UI 초기화 (common.js 요소 사용)
    if (scoreNum) scoreNum.innerText = "0";
    if (foodLeftNum && typeof totalFoodsToWin !== 'undefined') foodLeftNum.innerText = totalFoodsToWin.toString();
    if (progressBar) progressBar.style.width = "0%";
    if (resultPopup) resultPopup.style.display = "none";

    // 플레이어 기본 상태 초기화 (common.js의 player 객체 사용)
    player.score = 0;
    player.eatCount = 0;
    player.eating = false;

    // 수정: usernameInput을 이 함수 내에서 직접 다시 찾아서 사용
    const localUsernameInput = document.getElementById("username");
    if (localUsernameInput) {
        player.user = localUsernameInput.value || `Player_${generateFallbackUUID().substring(0,4)}`;
    } else {
        console.warn("DEBUG_SINGLE_JS: username input field ('username') not found! Using fallback name.");
        // common.js의 USER_NAME_FROM_DJANGO가 있다면 그것을 사용하도록 시도
        player.user = (typeof USER_NAME_FROM_DJANGO !== 'undefined' && USER_NAME_FROM_DJANGO) ? USER_NAME_FROM_DJANGO : `Player_${generateFallbackUUID().substring(0,4)}`;
    }
    console.log("DEBUG_SINGLE_JS: Player User:", player.user);

    // 캐릭터 이미지 선택 (common.js의 loadedDinoImages 사용)
    if (loadedDinoImages && loadedDinoImages.length > 0) {
        let randomIdx = Math.floor(Math.random() * loadedDinoImages.length);
        if (loadedDinoImages[randomIdx] && loadedDinoImages[randomIdx].complete && loadedDinoImages[randomIdx].naturalWidth > 0) {
            player.charImg = loadedDinoImages[randomIdx];
            player.charImgPath = DINO_IMG_PATHS[randomIdx]; 
        } else { 
            let foundValidImg = false;
            for(let i=0; i < loadedDinoImages.length; i++){
                if(loadedDinoImages[i] && loadedDinoImages[i].complete && loadedDinoImages[i].naturalWidth > 0){
                    player.charImg = loadedDinoImages[i];
                    player.charImgPath = DINO_IMG_PATHS[i];
                    foundValidImg = true;
                    break;
                }
            }
            if(!foundValidImg){
                 player.charImg = null; 
                 player.charImgPath = DINO_IMG_PATHS.length > 0 ? DINO_IMG_PATHS[0] : "dino1.png"; // DINO_IMG_PATHS가 비어있을 경우 대비
                 console.error("DEBUG_SINGLE_JS: No valid player images found after attempting fallback!");
            } else {
                console.warn("DEBUG_SINGLE_JS: Selected player image was invalid or not loaded, used first available fallback.");
            }
        }
        console.log("DEBUG_SINGLE_JS: Player charImgPath set to:", player.charImgPath);
    } else {
        console.error("DEBUG_SINGLE_JS: loadedDinoImages is empty or invalid!");
        player.charImgPath = DINO_IMG_PATHS.length > 0 ? DINO_IMG_PATHS[0] : "dino1.png";
        player.charImg = null; 
    }
    
    // 로컬 상태 초기화
    foods = [];
    npcPlayers = [];
    obstacles = [];
    opponentPlayer = null;

    const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const wsUrl_single = wsProtocol + window.location.host + `/ws/minigame/games/eat_food/single/`; 
    
    console.log("DEBUG_SINGLE_JS: Attempting WebSocket connection to:", wsUrl_single);
    updateSystemMessage(`싱글플레이어 서버에 연결 중...`);

    if (ws_single && (ws_single.readyState === WebSocket.OPEN || ws_single.readyState === WebSocket.CONNECTING)) {
        console.log("DEBUG_SINGLE_JS: Closing existing WebSocket connection.");
        ws_single.close();
    }
    
    try {
        ws_single = new WebSocket(wsUrl_single);
        console.log("DEBUG_SINGLE_JS: WebSocket object CREATED. Initial readyState:", ws_single.readyState);
    } catch (e) {
        console.error("DEBUG_SINGLE_JS: ERROR creating WebSocket:", e);
        updateSystemMessage("WebSocket 생성 중 오류 발생!", true);
        return;
    }

    ws_single.onopen = () => {
        console.log("DEBUG_SINGLE_JS: WebSocket connection OPENED! (readyState:", ws_single.readyState, ")");
        updateSystemMessage("서버 연결 성공! 게임 참여 요청 중...", false);
        
        const joinPayload = {
            action: "join",
            user: player.user,
            charImgPath: player.charImgPath 
        };
        console.log("DEBUG_SINGLE_JS: Sending JOIN message to server:", JSON.stringify(joinPayload));
        try {
            ws_single.send(JSON.stringify(joinPayload));
            console.log("DEBUG_SINGLE_JS: JOIN message sent.");
        } catch (e) {
            console.error("DEBUG_SINGLE_JS: ERROR sending JOIN message:", e);
        }
    };

    ws_single.onmessage = (event) => {
        console.log("DEBUG_SINGLE_JS: Raw message RECEIVED from server:", event.data);
        handleServerMessage_single(event); 
    };

    ws_single.onclose = (event) => {
        console.log(`DEBUG_SINGLE_JS: WebSocket connection CLOSED. Code: ${event.code}, Reason: "${event.reason}", WasClean: ${event.wasClean}`);
        updateSystemMessage("서버 연결이 종료되었습니다. 다시 시도해주세요.", true);
        gamePlaying = false; 
        if (gameLoopInterval_single) { clearInterval(gameLoopInterval_single); gameLoopInterval_single = null; }
    };

    ws_single.onerror = (errorEvent) => { 
        console.error("DEBUG_SINGLE_JS: WebSocket ERROR occurred:", errorEvent);
        updateSystemMessage("WebSocket 연결 중 오류가 발생했습니다.", true);
        gamePlaying = false;
        if (gameLoopInterval_single) { clearInterval(gameLoopInterval_single); gameLoopInterval_single = null; }
    };

    console.log("DEBUG_SINGLE_JS: WebSocket event handlers assigned.");
}

// --- 서버 메시지 처리 함수 (싱글플레이어용) ---
function handleServerMessage_single(event) {
    let data;
    try {
        data = JSON.parse(event.data);
        console.log("DEBUG_SINGLE_JS: Parsed server message data:", data);
    } catch (e) {
        console.error("DEBUG_SINGLE_JS: Error parsing server message JSON:", e, "Raw data:", event.data);
        return;
    }

    switch (data.action) {
        case "connection_established":
            console.log("DEBUG_SINGLE_JS: Action 'connection_established'. Message:", data.message);
            updateSystemMessage(data.message, false);
            break;
        case "game_start_info":
            console.log("DEBUG_SINGLE_JS: Action 'game_start_info'. Starting game setup.");
            if (data.player) {
                player.x = data.player.x;
                player.y = data.player.y;
                player.score = data.player.score;
                player.eatCount = data.player.eatCount;
                player.id = data.player.id; 
                console.log("DEBUG_SINGLE_JS: Player data updated from server:", player);
            }
            foods = data.foods.map(serverFood => { 
                const foodProto = FOOD_INFO.find(fi => fi.name === serverFood.name);
                return {...serverFood, imageObject: foodProto ? foodProto.imageObject : null };
            });
            npcPlayers = data.npcs.map(mapServerNpcToClientNpc_single); 
            obstacles = data.obstacles.map(mapServerObstacleToClientObstacle_single); 
            
            if (data.total_foods_to_win) totalFoodsToWin = data.total_foods_to_win;
            
            gamePlaying = true; 
            if (sounds.bgm) { sounds.bgm.currentTime = 0; sounds.bgm.play().catch(e => { console.warn("DEBUG_SINGLE_JS: BGM play error:", e);}); }
            if (sounds.sndStart) sounds.sndStart.play().catch(e => { console.warn("DEBUG_SINGLE_JS: Start sound play error:", e);});

            updateGameUI(); 
            if (gameLoopInterval_single) clearInterval(gameLoopInterval_single);
            gameLoopInterval_single = setInterval(mainGameLoop_single, 33); 
            updateSystemMessage("싱글플레이어 게임 시작!", false);
            console.log("DEBUG_SINGLE_JS: Game started! Foods:", foods.length, "NPCs:", npcPlayers.length, "Obstacles:", obstacles.length);
            break;

        case "state_update":
            console.log("DEBUG_SINGLE_JS: Action 'state_update'. Received data:", JSON.stringify(data)); 
            if (data.player) { 
                player.x = data.player.x;
                player.y = data.player.y;
                player.score = data.player.score;
                player.eatCount = data.player.eatCount;
            }
            if (data.foods) {
                foods = data.foods.map(serverFood => {
                    const foodProto = FOOD_INFO.find(fi => fi.name === serverFood.name);
                    return {...serverFood, imageObject: foodProto ? foodProto.imageObject : null };
                });
            }
            if (data.npcs) {
                npcPlayers = data.npcs.map(mapServerNpcToClientNpc_single);
            }
            if (data.obstacles) {
                obstacles = data.obstacles.map(mapServerObstacleToClientObstacle_single);
            }
            updateGameUI();
            break;

        case "game_over":
            console.log("DEBUG_SINGLE_JS: Action 'game_over'. Winner:", data.winner);
            endGame_single(data.winner === player.user); 
            break;
        
        case "error":
            console.error("DEBUG_SINGLE_JS: Action 'error'. Message:", data.message);
            updateSystemMessage(`[서버 오류] ${data.message}`, true);
            break;

        default:
            console.warn("DEBUG_SINGLE_JS: Unknown action received from server:", data.action, data);
    }
}

// --- 서버 데이터 매핑 함수 (이 파일 내에서만 사용) ---
function mapServerNpcToClientNpc_single(serverNpc) {
    let npcCollisionRadius = 30; // 기본값 또는 서버에서 내려주는 값 사용
    if(serverNpc && typeof serverNpc.collision_r !== 'undefined') { // 서버에서 collision_r을 내려준다면 사용
        npcCollisionRadius = serverNpc.collision_r;
    } else if (typeof eat_food_config !== 'undefined' && eat_food_config.NPC_COLLISION_RADIUS) { // Django 템플릿 통해 전달된 config 객체 (존재한다면)
        npcCollisionRadius = eat_food_config.NPC_COLLISION_RADIUS;
    }

    return {
        id: serverNpc.id, x: serverNpc.x, y: serverNpc.y,
        charImg: loadedNpcImage, 
        speed: serverNpc.speed,
        isAngry: serverNpc.isAngry || false,
        eatingTargetId: serverNpc.eatingTargetId,
        collisionRadius: npcCollisionRadius, 
    };
}

function mapServerObstacleToClientObstacle_single(serverObstacle) {
    return {
        id: serverObstacle.id, type: serverObstacle.type,
        x: serverObstacle.x, y: serverObstacle.y,
        r: serverObstacle.r, w: serverObstacle.w, h: serverObstacle.h,
        mainColor: serverObstacle.mainColor 
    };
}


// --- 플레이어 액션 서버 전송 함수 ---
function sendMoveToServer_single(newX, newY) {
    if (ws_single && ws_single.readyState === WebSocket.OPEN && gamePlaying) {
        const payload = { action: "move", player: { x: newX, y: newY } };
        // console.log("DEBUG_SINGLE_JS: Sending MOVE message:", JSON.stringify(payload)); // 너무 빈번하여 주석 처리
        ws_single.send(JSON.stringify(payload));
    }
}

function sendEatAttemptToServer_single(foodId) {
    if (ws_single && ws_single.readyState === WebSocket.OPEN && gamePlaying) {
        const foodTarget = foods.find(f => f.id === foodId);
        if (foodTarget) {
            player.eating = true; 
            setTimeout(() => { player.eating = false; }, 500); 
        }
        const payload = { action: "eatAttempt", foodId: foodId };
        console.log("DEBUG_SINGLE_JS: Sending EAT_ATTEMPT message for foodId:", foodId);
        ws_single.send(JSON.stringify(payload));
    }
}

// --- 게임 루프 (싱글플레이어용) ---
function mainGameLoop_single() {
    if (!gamePlaying) { 
        if (gameLoopInterval_single) clearInterval(gameLoopInterval_single);
        return;
    }
    draw(); // common.js의 그리기 함수 호출
}

// --- 플레이어 입력 처리 ---
// 이 함수는 eat_food_entry.html의 DOMContentLoaded 리스너에서 canvas의 mousemove 이벤트에 연결되어야 합니다.
function onPlayerMove_single(event) {
    if (!gamePlaying || !ctx || !canvas ) return; 
    
    // console.log("DEBUG_SINGLE_JS: onPlayerMove_single triggered"); // 마우스 이동 시 로그 (필요시 활성화)
    let rect = canvas.getBoundingClientRect();
    let scaleX = canvas.width / rect.width;
    let scaleY = canvas.height / rect.height;
    let targetX = (event.clientX - rect.left) * scaleX;
    let targetY = (event.clientY - rect.top) * scaleY;

    sendMoveToServer_single(targetX, targetY);

    if (!player.eating) { 
    for (let food of foods) {
        if (circleCircleCollision({x:targetX, y:targetY, r:player.collisionRadius}, food)) { 
            console.log(`DEBUG_SINGLE_JS: Player near food ${food.id}. Attempting to eat.`); // 로그 추가
            sendEatAttemptToServer_single(food.id);
            break; 
        }
    }
}
}

// --- 싱글플레이어 게임 종료 처리 ---
function endGame_single(isWin) {
    console.log(`DEBUG_SINGLE_JS: endGame_single called. Player won: ${isWin}`);
    if (gameLoopInterval_single) {
        clearInterval(gameLoopInterval_single);
        gameLoopInterval_single = null;
        console.log("DEBUG_SINGLE_JS: Game loop cleared.");
    }
    if (ws_single && ws_single.readyState === WebSocket.OPEN) {
        // ws_single.close(); // 서버에서 game_over 보내고 연결을 닫을 수도 있음
    }
    commonEndGameTasks(isWin); 
}

// startGame_single 함수와 onPlayerMove_single 함수를 전역 스코프에 노출
window.startGame_single = startGame_single; 
window.onPlayerMove_single = onPlayerMove_single; // eat_food_entry.html에서 이벤트 리스너로 사용하기 위함

console.log("eat_food_single.js 로드 완료 및 함수 전역 노출 완료");