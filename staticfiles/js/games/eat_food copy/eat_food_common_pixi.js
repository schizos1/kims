// static/js/games/eat_food/eat_food_common_pixi.js
// 'eat_food' 게임의 클라이언트 측 공통 로직 (PixiJS 기반)

console.log("LOG_TEST: eat_food_common_pixi.js 파일이 로드되고 실행 시작됨!");

// --- PixiJS 애플리케이션 및 주요 컨테이너 ---
let pixiApp = null; // Pixi Application 인스턴스 (전역으로 접근 가능하도록 window에 할당)
window.pixiApp = pixiApp;
let gameContainer = null; // 게임 요소들(플레이어, 음식, NPC, 장애물)을 담을 Pixi 컨테이너
window.gameContainer = gameContainer; // 전역으로 접근 가능하도록

// --- 게임 상수 및 기본 정보 (서버 설정과 동기화 필요) ---
let CANVAS_WIDTH = 1280; // 기본값, 서버에서 game_start_info로 받을 수 있음
let CANVAS_HEIGHT = 720; // 기본값, 서버에서 game_start_info로 받을 수 있음
window.totalFoodsToWin = 30; // 기본값, 서버에서 받을 수 있음

// 클라이언트 측에서 스프라이트 시트나 개별 이미지 에셋 이름을 정의합니다.
// 서버에서 오는 데이터의 'name' 필드 (예: 음식 이름)와 매칭될 수 있도록 합니다.
const ASSET_BASE_PATH = "/static/minigame/eat_food/img/"; // 이미지 기본 경로 (Node.js 서버 경로 기준)

const SPRITE_ASSET_NAMES = {
    // 음식 (서버의 SERVER_FOOD_TYPES의 name과 일치시켜야 함)
    apple: `${ASSET_BASE_PATH}apple.png`,
    chips: `${ASSET_BASE_PATH}chips.png`,
    icecream: `${ASSET_BASE_PATH}icecream.png`,
    kola: `${ASSET_BASE_PATH}kola.png`,
    noodle: `${ASSET_BASE_PATH}noodle.png`,
    pizza: `${ASSET_BASE_PATH}pizza.png`,
    salad: `${ASSET_BASE_PATH}salad.png`,
    serial: `${ASSET_BASE_PATH}serial.png`,
    steak: `${ASSET_BASE_PATH}steak.png`,
    koala: `${ASSET_BASE_PATH}koala.png`, // 특별 아이템
    monkey: `${ASSET_BASE_PATH}monkey.png`,// 특별 아이템
    // 플레이어 캐릭터 (서버의 charImgPath와 일치)
    dino1: `${ASSET_BASE_PATH}dino1.png`,
    dino2: `${ASSET_BASE_PATH}dino2.png`,
    // NPC 캐릭터 (서버의 NPC_CHAR_IMG_NAME과 일치)
    monster: `${ASSET_BASE_PATH}monster.png`,
    // 기타 필요한 공통 에셋 (예: 배경)
    // gameBackground: `${ASSET_BASE_PATH}background.jpg`,
};

// --- HTML UI 요소 참조 ---
let progressBarFillEl, scoreNumEl, foodLeftNumEl, timerNumEl, systemMsgEl, resultPopupEl, resultContentEl, usernameInputEl, startButtonEl, closeResultButtonEl;

// --- 에셋 로딩 관련 ---
window.assetsLoaded = false; // 전역 에셋 로딩 완료 플래그
const loadedTextures = {}; // 로드된 PixiJS 텍스처 저장

// --- 게임 상태 변수 (공통 기본 구조) ---
// 이 변수들은 각 모드별 JS (single_pixi.js, multi_pixi.js)에서 주로 관리하고,
// 서버로부터 받은 데이터로 업데이트됩니다.
window.player = { // 현재 플레이어 객체 (서버 데이터와 동기화)
    id: null, user: "플레이어", x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2,
    score: 0, eatCount: 0, charImgPath: "dino1.png",
    collisionRadius: 25, // 서버 설정과 일치해야 함
    sprite: null // PixiJS Sprite 객체
};
window.foods = [];      // { id, name, x, y, r(시각적), collision_r, special, sprite: PixiSprite }
window.npcs = [];       // { id, x, y, charImgName, collision_r, sprite: PixiSprite, isAngry?, eatingTargetId? }
window.obstacles = [];  // { id, type, x, y, r, w, h, mainColor, graphics: PixiGraphics }
window.otherPlayers = {}; // 멀티플레이용

