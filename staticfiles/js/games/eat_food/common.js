console.log("LOG_TEST: eat_food_common.js 파일이 로드되고 실행 시작됨!");
// static/minigame/js/eat_food_common.js
// 'eat_food' 게임의 싱글플레이어 및 멀티플레이어 모드에서 공통으로 사용되는
// 변수, 상수, 유틸리티 함수, 에셋 로딩, 기본 그리기 로직 등을 포함합니다.

// --- 게임 상수 및 기본 정보 ---
const FOOD_INFO = [
    {name: "apple", score: 10, imgPath: "apple.png"},
    {name: "chips", score: 10, imgPath: "chips.png"},
    {name: "icecream", score: 10, imgPath: "icecream.png"},
    {name: "kola", score: 10, imgPath: "kola.png"},
    {name: "noodle", score: 10, imgPath: "noodle.png"},
    {name: "pizza", score: 10, imgPath: "pizza.png"},
    {name: "salad", score: 10, imgPath: "salad.png"},
    {name: "serial", score: 10, imgPath: "serial.png"},
    {name: "steak", score: 10, imgPath: "steak.png"},
    {name: "koala", score: 100, imgPath: "koala.png", special: true},
    {name: "monkey", score: 100, imgPath: "monkey.png", special: true}
];
const DINO_IMG_PATHS = ["dino1.png", "dino2.png"]; // 플레이어 기본 이미지 경로들
const NPC_IMG_PATH = "monster.png"; // NPC 기본 이미지 경로

// --- 전역 참조 변수 (공통 사용) ---
let canvas, ctx;
let progressBar, scoreNum, foodLeftNum, timerNum, systemMsg, resultPopup, resultcontent, usernameInput;

// --- 에셋 로딩 관련 변수 ---
let loadedDinoImages = []; // 로드된 플레이어 이미지 객체들
let loadedNpcImage;     // 로드된 NPC 이미지 객체
// FOOD_INFO 배열 내 각 객체에 .imageObject로 이미지 로드 예정

const soundFiles = {
    bgm: "/static/minigame/eat_food/sound/bgm.mp3",
    sndEat: "/static/minigame/eat_food/sound/eatmeet.mp3",
    sndSpecial: "/static/minigame/eat_food/sound/koalamonkeystart.mp3",
    sndWin: "/static/minigame/eat_food/sound/win.mp3",
    sndLose: "/static/minigame/eat_food/sound/lose.mp3",
    sndStart: "/static/minigame/eat_food/sound/gamestart.mp3",
    sndWall: "/static/minigame/eat_food/sound/wall.mp3",
    sndFood: "/static/minigame/eat_food/sound/food.mp3",
    sndEnd: "/static/minigame/eat_food/sound/ending.mp3",
    sndJump: "/static/minigame/eat_food/sound/jump.mp3"
};
let sounds = {}; // 로드된 오디오 객체 저장
let totalAssetsToLoad = 0;
let assetsCurrentlyLoaded = 0;
//let assetsLoaded = false; // 모든 에셋 로딩 완료 여부
window.assetsLoaded = false;

// --- 게임 상태 변수 (공통 기본 구조) ---
let player = { // 기본 플레이어 객체 구조. 모드별 JS에서 상세 속성 관리.
    x: 100, y: 300, score: 0, eatCount: 0, eating: false, charImg: null,
    collisionRadius: 30, // 서버 설정과 맞추거나, 클라이언트 전용 시각/판정 값
    user: "",
    // 싱글/멀티 공통으로 서버에서 받을 수 있는 속성들
    id: null, // 서버에서 할당된 ID (멀티플레이어 시 채널 ID 등)
    charImgPath: "dino1.png" // 기본 또는 선택된 이미지 경로
};

let opponentPlayer = null; // 멀티플레이어 시 상대방 정보
let foods = [];      // 현재 게임 내 음식 배열 (서버 데이터 또는 로컬 생성 데이터)
let npcPlayers = []; // 현재 게임 내 NPC 배열 (서버 데이터 또는 로컬 생성 데이터)
let obstacles = [];  // 현재 게임 내 장애물 배열 (서버 데이터 또는 로컬 생성 데이터)

