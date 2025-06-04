let ws = null, room_id = "solo", user = "", player = {}, opponent = {}, food = {}, joined = false;

const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

function startSolo() {
    room_id = "solo";
    connectWS();
}
function showInvite() {
    room_id = Math.random().toString(36).substr(2, 6);
    document.getElementById("invite-tip").innerText = "초대코드: " + room_id + " (친구에게 전달)";
    connectWS();
}
function joinRoom() {
    room_id = document.getElementById("input-invite-code").value.trim();
    if(room_id.length < 3) return alert("코드를 입력하세요!");
    connectWS();
}
function connectWS() {
    // 닉네임: 화면 input 또는 hidden input에서 가져오도록 수정
    user = document.getElementById("username").value.trim() || "플레이어";
    ws = new WebSocket("ws://" + window.location.host + "/ws/minigame/" + room_id + "/");
    ws.onopen = function() {
        ws.send(JSON.stringify({action:"join", user:user}));
        joined = true;
        document.getElementById("chat-ui").style.display = "block";
        logSys("[알림] 게임 시작!");
    }
    ws.onmessage = function(evt) {
        let data = JSON.parse(evt.data);
        if(data.action === "state") {
            player = data.player;
            opponent = data.opponent || {};
            food = data.food;
            draw();
        } else if(data.action === "chat") {
            logChat(data.user, data.message);
        } else if(data.action === "system") {
            logSys(data.message);
        }
    }
    ws.onclose = function() { logSys("[알림] 연결 종료! 새로고침 하세요."); }
}
function sendMove() {
    if(!joined) return;
    ws.send(JSON.stringify({action:"move", user:user, player:player}));
}
function draw() {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    // 플레이어
    ctx.fillStyle = "#68e";
    ctx.beginPath();
    ctx.arc(player.x||40, player.y||40, 18, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle = "#333";
    ctx.fillText(player.user||user, (player.x||40)-13, (player.y||40)+4);

    // 상대
    if(opponent && opponent.x){
        ctx.fillStyle = "#e66";
        ctx.beginPath();
        ctx.arc(opponent.x, opponent.y, 18, 0, Math.PI*2); ctx.fill();
        ctx.fillStyle = "#333";
        ctx.fillText(opponent.user, opponent.x-13, opponent.y+4);
    }
    // 먹이
    ctx.fillStyle = "#ec4";
    ctx.beginPath();
    ctx.arc(food.x||200, food.y||100, food.r||12, 0, Math.PI*2); ctx.fill();

    // 점수
    ctx.fillStyle = "#111";
    ctx.fillText("내 점수: "+(player.score||0), 20, 18);
    if(opponent && opponent.user) ctx.fillText("상대 점수: "+(opponent.score||0), 380, 18);
}

canvas.addEventListener("mousemove", function(e) {
    if(!joined) return;
    let rect = canvas.getBoundingClientRect();
    player.x = Math.round(e.clientX - rect.left);
    player.y = Math.round(e.clientY - rect.top);
    sendMove();
});

function sendChat() {
    let msg = document.getElementById("chatbox").value.trim();
    if(msg) ws.send(JSON.stringify({action:"chat", user:user, message:msg}));
    document.getElementById("chatbox").value = "";
}
function logChat(user, msg) {
    let c = document.getElementById("chatlog");
    c.innerHTML += `<div><b>${user}:</b> ${msg}</div>`;
    c.scrollTop = c.scrollHeight;
}
function logSys(msg) {
    document.getElementById("system-msg").innerText = msg;
}