// --- 초기화 함수 ---
function initializeDOMElements() {
    progressBarFillEl = document.getElementById("progress-bar-fill");
    scoreNumEl = document.getElementById("score-num");
    foodLeftNumEl = document.getElementById("foodleft-num"); // Django 템플릿 ID: food-left
    timerNumEl = document.getElementById("timer-num");
    systemMsgEl = document.getElementById("system-msg");
    resultPopupEl = document.getElementById("result-popup");
    resultContentEl = document.getElementById("result-content");
    usernameInputEl = document.getElementById('username');
    startButtonEl = document.getElementById("actual-start-button"); // Django 템플릿 ID
    closeResultButtonEl = document.getElementById("close-result-button"); // Django 템플릿 ID
}

async function initializePixiApp(targetElementId = 'canvas') {
    // Django 템플릿에 <canvas id="canvas">가 이미 존재하므로, 해당 캔버스를 사용합니다.
    const existingCanvas = document.getElementById(targetElementId);
    if (!existingCanvas) {
        console.error(`PixiJS를 초기화할 <canvas id="${targetElementId}"> 요소를 찾을 수 없습니다.`);
        updateSystemMessage("오류: 게임 영역을 초기화할 수 없습니다.", true);
        return false;
    }

    CANVAS_WIDTH = parseInt(existingCanvas.width);
    CANVAS_HEIGHT = parseInt(existingCanvas.height);

    window.pixiApp = new PIXI.Application();
    await window.pixiApp.init({
        view: existingCanvas, // 기존 캔버스 사용
        width: CANVAS_WIDTH,
        height: CANVAS_HEIGHT,
        backgroundColor: 0x112233, // 기본 배경색
        antialias: true,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
    });
    
    window.gameContainer = new PIXI.Container();
    window.pixiApp.stage.addChild(window.gameContainer);
    window.pixiApp.stage.interactive = true; // 마우스/터치 이벤트 수신

    console.log("PixiJS 애플리케이션 초기화 완료 (기존 캔버스 사용).");
    return true;
}

async function loadAssets() {
    updateSystemMessage("게임 에셋 로딩 중...", false);
    const assetsToLoad = [];
    for (const key in SPRITE_ASSET_NAMES) {
        assetsToLoad.push({ alias: key, src: SPRITE_ASSET_NAMES[key] });
    }

    try {
        // PIXI.Assets.addBundle('game_assets', assetsToLoad); // 번들로 추가하는 방식도 가능
        // await PIXI.Assets.loadBundle('game_assets', progress => { ... });
        // 또는 개별적으로 로드
        for (const asset of assetsToLoad) {
            PIXI.Assets.add(asset);
        }
        const loaded = await PIXI.Assets.load(assetsToLoad.map(a => a.alias), progress => {
            updateSystemMessage(`에셋 로딩 중... ${Math.round(progress * 100)}%`, false);
        });

        // 로드된 텍스처 저장
        for (const key in loaded) {
            loadedTextures[key] = loaded[key];
        }

        console.log("모든 이미지 에셋 로딩 완료!");
        window.assetsLoaded = true;
        updateSystemMessage("에셋 로딩 완료! '게임 시작' 버튼을 눌러주세요.", false);
        // Django 템플릿의 시작 버튼 활성화 로직은 entry.html의 DOMContentLoaded에서 처리
        if (window.startButtonEl) window.startButtonEl.disabled = false;
        if (window.startButtonEl) window.startButtonEl.textContent = "게임 시작!";


    } catch (error) {
        console.error("에셋 로딩 중 오류 발생:", error);
        updateSystemMessage("오류: 게임 에셋을 로드할 수 없습니다.", true);
    }
}

// --- UI 업데이트 함수 (HTML 요소 대상) ---
function updateSystemMessage(msg, isError = false) {
    if (systemMsgEl) {
        systemMsgEl.textContent = msg;
        systemMsgEl.style.color = isError ? "red" : "#82a7dd"; // eat_food.css 와 일치 또는 여기서 정의
    }
}
window.updateSystemMessage = updateSystemMessage; // 전역으로 노출

function updateGameUI() { // HTML UI 업데이트
    if (scoreNumEl && window.player) scoreNumEl.innerText = window.player.score.toString();
    if (foodLeftNumEl && window.player && typeof window.totalFoodsToWin !== 'undefined') {
        let remaining = window.totalFoodsToWin - window.player.eatCount;
        foodLeftNumEl.innerText = remaining >= 0 ? remaining.toString() : "성공!";
    }
    if (progressBarFillEl && window.player && typeof window.totalFoodsToWin !== 'undefined' && window.totalFoodsToWin > 0) {
        progressBarFillEl.style.width = Math.min(100, (window.player.eatCount / window.totalFoodsToWin) * 100) + "%";
    }
}
window.updateCommonGameUI = updateGameUI;

