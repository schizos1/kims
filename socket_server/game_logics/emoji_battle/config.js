// socket_server/game_logics/emoji_battle/config.js
// 이모지 배틀 게임 설정값 정의

export const HIT_TO_WIN = 50; // 먼저 50회 맞히면 승리
export const EMOJI_TYPES = [
    { name: 'ice', effect: 'freeze', points: 1 },
    { name: 'snow', effect: 'freeze', points: 1 },
    { name: 'banana', effect: 'slip', points: 1 },
    { name: 'heart', effect: 'love', points: 1 }
];