let totalFoodsToWin = 30; // 목표 음식 개수 (서버에서 받을 수 있음)
let gamePlaying = false;  // 현재 게임 진행 상태 (공통 플래그)

// --- 유틸리티 함수 ---
function generateFallbackUUID() {
  let d = new Date().getTime();
  let d2 = (performance && performance.now && (performance.now() * 1000)) || 0;
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    let r = Math.random() * 16;
    if (d > 0) { r = (d + r) % 16 | 0; d = Math.floor(d / 16); }
    else { r = (d2 + r) % 16 | 0; d2 = Math.floor(d2 / 16); }
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  }).slice(0,8); // 8자리로 축소
}

function adjustColor(hex, amount) {
    let usePound = false;
    if (hex.startsWith("#")) {
        hex = hex.slice(1);
        usePound = true;
    }
    const num = parseInt(hex, 16);
    let r = (num >> 16) + amount; r = Math.max(0, Math.min(255, r));
    let g = ((num >> 8) & 0x00FF) + amount; g = Math.max(0, Math.min(255, g));
    let b = (num & 0x0000FF) + amount; b = Math.max(0, Math.min(255, b));
    return (usePound ? "#" : "") + (r << 16 | g << 8 | b).toString(16).padStart(6, '0');
}

// --- 충돌 감지 헬퍼 함수 ---
function circleCircleCollision(c1, c2) {
    if (!c1 || !c2 || c1.r === undefined || c2.r === undefined) return false;
    const distSq = (c1.x - c2.x)**2 + (c1.y - c2.y)**2;
    const radiiSumSq = (c1.r + c2.r)**2;
    return distSq < radiiSumSq;
}

function rectRectCollision(r1, r2) { // r1, r2: {x, y, w, h}
    if (!r1 || !r2) return false;
    return r1.x < r2.x + r2.w && r1.x + r1.w > r2.x &&
           r1.y < r2.y + r2.h && r1.y + r1.h > r2.y;
}

function circleRectCollision(circle, rect) { // circle: {x, y, r}, rect: {x, y, w, h}
    if (!circle || !rect || circle.r === undefined) return false;
    let closestX = Math.max(rect.x, Math.min(circle.x, rect.x + rect.w));
    let closestY = Math.max(rect.y, Math.min(circle.y, rect.y + rect.h));
    const distanceSq = (circle.x - closestX)**2 + (circle.y - closestY)**2;
    return distanceSq < (circle.r * circle.r);
}

// --- 에셋 로딩 함수 ---
function assetLoadTracker() {
    assetsCurrentlyLoaded++;
    console.log(`DEBUG_TRACKER: Assets loaded count: <span class="math-inline">\{assetsCurrentlyLoaded\}/</span>{totalAssetsToLoad}`); 
    updateSystemMessage(`에셋 로딩 중... (${assetsCurrentlyLoaded}/${totalAssetsToLoad})`);
    if (assetsCurrentlyLoaded >= totalAssetsToLoad) {
        console.log("DEBUG_TRACKER: All assets reported. Calling allAssetsLoaded().");
        allAssetsLoaded();
    }
}