function showResultPopup(isWin, finalScore, foodsEaten) { // HTML 결과 팝업 표시
    if (!resultPopupEl || !resultContentEl) return;

    let titleText = isWin ? "🎉 클리어! 🎉" : "🤔 게임 오버 🤔";
    let contentHtml = `최종 점수: <span style="color:#21b8ff; font-weight:bold;">${finalScore}</span>점<br>
                       먹은 음식: <b>${foodsEaten}</b>개 (목표: ${window.totalFoodsToWin}개)`;
    
    // 멀티플레이어 모드일 경우 상대방 정보 추가 (multi_pixi.js에서 호출 시 추가 데이터 전달)
    // if (GAME_MODE === 'multi' && window.otherPlayers) { ... }

    resultContentEl.innerHTML = contentHtml;
    // Django 템플릿에 result-title ID가 없으므로, content에 포함하거나 새로 추가 필요
    
    resultPopupEl.style.display = "block";
}
window.showCommonResultPopup = showResultPopup;

function closeResultPopup() { // HTML 결과 팝업 닫기
    if (resultPopupEl) resultPopupEl.style.display = "none";
    updateSystemMessage("새 게임을 시작하거나 방을 선택하세요.", false);
    if (startButtonEl) startButtonEl.disabled = false;
}
window.closeCommonResultPopup = closeResultPopup;


// --- PixiJS 객체 생성 헬퍼 함수들 ---
// 이 함수들은 각 모드별 JS 파일(single_pixi.js 등)에서 호출됩니다.

/**
 * 플레이어 PixiJS 스프라이트를 생성하거나 업데이트합니다.
 * @param {object} playerData 서버에서 받은 플레이어 데이터
 * @returns {PIXI.Sprite} 생성 또는 업데이트된 스프라이트
 */
window.createOrUpdatePlayerSprite = function(playerData) {
    if (!window.gameContainer || !playerData) return null;
    
    let sprite = window.player.sprite; // 기존 스프라이트 확인 (window.player는 이 클라이언트의 플레이어)
    const textureAlias = playerData.charImgPath ? playerData.charImgPath.replace(".png", "") : "dino1";
    const texture = loadedTextures[textureAlias] || loadedTextures["dino1"];

    if (!texture) {
        console.error(`플레이어 텍스처 '${textureAlias}'를 찾을 수 없습니다.`);
        return null; // 텍스처 없으면 생성 불가
    }

    if (!sprite) { // 새 스프라이트 생성
        sprite = new PIXI.Sprite(texture);
        sprite.anchor.set(0.5);
        window.gameContainer.addChild(sprite);
        window.player.sprite = sprite; // window.player 객체에 할당
    } else { // 기존 스프라이트 업데이트
        sprite.texture = texture; // 캐릭터 변경 시 텍스처 교체
    }
    
    sprite.x = playerData.x;
    sprite.y = playerData.y;
    // 스케일은 캐릭터 종류나 상태에 따라 설정 (예: PLAYER_SPRITE_INFO 참고)
    const playerSpriteInfo = PLAYER_SPRITE_INFO[textureAlias] || PLAYER_SPRITE_INFO.dino1;
    sprite.scale.set(playerSpriteInfo ? playerSpriteInfo.baseScale : 0.2);
    sprite.id = playerData.id; // Socket ID 등 식별자
    
    return sprite;
}

/**
 * 음식 PixiJS 스프라이트를 생성합니다.
 * @param {object} foodData 서버에서 받은 음식 데이터
 * @returns {PIXI.Sprite} 생성된 스프라이트
 */
window.createFoodSprite = function(foodData) {
    if (!window.gameContainer || !foodData) return null;

    const textureAlias = foodData.name; // 서버에서 온 음식 이름 (apple, chips 등)
    const texture = loadedTextures[textureAlias];
    const foodSpriteInfo = FOOD_SPRITE_INFO[textureAlias];

    if (!texture || !foodSpriteInfo) {
        console.warn(`음식 텍스처 또는 정보 '${textureAlias}'를 찾을 수 없습니다. 기본 도형으로 대체합니다.`);
        const graphics = new PIXI.Graphics().circle(0,0, foodData.r || 10).fill(0x00ff00); // .fill()은 이전 버전, fillStyle 사용
        // PIXI v7+ 에서는 graphics.fill(0x00ff00).circle(0,0, foodData.r || 10);
        const tempTexture = window.pixiApp.renderer.generateTexture(graphics);
        const sprite = new PIXI.Sprite(tempTexture);
        sprite.anchor.set(0.5);
        sprite.x = foodData.x;
        sprite.y = foodData.y;
        sprite.id = foodData.id;
        window.gameContainer.addChild(sprite);
        return sprite;
    }

    const sprite = new PIXI.Sprite(texture);
    sprite.anchor.set(0.5);
    
    // 서버에서 받은 r (시각적 반지름)을 사용하거나, 없으면 FOOD_SPRITE_INFO의 기본값 사용
    const visualRadius = foodData.r || (foodSpriteInfo.special ? config.FOOD_RADIUS_SPECIAL : config.FOOD_RADIUS_NORMAL);
    // 스프라이트 크기를 시각적 반지름에 맞춤
    sprite.width = visualRadius * 2;
    sprite.height = visualRadius * 2;
    // 또는 스케일 사용: sprite.scale.set(foodSpriteInfo.baseScale);

    sprite.x = foodData.x;
    sprite.y = foodData.y;
    sprite.id = foodData.id;
    window.gameContainer.addChild(sprite);
    return sprite;
}

