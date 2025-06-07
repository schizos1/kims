/**
 * 모노폴리 게임 보드를 관리하는 클래스
 */
export default class Board {
  /**
   * 보드를 초기화합니다.
   * @param {Phaser.Scene} scene - Phaser 장면
   */
  constructor(scene) {
    this.scene = scene;
    this.tiles = []; // 보드 타일 (40개)
    this.initBoard();
  }

  /**
   * 보드 타일을 초기화합니다.
   */
  initBoard() {
    const boardImage = this.scene.add.image(400, 400, 'board');
    boardImage.setScale(0.5); // 크기 조정
    this.tiles.push(boardImage);
  }
}