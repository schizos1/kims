// static/js/games/eat_food/single_pixi.js
// 'eat_food' 게임의 싱글플레이어 모드 클라이언트 로직 (PixiJS + Socket.IO)

console.log("LOG_TEST: single_pixi.js 파일이 로드되고 실행 시작됨!");

let socket_single = null;
let gamePlaying_single = false;

// 공통 로직 파일(eat_food_common_pixi.js)에서 전역으로 설정된 변수들을 참조합니다.
// 예: window.pixiApp, window.gameContainer, window.player, window.foods, window.npcs, window.obstacles
// window.updateSystemMessage, window.updateCommonGameUI, window.showCommonResultPopup 등

let mouseGlobalPosition = { x: 0, y: 0 }; // PixiJS 스테이지 기준 마우스 좌표

// 게임 시작 함수 (eat_food_entry.html에서 GAME_MODE === 'single'일 때 호출)
window.startGame_single = async function() {
    console.log("DEBUG_SINGLE_JS: startGame_single() 호출됨.");

    if (!window.assetsLoaded) {
        window.updateSystemMessage("아직 에셋 로딩 중입니다. 잠시 후 다시 시도해주세요.", true);
        return;
    }
    if (gamePlaying_single) {
        console.warn("startGame_single: 게임이 이미 진행 중입니다.");
        return;
    }

    // 공통 Pixi 초기화가 아직 안 되었다면 실행 (commonPixiInit은 최초 한 번만 실행되도록 설계 가능)
    if (!window.pixiApp) {
        const initSuccess = await window.commonPixiInit(); // commonPixiInit 호출
        if (!initSuccess) {
            window.updateSystemMessage("게임 영역 초기화에 실패했습니다. 페이지를 새로고침해주세요.", true);
            return;
        }
    }

    window.updateSystemMessage("싱글플레이어 게임 시작 준비 중...", false);

    // HTML UI 초기화
    window.updateCommonGameUI(); // 점수, 남은 음식 등 초기화
    if (window.resultPopupEl) window.resultPopupEl.style.display = "none";

    // 플레이어 상태 초기화 (common의 window.player 객체 사용)
    window.player.score = 0;
    window.player.eatCount = 0;
    // window.player.x, window.player.y는 서버에서 game_start_info로 받아서 설정

    if (window.usernameInputEl) {
        window.player.user = window.usernameInputEl.value || `Player_${Math.floor(Math.random() * 1000)}`;
    } else {
        // USER_NAME_FROM_DJANGO는 eat_food_entry.html에서 정의됨
        window.player.user = (typeof USER_NAME_FROM_DJANGO !== 'undefined' && USER_NAME_FROM_DJANGO) ? USER_NAME_FROM_DJANGO : `Player_${Math.floor(Math.random() * 1000)}`;
    }
    // window.player.charImgPath는 common에서 기본값 설정, 서버에서 변경 가능

    // 기존 게임 요소들 제거 (PixiJS 컨테이너 비우기)
    if (window.gameContainer) {
        window.gameContainer.removeChildren(); // 모든 자식 DisplayObject 제거
    }
    window.foods = [];
    window.npcs = [];
    window.obstacles = [];

    // Socket.IO 연결 (포트는 Node.js 서버와 일치해야 함)
    const socketUrl = `http://${window.location.hostname}:3001`; // Node.js 서버 포트
    if (socket_single && socket_single.connected) {
        socket_single.disconnect();
    }
    socket_single = io(socketUrl, {
        reconnectionAttempts: 3, // 재연결 시도 횟수
        timeout: 5000 // 연결 타임아웃
    });
    window.updateSystemMessage(`싱글플레이어 서버 (${socketUrl}) 연결 중...`);

    // Socket.IO 이벤트 핸들러 등록
    socket_single.on("connect", () => {
        window.updateSystemMessage("서버 연결 성공! 게임 참여 요청 중...", false);
        const joinPayload = {
            user: window.player.user,
            charImgPath: window.player.charImgPath || "dino1" // .png 제외한 이름으로 통일 권장 (서버와 협의)
        };
        console.log("DEBUG_SINGLE_JS: 'join_single_game' 이벤트 전송:", joinPayload);
        socket_single.emit("join_single_game", joinPayload);
    });

    socket_single.on("disconnect", (reason) => {
        window.updateSystemMessage(`서버 연결이 종료되었습니다. (${reason})`, true);
        gamePlaying_single = false;
        if (window.pixiApp && window.pixiApp.ticker) window.pixiApp.ticker.stop();
    });

    socket_single.on("connect_error", (err) => {
        console.error("Socket.IO 연결 오류:", err);
        window.updateSystemMessage(`서버 연결 실패: ${err.message || '알 수 없는 오류'}`, true);
        gamePlaying_single = false;
    });

    socket_single.on("game_start_info", handleGameStartInfo_single);
    socket_single.on("state_update", handleStateUpdate_single);
    socket_single.on("game_over", handleGameOver_single);
    socket_single.on("server_error", (data) => {
        window.updateSystemMessage(`[서버 오류] ${data.message}`, true);
        gamePlaying_single = false; // 오류 시 게임 중단
        if (window.pixiApp && window.pixiApp.ticker) window.pixiApp.ticker.stop();
    });
};
// startGame_single 함수를 전역으로 노출 (eat_food_entry.html에서 호출 위함)
window.startGame_single = startGame_single;