/**
 * NPC PixiJS 스프라이트를 생성합니다.
 * @param {object} npcData 서버에서 받은 NPC 데이터
 * @returns {PIXI.Sprite} 생성된 스프라이트
 */
window.createNpcSprite = function(npcData) {
    if (!window.gameContainer || !npcData) return null;

    const textureAlias = npcData.charImgName ? npcData.charImgName.replace(".png", "") : "monster";
    const texture = loadedTextures[textureAlias] || loadedTextures["monster"];
    const npcSpriteInfo = NPC_SPRITE_INFO[textureAlias] || NPC_SPRITE_INFO.monster;

    if (!texture || !npcSpriteInfo) {
        console.warn(`NPC 텍스처 또는 정보 '${textureAlias}'를 찾을 수 없습니다.`);
        return null;
    }

    const sprite = new PIXI.Sprite(texture);
    sprite.anchor.set(0.5);
    sprite.scale.set(npcSpriteInfo.baseScale);
    sprite.x = npcData.x;
    sprite.y = npcData.y;
    sprite.id = npcData.id;
    window.gameContainer.addChild(sprite);
    return sprite;
}

/**
 * 장애물 PixiJS Graphics 객체를 생성합니다.
 * @param {object} obstacleData 서버에서 받은 장애물 데이터
 * @returns {PIXI.Graphics} 생성된 그래픽 객체
 */
window.createObstacleGraphics = function(obstacleData) {
    if (!window.gameContainer || !obstacleData) return null;

    const graphics = new PIXI.Graphics();
    const color = PIXI.utils.string2hex(obstacleData.mainColor || (obstacleData.type === "circle" ? "#A0A0A0" : "#808080"));
    
    graphics.fill(color); // PIXI v7+
    if (obstacleData.type === "circle") {
        graphics.circle(0, 0, obstacleData.r);
    } else { // rect
        graphics.rect(0, 0, obstacleData.w, obstacleData.h);
    }
    // graphics.fill(); // PIXI v7+ 에서는 도형 그리기 전에 fill() 호출

    // Graphics 객체의 위치는 pivot을 고려하여 설정
    graphics.x = obstacleData.x;
    graphics.y = obstacleData.y;
    if (obstacleData.type === "rect") {
        // 사각형의 경우, (x,y)가 좌상단 기준이므로 pivot 설정 불필요.
        // 만약 (x,y)를 중심으로 하고 싶다면 pivot 설정.
        // graphics.pivot.set(obstacleData.w / 2, obstacleData.h / 2);
        // graphics.x += obstacleData.w / 2;
        // graphics.y += obstacleData.h / 2;
    } else if (obstacleData.type === "circle") {
        // 원의 경우, (x,y)가 중심이므로 pivot 설정 불필요.
    }
    
    graphics.id = obstacleData.id;
    window.gameContainer.addChild(graphics);
    return graphics;
}

// --- 공통 초기화 실행 ---
// DOMContentLoaded는 eat_food_entry.html의 하단 스크립트에서 이미 처리하고 있음.
// 이 파일은 해당 시점 이후에 로드되므로, 필요한 초기화 함수들을 전역으로 노출시키거나,
// 각 모드별 JS 파일(single_pixi.js, multi_pixi.js)에서 호출하도록 구성.

// eat_food_entry.html에서 DOMContentLoaded 후 commonPixiInit을 호출하도록 수정됨.
window.commonPixiInit = async function() {
    initializeDOMElements(); // HTML UI 요소들 먼저 참조
    const pixiReady = await initializePixiApp('canvas'); // Django 템플릿의 canvas ID 사용
    if (pixiReady) {
        await loadAssets(); // Pixi 초기화 후 에셋 로딩
    }
    return pixiReady && window.assetsLoaded;
};

console.log("eat_food_common_pixi.js 로드 및 전역 함수 설정 완료.");