function initializeAndPreloadAssets() {
    console.log("DEBUG: initializeAndPreloadAssets() CALLED"); // 함수 호출 확인

    // DOM 요소 할당
    canvas = document.getElementById("canvas");
    // ... (다른 DOM 요소 할당) ...

    if (!canvas) {
        console.error("캔버스 요소를 찾을 수 없습니다! (common.js)");
        updateSystemMessage("오류: 캔버스 요소를 찾을 수 없습니다.", true);
        return; // 중요한 요소 없으면 중단
    }
    ctx = canvas.getContext('2d');

    // 에셋 목록 변수 상태 확인
    console.log("DEBUG: FOOD_INFO before load:", JSON.stringify(FOOD_INFO));
    console.log("DEBUG: DINO_IMG_PATHS before load:", JSON.stringify(DINO_IMG_PATHS));
    console.log("DEBUG: NPC_IMG_PATH before load:", NPC_IMG_PATH);
    console.log("DEBUG: soundFiles before load:", JSON.stringify(soundFiles));

    totalAssetsToLoad = (FOOD_INFO ? FOOD_INFO.length : 0) + 
                        (DINO_IMG_PATHS ? DINO_IMG_PATHS.length : 0) + 
                        (NPC_IMG_PATH ? 1 : 0) + 
                        (soundFiles ? Object.keys(soundFiles).length : 0);
    console.log("DEBUG: Calculated totalAssetsToLoad:", totalAssetsToLoad);

    if (totalAssetsToLoad === 0) {
        console.warn("DEBUG: No assets to load, calling allAssetsLoaded() immediately.");
        allAssetsLoaded(); // 로드할 에셋이 없으면 바로 완료 처리
        return;
    }
    assetsCurrentlyLoaded = 0; // 초기화 확실히
    updateSystemMessage(`에셋 로딩 중... (0/${totalAssetsToLoad})`);

    // 플레이어 이미지 로드
    if (DINO_IMG_PATHS && DINO_IMG_PATHS.length > 0) {
        DINO_IMG_PATHS.forEach(path => {
            console.log("DEBUG: Attempting to load Player Image:", path); // 경로 확인
            const img = new Image();
            img.onload = () => { console.log(`DEBUG: Loaded Player Image: ${path}`); assetLoadTracker(); };
            img.onerror = () => { console.error("플레이어 이미지 로드 실패:", path); assetLoadTracker(); };
            img.src = `/static/minigame/eat_food/img/${path}`;
            loadedDinoImages.push(img);
        });
    } else {
        console.warn("DEBUG: DINO_IMG_PATHS is empty or undefined.");
    }


    // NPC 이미지 로드
    if (NPC_IMG_PATH) {
        console.log("DEBUG: Attempting to load NPC Image:", NPC_IMG_PATH); // 경로 확인
        const npcImg = new Image();
        npcImg.onload = () => { console.log(`DEBUG: Loaded NPC Image: ${NPC_IMG_PATH}`); assetLoadTracker(); };
        npcImg.onerror = () => { console.error("NPC 이미지 로드 실패:", NPC_IMG_PATH); assetLoadTracker(); };
        npcImg.src = `/static/minigame/eat_food/img/${NPC_IMG_PATH}`;
        loadedNpcImage = npcImg;
    } else {
        console.warn("DEBUG: NPC_IMG_PATH is empty or undefined.");
        // NPC 이미지가 필수 에셋이 아니라면 totalAssetsToLoad 계산에서 제외했어야 함.
        // 만약 필수인데 경로가 없다면 로딩이 멈출 수 있으므로, 이 경우 assetLoadTracker()를 호출해줄지 결정 필요.
    }


    // 음식 아이템 이미지 로드
    if (FOOD_INFO && FOOD_INFO.length > 0) {
        FOOD_INFO.forEach(foodItem => {
            console.log("DEBUG: Attempting to load Food Image:", foodItem.imgPath); // 경로 확인
            const img = new Image();
            img.onload = () => { console.log(`DEBUG: Loaded Food Image: ${foodItem.imgPath}`); assetLoadTracker(); };
            img.onerror = () => { console.error("음식 이미지 로드 실패:", foodItem.imgPath); assetLoadTracker(); };
            img.src = `/static/minigame/eat_food/img/${foodItem.imgPath}`;
            foodItem.imageObject = img;
        });
    } else {
        console.warn("DEBUG: FOOD_INFO is empty or undefined.");
    }

    // 사운드 파일 로드
    if (soundFiles && Object.keys(soundFiles).length > 0) {
        Object.keys(soundFiles).forEach(key => {
            console.log("DEBUG: Attempting to load Sound:", soundFiles[key]); // 경로 확인
            const audio = new Audio();
            audio.onloadeddata = () => { console.log(`DEBUG: Loaded Sound: ${soundFiles[key]}`); assetLoadTracker(); };
            audio.onerror = () => { console.error(`${key} 사운드 로드 실패: ${soundFiles[key]}`); assetLoadTracker(); };
            audio.src = soundFiles[key];
            sounds[key] = audio;
            if (key === 'bgm') { audio.loop = true; audio.volume = 0.25; }
        });
    } else {
        console.warn("DEBUG: soundFiles is empty or undefined.");
    }
}

function allAssetsLoaded() {
    console.log("DEBUG_LOAD_COMPLETE: allAssetsLoaded() function called. Setting assetsLoaded = true.");
    window.assetsLoaded = true;
    updateSystemMessage("모든 에셋 로딩 완료! 게임을 시작하세요.", false);
    const startButton = document.querySelector("#user-ui button"); // 공통 시작 버튼
    if (startButton) startButton.disabled = false;
}