function handleGameStartInfo_single(data) {
    console.log("DEBUG_SINGLE_JS: 'game_start_info' 수신:", data);
    if (!window.pixiApp || !window.gameContainer) {
        console.error("PixiJS 앱 또는 게임 컨테이너가 준비되지 않았습니다.");
        return;
    }

    // 캔버스 크기 업데이트 (서버에서 받았다면)
    if (data.canvas_width && data.canvas_height) {
        CANVAS_WIDTH = data.canvas_width;
        CANVAS_HEIGHT = data.canvas_height;
        window.pixiApp.renderer.resize(CANVAS_WIDTH, CANVAS_HEIGHT);
    }

    if (data.player) {
        Object.assign(window.player, data.player);
        window.player.sprite = window.createOrUpdatePlayerSprite(window.player); // common 함수 사용
    }

    // 기존 요소들 확실히 클리어
    window.gameContainer.removeChildren();
    if (window.player.sprite) window.gameContainer.addChild(window.player.sprite); // 플레이어는 다시 추가

    window.foods = [];
    data.foods.forEach(serverFood => {
        const food = { ...serverFood };
        food.sprite = window.createFoodSprite(food); // common 함수 사용
        window.foods.push(food);
    });

    window.npcs = [];
    data.npcs.forEach(serverNpc => {
        const npc = { ...serverNpc };
        npc.sprite = window.createNpcSprite(npc); // common 함수 사용
        window.npcs.push(npc);
    });

    window.obstacles = [];
    data.obstacles.forEach(serverObstacle => {
        const obstacle = { ...serverObstacle };
        obstacle.graphics = window.createObstacleGraphics(obstacle); // common 함수 사용
        window.obstacles.push(obstacle);
    });

    if (data.total_foods_to_win) window.totalFoodsToWin = data.total_foods_to_win;

    gamePlaying_single = true;
    window.updateSystemMessage("싱글플레이어 게임 시작!", false);
    window.updateCommonGameUI();

    // PixiJS 게임 루프 시작 (이미 실행 중이면 중복 실행 방지)
    if (window.pixiApp.ticker && !window.pixiApp.ticker.started) {
        window.pixiApp.ticker.add(gameLoop_single);
        window.pixiApp.ticker.start();
    } else if (window.pixiApp.ticker && window.pixiApp.ticker.started) {
        // 루프가 이미 돌고 있다면, 함수를 교체하거나 할 필요는 없음.
        // 다만, 이전 게임의 루프 함수가 등록되어 있다면 제거 후 새로 등록 고려.
        // 여기서는 동일한 gameLoop_single 함수를 사용한다고 가정.
    }
    
    // 마우스/터치 이벤트 리스너 등록 (PixiJS 스테이지에)
    if (window.pixiApp.stage) {
        window.pixiApp.stage.off('pointermove', onPlayerMouseMove_pixi_single); // 기존 리스너 제거
        window.pixiApp.stage.on('pointermove', onPlayerMouseMove_pixi_single);
        
        window.pixiApp.stage.off('pointerdown', onGameClick_pixi_single);
        window.pixiApp.stage.on('pointerdown', onGameClick_pixi_single);
    }
}

