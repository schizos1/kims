// File: /static/minigame/js/games/monopoly/tile.js
// 역할: 모노폴리 1칸(타일)의 데이터/상태 및 타입별 속성 관리

export default class Tile {
  /**
   * @param {object} param0 - 타일 정보
   * @param {number} param0.id - 칸 번호(0~39)
   * @param {string} param0.name - 칸 이름(예: 도시명)
   * @param {string} param0.type - 칸 종류(property, railroad, utility, chance, tax, jail, etc)
   * @param {number} [param0.price] - 구매가(해당되는 경우)
   * @param {number|array} [param0.rent] - 임대료(배열 or 숫자)
   * @param {string} [param0.color] - 색상군(도시)
   */
  constructor({ id, name, type, price = 0, rent = 0, color = null }) {
    this.id = id;
    this.name = name;
    this.type = type;
    this.price = price;
    this.rent = rent;
    this.color = color;
    this.owner = null;
    this.houseCount = 0;
    this.mortgaged = false;
    this.special = {}; // 찬스/공공기금/감옥 등 특수 데이터 확장용
  }
}
