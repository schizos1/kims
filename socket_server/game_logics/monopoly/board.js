// File: /static/minigame/js/games/monopoly/board.js
// 역할: 모노폴리 40칸 전체 보드 데이터 및 보드 초기화/관리

import Tile from './tile.js';

export default class Board {
  constructor(scene = null) {
    this.scene = scene;
    this.tiles = [];
    this.initBoard();
  }


initBoard() {
  this.tiles = [
    new Tile({ id: 0, name: '출발', type: 'go' }),
    new Tile({ id: 1, name: '수유', type: 'property', price: 60, rent: [2,10,30,90,160,250], color: 'brown' }),
    new Tile({ id: 2, name: '사회복지기금', type: 'community' }),
    new Tile({ id: 3, name: '신림동', type: 'property', price: 60, rent: [4,20,60,180,320,450], color: 'brown' }),
    new Tile({ id: 4, name: '소득세', type: 'tax', price: 200 }),
    new Tile({ id: 5, name: '청량리역', type: 'railroad', price: 200, rent: [25,50,100,200] }),
    new Tile({ id: 6, name: '왕십리', type: 'property', price: 100, rent: [6,30,90,270,400,550], color: 'lightblue' }),
    new Tile({ id: 7, name: '찬스', type: 'chance' }),
    new Tile({ id: 8, name: '노량진', type: 'property', price: 100, rent: [6,30,90,270,400,550], color: 'lightblue' }),
    new Tile({ id: 9, name: '구로', type: 'property', price: 120, rent: [8,40,100,300,450,600], color: 'lightblue' }),
    new Tile({ id: 10, name: '감옥(방문)', type: 'jail' }),
    new Tile({ id: 11, name: '홍대입구', type: 'property', price: 140, rent: [10,50,150,450,625,750], color: 'pink' }),
    new Tile({ id: 12, name: '전기회사', type: 'utility', price: 150 }),
    new Tile({ id: 13, name: '마포', type: 'property', price: 140, rent: [10,50,150,450,625,750], color: 'pink' }),
    new Tile({ id: 14, name: '신촌', type: 'property', price: 160, rent: [12,60,180,500,700,900], color: 'pink' }),
    new Tile({ id: 15, name: '용산역', type: 'railroad', price: 200, rent: [25,50,100,200] }),
    new Tile({ id: 16, name: '이태원', type: 'property', price: 180, rent: [14,70,200,550,750,950], color: 'orange' }),
    new Tile({ id: 17, name: '사회복지기금', type: 'community' }),
    new Tile({ id: 18, name: '을지로', type: 'property', price: 180, rent: [14,70,200,550,750,950], color: 'orange' }),
    new Tile({ id: 19, name: '종로', type: 'property', price: 200, rent: [16,80,220,600,800,1000], color: 'orange' }),
    new Tile({ id: 20, name: '무료주차장', type: 'freepark' }),
    new Tile({ id: 21, name: '신사동', type: 'property', price: 220, rent: [18,90,250,700,875,1050], color: 'red' }),
    new Tile({ id: 22, name: '찬스', type: 'chance' }),
    new Tile({ id: 23, name: '목동', type: 'property', price: 220, rent: [18,90,250,700,875,1050], color: 'red' }),
    new Tile({ id: 24, name: '여의도', type: 'property', price: 240, rent: [20,100,300,750,925,1100], color: 'red' }),
    new Tile({ id: 25, name: '영등포역', type: 'railroad', price: 200, rent: [25,50,100,200] }),
    new Tile({ id: 26, name: '건대입구', type: 'property', price: 260, rent: [22,110,330,800,975,1150], color: 'yellow' }),
    new Tile({ id: 27, name: '성수동', type: 'property', price: 260, rent: [22,110,330,800,975,1150], color: 'yellow' }),
    new Tile({ id: 28, name: '수도회사', type: 'utility', price: 150 }),
    new Tile({ id: 29, name: '잠원동', type: 'property', price: 280, rent: [24,120,360,850,1025,1200], color: 'yellow' }),
    new Tile({ id: 30, name: '감옥으로', type: 'go_to_jail' }),
    new Tile({ id: 31, name: '대치동', type: 'property', price: 300, rent: [26,130,390,900,1100,1275], color: 'green' }),
    new Tile({ id: 32, name: '압구정', type: 'property', price: 300, rent: [26,130,390,900,1100,1275], color: 'green' }),
    new Tile({ id: 33, name: '사회복지기금', type: 'community' }),
    new Tile({ id: 34, name: '반포동', type: 'property', price: 320, rent: [28,150,450,1000,1200,1400], color: 'green' }),
    new Tile({ id: 35, name: '서울역', type: 'railroad', price: 200, rent: [25,50,100,200] }),
    new Tile({ id: 36, name: '찬스', type: 'chance' }),
    new Tile({ id: 37, name: '송파구', type: 'property', price: 350, rent: [35,175,500,1100,1300,1500], color: 'darkblue' }),
    new Tile({ id: 38, name: '사치세', type: 'tax', price: 100 }),
    new Tile({ id: 39, name: '강남/서초', type: 'property', price: 400, rent: [50,200,600,1400,1700,2000], color: 'darkblue' }),
  ];
}
}