// --- UI 업데이트 함수 ---
function updateSystemMessage(msg, isError = false) {
    if (!systemMsg) { systemMsg = document.getElementById("system-msg"); }
    if (systemMsg) {
        console.log("DEBUG_COMMON_JS: Updating system message to:", msg); // 이 로그 확인
        systemMsg.textContent = msg;
        systemMsg.style.color = isError ? "#ff6b6b" : "#82a7dd";
    } else {
        console.error("DEBUG_COMMON_JS: systemMsg DOM element NOT FOUND!");
    }
}

function updateGameUI() {
    if (scoreNum && player) {
        console.log("DEBUG_COMMON_JS: Updating UI Score to:", player.score); // 로그 추가
        scoreNum.innerText = player.score;
    }
    if (foodLeftNum && player && typeof totalFoodsToWin !== 'undefined') {
         let remaining = totalFoodsToWin - player.eatCount;
         console.log("DEBUG_COMMON_JS: Updating UI FoodLeft to:", remaining); // 로그 추가
         foodLeftNum.innerText = remaining >= 0 ? remaining.toString() : "성공!";
    }
    if (progressBar && player && typeof totalFoodsToWin !== 'undefined' && totalFoodsToWin > 0) {
        progressBar.style.width = Math.min(100, (player.eatCount / totalFoodsToWin) * 100) + "%";
    }
}

function showResultPopup(isWin) {
    console.log(`DEBUG (Common): showResultPopup called with isWin: ${isWin}`);
    let txt = `최종 점수 <span style="color:#21b8ff">${player.score}</span>점<br>
총 먹이 <b>${player.eatCount}</b>개 (목표: ${totalFoodsToWin}개)`;

    // 멀티플레이 모드에서 상대방 정보가 있다면 추가 (multi.js에서 opponentPlayer 업데이트)
    if (opponentPlayer && opponentPlayer.user) {
        txt += `<br><br>--- 상대방 (${opponentPlayer.user}) ---<br>
        점수: <span style="color:#ff6b6b">${opponentPlayer.score || 0}</span>점`;
    }

    if (isWin) {
        if (sounds.sndWin) sounds.sndWin.play().catch(e => {});
        txt = "🎉 <b>클리어!</b><br>" + txt;
    } else {
        if (sounds.sndLose) sounds.sndLose.play().catch(e => {});
        txt = "🤔 <b>게임 오버!</b><br>" + txt;
    }
    if (resultcontent) resultcontent.innerHTML = txt;
    if (resultPopup) resultPopup.style.display = "block";
}

function closeResult() {
    if (resultPopup) resultPopup.style.display = "none";
    updateSystemMessage("새 게임을 시작하려면 시작 버튼을 누르세요.", false);
    // UI 초기화
    if (scoreNum) scoreNum.innerText = "0";
    if (foodLeftNum && totalFoodsToWin) foodLeftNum.innerText = totalFoodsToWin.toString();
    if (progressBar) progressBar.style.width = "0%";
}

// --- 공통 게임 종료 로직 ---
function commonEndGameTasks(isWin) {
    // 이 함수는 모드별 endGame 함수 내부에서 호출될 수 있습니다.
    // 공통적인 종료 처리 (예: BGM 중지, 결과 팝업 표시)
    gamePlaying = false; // 게임 상태 플래그 업데이트
    if (sounds.bgm && !sounds.bgm.paused) sounds.bgm.pause();
    if (sounds.sndEnd) sounds.sndEnd.play().catch(e => {}); // 공통 종료음
    
    showResultPopup(isWin); // 결과 팝업 표시는 공통
}


