// socket_server/game_logics/game_records.js
// 미니게임 전반의 승패 기록을 관리하는 모듈

export const userWinCount = new Map();
export const userLossCount = new Map();

export function recordWin(id) {
    userWinCount.set(id, (userWinCount.get(id) || 0) + 1);
}

export function recordLoss(id) {
    userLossCount.set(id, (userLossCount.get(id) || 0) + 1);
}
