// socket_server/game_logics/emoji_battle/config.js

export const HIT_TO_WIN = 50; // 먼저 50점 도달 시 승리

export const EMOJI_TYPES = [
    {
        key: 'ice',
        emoji: '🥶',
        effect: 'freeze',
        points: 500,
        sound: ['frozen_hit', 'frozen'],
        desc: '빙결, 1초 이동불가'
    },
    {
        key: 'snow',
        emoji: '❄️',
        effect: 'freeze',
        points: 500,
        sound: ['frozen_hit', 'frozen'],
        desc: '빙결, 1초 이동불가'
    },
    {
        key: 'banana',
        emoji: '🍌',
        effect: 'slip',
        points: 500,
        sound: ['hit', 'slide'],
        desc: '미끄러짐, 흔들림 애니메이션'
    },
    {
        key: 'heart',
        emoji: '💖',
        effect: 'heal',
        points: 100,
        sound: ['hit'],
        desc: '회복/쉴드(커스텀)'
    },
    {
        key: 'apple',
        emoji: '🍎',
        effect: 'normal',
        points: 100,
        sound: ['hit'],
        desc: '일반 타격, 스파클'
    },
    {
        key: 'burger',
        emoji: '🍔',
        effect: 'normal',
        points: 100,
        sound: ['hit'],
        desc: '일반 타격, 스파클'
    },
    {
        key: 'pizza',
        emoji: '🍕',
        effect: 'normal',
        points: 100,
        sound: ['hit'],
        desc: '일반 타격, 스파클'
    }
    // 필요한 만큼 추가!
];