// --- 그리기 함수 (공통) ---
function draw() {
    if (!ctx || !canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#000"; // 배경색
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 1. 장애물 그리기
    if (obstacles && obstacles.length > 0) {
        const groundShadowOffsetX = 4; const groundShadowOffsetY = 4;
        obstacles.forEach(ob => {
            ctx.save();
            // 그림자 (간단 버전)
            ctx.fillStyle = "rgba(0, 0, 0, 0.2)";
            if (ob.type === "circle") {
                ctx.beginPath();
                ctx.arc(ob.x + groundShadowOffsetX, ob.y + groundShadowOffsetY, ob.r, 0, Math.PI * 2);
                ctx.fill();
            } else { // rect
                ctx.fillRect(ob.x + groundShadowOffsetX, ob.y + groundShadowOffsetY, ob.w, ob.h);
            }
            
            // 본체
            const mainColor = ob.mainColor || (ob.type === "circle" ? "#d16060" : "#4A5568");
            const highlightColor = adjustColor(mainColor, 30);
            const shadowColor = adjustColor(mainColor, -30);

            if (ob.type === "circle") {
                let gradient = ctx.createRadialGradient(ob.x - ob.r*0.3, ob.y - ob.r*0.3, ob.r*0.1, ob.x, ob.y, ob.r);
                gradient.addColorStop(0, highlightColor);
                gradient.addColorStop(0.8, mainColor);
                gradient.addColorStop(1, shadowColor);
                ctx.fillStyle = gradient;
                ctx.beginPath(); ctx.arc(ob.x, ob.y, ob.r, 0, Math.PI * 2); ctx.fill();
            } else { // rect
                ctx.fillStyle = mainColor;
                ctx.fillRect(ob.x, ob.y, ob.w, ob.h);
                // 간단한 입체감
                ctx.fillStyle = highlightColor;
                ctx.fillRect(ob.x, ob.y, ob.w, 3); 
                ctx.fillRect(ob.x, ob.y, 3, ob.h);
                ctx.fillStyle = shadowColor;
                ctx.fillRect(ob.x + 3, ob.y + ob.h - 3, ob.w - 3, 3);
                ctx.fillRect(ob.x + ob.w - 3, ob.y + 3, 3, ob.h - 3);
            }
            ctx.restore();
        });
    }

    // 2. 음식 그리기
    if (foods && foods.length > 0) {
        foods.forEach(f => {
            ctx.save();
            let foodImageToDraw = f.imageObject; // FOOD_INFO에서 로드된 이미지 객체
            let foodRadiusToDraw = f.r || (f.special ? 38 : 28); // 서버에서 r을 안주면 기본값 사용

            // 먹히는 중 애니메이션 (시각적 효과)
            // (이 부분은 각 모드별 eating 로직에서 f.eatProgress 등을 업데이트하여 반영 가능)
            // 여기서는 간단히 크기만 조절하는 예시 (실제 먹는 진행도는 서버/로컬 상태에 따름)
            // if (f.isBeingEaten && f.eatProgress !== undefined) {
            //    foodRadiusToDraw *= (1.0 - f.eatProgress);
            // }

            if (foodRadiusToDraw > 0.5) {
                if (foodImageToDraw && foodImageToDraw.complete) {
                    if (f.special) { ctx.shadowColor = "#ffdd00"; ctx.shadowBlur = 20; }
                    ctx.drawImage(foodImageToDraw, f.x - foodRadiusToDraw, f.y - foodRadiusToDraw, foodRadiusToDraw * 2, foodRadiusToDraw * 2);
                } else { // 이미지 로드 실패 또는 아직 안된 경우 대체 도형
                    ctx.fillStyle = f.special ? "gold" : "lightgreen";
                    ctx.beginPath(); ctx.arc(f.x, f.y, foodRadiusToDraw, 0, Math.PI * 2); ctx.fill();
                }
            }
            ctx.restore();
        });
    }

    // 3. NPC 그리기
    if (npcPlayers && npcPlayers.length > 0) {
        npcPlayers.forEach(npc => {
            if (npc.charImg && npc.charImg.complete) { // charImg는 로드된 이미지 객체여야 함
                ctx.save();
                let npcDrawX = npc.x; let npcDrawY = npc.y;
                let npcBaseSize = 80; // NPC 시각적 크기
                let npcCurrentSize = npcBaseSize;
                
                if (npc.isAngry) { // 서버에서 받은 isAngry 상태
                    ctx.shadowColor = "red"; ctx.shadowBlur = 25;
                    npcCurrentSize *= (1 + Math.sin(Date.now() / 80) * 0.15); // 화났을 때 크기 변화
                } else if (npc.eatingTargetId) { // 서버에서 받은 eatingTargetId 상태
                    ctx.shadowColor = "orange"; ctx.shadowBlur = 15;
                    npcCurrentSize *= (1 + Math.sin(Date.now() / 120) * 0.05); // 먹을 때 크기 변화
                }
                ctx.drawImage(npc.charImg, npcDrawX - npcCurrentSize / 2, npcDrawY - npcCurrentSize / 2, npcCurrentSize, npcCurrentSize);
                ctx.restore();
            }
        });
    }

    // 4. 상대 플레이어 그리기 (멀티플레이어 시)
    if (opponentPlayer && opponentPlayer.x && opponentPlayer.y) {
        ctx.save();
        const opponentSize = 80; // 상대 플레이어 시각적 크기
        if (opponentPlayer.charImg && opponentPlayer.charImg.complete) { // charImg는 로드된 이미지 객체
             ctx.shadowColor = "cyan"; ctx.shadowBlur = 15;
             ctx.globalAlpha = 0.9;
             ctx.drawImage(opponentPlayer.charImg, opponentPlayer.x - opponentSize / 2, opponentPlayer.y - opponentSize / 2, opponentSize, opponentSize);
        } else { // 이미지 없으면 기본 도형
            ctx.fillStyle = "rgba(0, 150, 255, 0.7)";
            ctx.fillRect(opponentPlayer.x - opponentSize/2, opponentPlayer.y - opponentSize/2, opponentSize, opponentSize);
        }
        // 상대방 이름 표시 (간단히)
        if (opponentPlayer.user) {
            ctx.font = "bold 14px 'Noto Sans KR', sans-serif"; ctx.textAlign = "center";
            ctx.fillStyle = "#fff";
            ctx.fillText(opponentPlayer.user.substring(0,5), opponentPlayer.x, opponentPlayer.y - opponentSize/2 - 8);
        }
        ctx.restore();
    }

    // 5. 내 플레이어 그리기
    if (player && player.charImg && player.charImg.complete) { // charImg는 로드된 이미지 객체
        ctx.save();
        let playerDrawX = player.x; let playerDrawY = player.y;
        let playerBaseSize = 80; // 내 플레이어 시각적 크기
        let playerCurrentSize = playerBaseSize;

        if (player.eating) { // eating 플래그 (로컬 시각 효과용)
            ctx.shadowColor = "yellow"; ctx.shadowBlur = 20;
            playerCurrentSize *= (1 + Math.sin(Date.now() / 100) * 0.1);
        } else {
            ctx.shadowColor = "lightblue"; ctx.shadowBlur = 10;
        }
        ctx.drawImage(player.charImg, playerDrawX - playerCurrentSize / 2, playerDrawY - playerCurrentSize / 2, playerCurrentSize, playerCurrentSize);
        
        // 내 이름 표시
        if (player.user) {
            ctx.font = "bold 16px 'Noto Sans KR', sans-serif"; ctx.textAlign = "center";
            ctx.fillStyle = "#fff";
            ctx.fillText(player.user.substring(0,5), player.x, player.y - playerCurrentSize/2 - 10);
        }
        ctx.restore();
    }
}


// --- 페이지 로드 시 공통 초기화 ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("LOG_TEST: common.js - DOMContentLoaded 이벤트 발생! initializeAndPreloadAssets 호출 시도.");
    initializeAndPreloadAssets(); // 에셋 로딩 시작
    
    // 시작 버튼은 에셋 로딩 완료 후 allAssetsLoaded()에서 활성화
    const startButton = document.querySelector("#user-ui button"); 
    if (startButton) startButton.disabled = true;

    // 마우스 이동 이벤트 리스너는 각 모드별 JS에서 필요에 따라 canvas에 추가.
    // 예: if (canvas) canvas.addEventListener("mousemove", onPlayerMove_single);
    // 예: if (canvas) canvas.addEventListener("mousemove", onPlayerMove_multi);

    // 전역으로 노출시켜야 하는 함수가 있다면 여기에 window.함수명 = 함수명; 형태로 할당.
    // 예: window.closeResult = closeResult;
});

// 이 파일은 공통 로직만 포함하므로, 실제 게임 시작(startGame) 함수는
// eat_food_single.js 또는 eat_food_multi.js 에서 정의되고 호출됩니다.