function handleStateUpdate_single(data) {
    if (!gamePlaying_single) return;

    if (data.player && window.player && window.player.sprite) {
        Object.assign(window.player, data.player); // 점수, 먹은 개수 등도 업데이트
        window.player.sprite.x = window.player.x;
        window.player.sprite.y = window.player.y;
    }

    // 음식 상태 업데이트 (ID 기반으로 매칭하여 업데이트 또는 재생성)
    if (data.foods) {
        const existingFoodIds = new Set();
        data.foods.forEach(serverFood => {
            existingFoodIds.add(serverFood.id);
            let localFood = window.foods.find(f => f.id === serverFood.id);
            if (localFood && localFood.sprite) { // 기존 음식 업데이트
                localFood.x = serverFood.x;
                localFood.y = serverFood.y;
                localFood.sprite.x = serverFood.x;
                localFood.sprite.y = serverFood.y;
                // 필요시 다른 속성도 업데이트 (예: special 상태 변경)
            } else { // 새 음식 추가
                const newFood = { ...serverFood };
                newFood.sprite = window.createFoodSprite(newFood);
                window.foods.push(newFood);
            }
        });
        // 서버에 없는 로컬 음식 제거
        window.foods = window.foods.filter(localFood => {
            if (!existingFoodIds.has(localFood.id) && localFood.sprite) {
                window.gameContainer.removeChild(localFood.sprite);
                localFood.sprite.destroy(); // PixiJS 객체 메모리 해제
                return false;
            }
            return true;
        });
    }

    // NPC 상태 업데이트 (ID 기반)
    if (data.npcs) {
        const existingNpcIds = new Set();
        data.npcs.forEach(serverNpc => {
            existingNpcIds.add(serverNpc.id);
            let localNpc = window.npcs.find(n => n.id === serverNpc.id);
            if (localNpc && localNpc.sprite) {
                Object.assign(localNpc, serverNpc); // 상태 전체 업데이트
                localNpc.sprite.x = localNpc.x;
                localNpc.sprite.y = localNpc.y;
                // NPC 화남/먹는 중 상태에 따른 시각적 효과 (예: 틴트, 애니메이션)
                if (localNpc.isAngry) localNpc.sprite.tint = 0xFF6666;
                else if (localNpc.eatingTargetId) localNpc.sprite.tint = 0xFFCC66;
                else localNpc.sprite.tint = 0xFFFFFF; // 기본 색상
            } else {
                const newNpc = { ...serverNpc };
                newNpc.sprite = window.createNpcSprite(newNpc);
                window.npcs.push(newNpc);
            }
        });
        window.npcs = window.npcs.filter(localNpc => {
            if (!existingNpcIds.has(localNpc.id) && localNpc.sprite) {
                window.gameContainer.removeChild(localNpc.sprite);
                localNpc.sprite.destroy();
                return false;
            }
            return true;
        });
    }
    
    // 장애물 상태 업데이트 (만약 동적으로 변한다면)
    if (data.obstacles) {
        // 장애물은 보통 게임 시작 시 고정되지만, 재생성된다면 유사한 로직으로 처리
        window.obstacles.forEach(o => { if(o.graphics) window.gameContainer.removeChild(o.graphics); o.graphics.destroy(); });
        window.obstacles = [];
        data.obstacles.forEach(serverObstacle => {
            const obstacle = { ...serverObstacle };
            obstacle.graphics = window.createObstacleGraphics(obstacle);
            window.obstacles.push(obstacle);
        });
    }
    window.updateCommonGameUI(); // HTML UI 업데이트
}

function handleGameOver_single(data) {
    console.log("DEBUG_SINGLE_JS: 'game_over' 수신:", data);
    gamePlaying_single = false;
    if (window.pixiApp.ticker) window.pixiApp.ticker.stop();

    const isWin = data.winner === window.player.user;
    window.showCommonResultPopup(isWin, window.player.score, window.player.eatCount);
}

// 서버로 플레이어 이동 요청 (목표 좌표)
function sendMoveToServer_single(targetX, targetY) {
    if (socket_single && socket_single.connected && gamePlaying_single) {
        socket_single.emit("player_move_request", { x: targetX, y: targetY });
    }
}

// 서버로 음식 먹기 시도
function sendEatAttemptToServer_single(foodId) {
    if (socket_single && socket_single.connected && gamePlaying_single) {
        socket_single.emit("player_eat_attempt", { foodId: foodId });
    }
}

// PixiJS 스테이지에서의 마우스 이동 이벤트 핸들러
function onPlayerMouseMove_pixi_single(event) {
    if (!gamePlaying_single || !window.pixiApp || !window.player || !window.player.sprite) return;
    mouseGlobalPosition = event.data.getLocalPosition(window.pixiApp.stage);
    // 실제 이동 요청은 게임 루프에서 주기적으로 보내거나, 변경 폭이 클 때만 보낼 수 있음
    // 여기서는 매번 보내는 대신, 게임 루프에서 플레이어가 마우스를 향하도록 하고,
    // 서버로는 최종 목표 지점을 보낸다고 가정.
    // 또는, 서버가 클라이언트의 마우스 좌표를 직접 받아서 처리할 수도 있음.
    // 여기서는 간단히 목표 좌표를 서버로 보냄
    sendMoveToServer_single(mouseGlobalPosition.x, mouseGlobalPosition.y);
}
// eat_food_entry.html에서 이 함수를 직접 사용하지 않고, startGame_single 내부에서 리스너 등록

