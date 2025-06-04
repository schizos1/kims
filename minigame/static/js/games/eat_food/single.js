//single.js - Socket.IO 기반 싱글 플레이 모드 + Pixi.js 적용

let socket_single = null;
let gameLoopInterval_single = null;

function startGame_single() {
    console.log("DEBUG_SINGLE_JS: startGame_single() function CALLED!");

    if (!window.assetsLoaded) {
        updateSystemMessage("아직 에셋 로딩 중입니다...", true);
        return;
    }
    if (gamePlaying) {
        return;
    }

    updateSystemMessage("싱글플레이어 게임 시작 준비 중...", false);

    if (scoreNum) scoreNum.innerText = "0";
    if (foodLeftNum && typeof totalFoodsToWin !== 'undefined') foodLeftNum.innerText = totalFoodsToWin.toString();
    if (progressBar) progressBar.style.width = "0%";
    if (resultPopup) resultPopup.style.display = "none";

    player.score = 0;
    player.eatCount = 0;
    player.eating = false;

    const localUsernameInput = document.getElementById("username");
    if (localUsernameInput) {
        player.user = localUsernameInput.value || `Player_${generateFallbackUUID().substring(0,4)}`;
    } else {
        player.user = (typeof USER_NAME_FROM_DJANGO !== 'undefined' && USER_NAME_FROM_DJANGO) ? USER_NAME_FROM_DJANGO : `Player_${generateFallbackUUID().substring(0,4)}`;
    }

    if (loadedDinoImages && loadedDinoImages.length > 0) {
        let randomIdx = Math.floor(Math.random() * loadedDinoImages.length);
        player.charImg = loadedDinoImages[randomIdx];
        player.charImgPath = DINO_IMG_PATHS[randomIdx];
    } else {
        player.charImgPath = DINO_IMG_PATHS.length > 0 ? DINO_IMG_PATHS[0] : "dino1.png";
        player.charImg = null;
    }

    foods = [];
    npcPlayers = [];
    obstacles = [];
    opponentPlayer = null;

    const socketUrl = "http://" + window.location.hostname + ":3000";
    socket_single = io(socketUrl);
    updateSystemMessage(`싱글플레이어 서버에 연결 중...`);

    socket_single.on("connect", () => {
        updateSystemMessage("서버 연결 성공! 게임 참여 요청 중...", false);
        const joinPayload = {
            action: "join",
            user: player.user,
            charImgPath: player.charImgPath
        };
        socket_single.emit("message", joinPayload);
    });

    socket_single.on("message", (data) => {
        handleServerMessage_single({ data: JSON.stringify(data) });
    });

    socket_single.on("disconnect", () => {
        updateSystemMessage("서버 연결이 종료되었습니다. 다시 시도해주세요.", true);
        gamePlaying = false;
        if (gameLoopInterval_single) clearInterval(gameLoopInterval_single);
    });

    socket_single.on("connect_error", (err) => {
        console.error("DEBUG_SINGLE_JS: Socket.IO connect error:", err);
        updateSystemMessage("서버 연결 실패", true);
    });
}

function handleServerMessage_single(event) {
    let data;
    try {
        data = JSON.parse(event.data);
    } catch (e) {
        return;
    }

    switch (data.action) {
        case "connection_established":
            updateSystemMessage(data.message, false);
            break;
        case "game_start_info":
            if (data.player) {
                Object.assign(player, data.player);
            }
            foods = data.foods.map(serverFood => {
                const foodProto = FOOD_INFO.find(fi => fi.name === serverFood.name);
                return { ...serverFood, imageObject: foodProto ? foodProto.imageObject : null };
            });
            npcPlayers = data.npcs.map(mapServerNpcToClientNpc_single);
            obstacles = data.obstacles.map(mapServerObstacleToClientObstacle_single);
            if (data.total_foods_to_win) totalFoodsToWin = data.total_foods_to_win;
            gamePlaying = true;
            if (sounds.bgm) sounds.bgm.play().catch(e => {});
            if (sounds.sndStart) sounds.sndStart.play().catch(e => {});
            updateGameUI();
            if (gameLoopInterval_single) clearInterval(gameLoopInterval_single);
            gameLoopInterval_single = setInterval(mainGameLoop_single, 33);
            updateSystemMessage("싱글플레이어 게임 시작!", false);
            break;
        case "state_update":
            Object.assign(player, data.player);
            foods = data.foods.map(f => ({ ...f, imageObject: FOOD_INFO.find(fi => fi.name === f.name)?.imageObject || null }));
            npcPlayers = data.npcs.map(mapServerNpcToClientNpc_single);
            obstacles = data.obstacles.map(mapServerObstacleToClientObstacle_single);
            updateGameUI();
            break;
        case "game_over":
            endGame_single(data.winner === player.user);
            break;
        case "error":
            updateSystemMessage(`[서버 오류] ${data.message}`, true);
            break;
    }
}

function sendMoveToServer_single(newX, newY) {
    if (socket_single && gamePlaying) {
        socket_single.emit("message", { action: "move", player: { x: newX, y: newY } });
    }
}

function sendEatAttemptToServer_single(foodId) {
    if (socket_single && gamePlaying) {
        const foodTarget = foods.find(f => f.id === foodId);
        if (foodTarget) {
            player.eating = true;
            setTimeout(() => { player.eating = false; }, 500);
        }
        socket_single.emit("message", { action: "eatAttempt", foodId });
    }
}

function mapServerNpcToClientNpc_single(serverNpc) {
    return {
        id: serverNpc.id,
        x: serverNpc.x,
        y: serverNpc.y,
        charImg: loadedNpcImage,
        speed: serverNpc.speed,
        isAngry: serverNpc.isAngry || false,
        eatingTargetId: serverNpc.eatingTargetId,
        collisionRadius: serverNpc.collision_r || 30
    };
}

function mapServerObstacleToClientObstacle_single(serverObstacle) {
    return {
        id: serverObstacle.id,
        type: serverObstacle.type,
        x: serverObstacle.x,
        y: serverObstacle.y,
        r: serverObstacle.r,
        w: serverObstacle.w,
        h: serverObstacle.h,
        mainColor: serverObstacle.mainColor
    };
}

function mainGameLoop_single() {
    if (!gamePlaying) {
        if (gameLoopInterval_single) clearInterval(gameLoopInterval_single);
        return;
    }
    draw();
}

function onPlayerMove_single(event) {
    if (!gamePlaying || !ctx || !canvas) return;
    let rect = canvas.getBoundingClientRect();
    let scaleX = canvas.width / rect.width;
    let scaleY = canvas.height / rect.height;
    let targetX = (event.clientX - rect.left) * scaleX;
    let targetY = (event.clientY - rect.top) * scaleY;
    sendMoveToServer_single(targetX, targetY);
    if (!player.eating) {
        for (let food of foods) {
            if (circleCircleCollision({ x: targetX, y: targetY, r: player.collisionRadius }, food)) {
                sendEatAttemptToServer_single(food.id);
                break;
            }
        }
    }
}

function endGame_single(isWin) {
    if (gameLoopInterval_single) clearInterval(gameLoopInterval_single);
    commonEndGameTasks(isWin);
}

window.startGame_single = startGame_single;
window.onPlayerMove_single = onPlayerMove_single;

console.log("eat_food_single.js 리팩토링 완료 (Socket.IO + Pixi.js 기반)");
