/**
 * 모노폴리 주사위를 관리하는 클래스
 */
export default class Dice {
  /**
   * 주사위를 초기화합니다.
   * @param {Phaser.Scene} scene - Phaser 장면
   */
  constructor(scene) {
    this.scene = scene;
    this.result = 0;
  }

  /**
   * 주사위를 굴립니다.
   * @returns {number} 주사위 결과 (1~6)
   */
  roll() {
    this.result = Math.floor(Math.random() * 6) + 1;
    // TODO: 주사위 애니메이션
    this.scene.add.text(100, 150, `Dice: ${this.result}`, { fontSize: '24px', color: '#ffffff' });
    return this.result;
  }
}