// PixiJS 스테이지에서의 클릭 이벤트 핸들러 (음식 먹기 시도)
function onGameClick_pixi_single(event) {
    if (!gamePlaying_single || !window.pixiApp || !window.player || !window.player.sprite) return;

    const clickPos = event.data.getLocalPosition(window.gameContainer); // 게임 컨테이너 기준 좌표

    // 플레이어와 가장 가까운 음식 또는 클릭 위치의 음식 찾기
    let foodToEat = null;
    let minDistanceSqToClick = Infinity;

    window.foods.forEach(food => {
        if (food.sprite) {
            // 클릭 지점과 음식 중심 사이의 거리 제곱
            const distSq = (clickPos.x - food.x)**2 + (clickPos.y - food.y)**2;
            // 음식의 시각적 반지름(food.r) 내에 클릭했는지 확인
            if (distSq < (food.r * food.r) && distSq < minDistanceSqToClick) {
                 // 그리고 플레이어가 해당 음식 근처에 있는지도 확인 (서버에서 최종 판정)
                const playerToFoodDistSq = (window.player.x - food.x)**2 + (window.player.y - food.y)**2;
                const touchRange = (window.player.collisionRadius + food.collision_r + 10)**2; // 약간의 여유 범위
                if (playerToFoodDistSq < touchRange) {
                    minDistanceSqToClick = distSq;
                    foodToEat = food;
                }
            }
        }
    });

    if (foodToEat) {
        sendEatAttemptToServer_single(foodToEat.id);
    }
}
// eat_food_entry.html에서 이 함수를 직접 사용하지 않고, startGame_single 내부에서 리스너 등록


// PixiJS 게임 루프
function gameLoop_single(ticker) { // ticker는 PIXI.Ticker 인스턴스 또는 델타타임 제공
    if (!gamePlaying_single) return;

    // 클라이언트 측 예측/보간 로직 (선택 사항, 서버가 모든 상태를 관리한다면 불필요할 수 있음)
    // 예: 플레이어 스프라이트가 서버에서 받은 x,y로 부드럽게 이동
    if (window.player && window.player.sprite) {
        // Lerp 이동 예시 (더 부드러운 움직임을 위해)
        // window.player.sprite.x += (window.player.x - window.player.sprite.x) * 0.2;
        // window.player.sprite.y += (window.player.y - window.player.sprite.y) * 0.2;
        // 또는 서버에서 받은 x,y를 그대로 사용
         window.player.sprite.x = window.player.x;
         window.player.sprite.y = window.player.y;
    }

    // NPC 스프라이트 위치 업데이트 (서버에서 받은 x,y 사용)
    window.npcs.forEach(npc => {
        if (npc.sprite) {
            npc.sprite.x = npc.x;
            npc.sprite.y = npc.y;
            if (npc.isAngry) { // 화났을 때 시각적 효과
                npc.sprite.tint = 0xFF6666; // 붉은색 틴트
                npc.sprite.rotation = Math.sin(Date.now() * 0.02) * 0.15; // 약간 흔들림
            } else if (npc.eatingTargetId) {
                npc.sprite.tint = 0xFFFF99; // 먹는 중 노란색 틴트
                npc.sprite.rotation = 0;
            } else {
                npc.sprite.tint = 0xFFFFFF; // 기본
                npc.sprite.rotation = 0;
            }
        }
    });
    // 음식, 장애물은 보통 위치가 고정되므로 루프에서 업데이트할 필요는 없음 (서버에서 변경 시 state_update로 처리)
}

// 게임 재시작/초기화 로직 (결과 팝업 닫을 때 등 호출)
window.resetGame_single = function() {
    console.log("DEBUG_SINGLE_JS: resetGame_single() 호출됨.");
    gamePlaying_single = false;
    if (window.pixiApp && window.pixiApp.ticker) {
        window.pixiApp.ticker.stop();
        window.pixiApp.ticker.remove(gameLoop_single); // 등록된 루프 함수 제거
    }
    if (socket_single && socket_single.connected) {
        socket_single.disconnect();
    }
    socket_single = null;

    if (window.gameContainer) {
        window.gameContainer.removeChildren();
    }
    // 상태 변수 초기화
    window.player.score = 0;
    window.player.eatCount = 0;
    window.player.sprite = null; // Pixi 스프라이트 참조도 초기화
    window.foods = [];
    window.npcs = [];
    window.obstacles = [];

    if (window.startButtonEl) window.startButtonEl.disabled = false;
    window.updateSystemMessage("게임을 시작하려면 '게임 시작' 버튼을 누르세요.", false);
    window.updateCommonGameUI(); // 점수판 등 UI 초기화
};

console.log("single_pixi.js 로드 및 전역 함수 설정 완료.");