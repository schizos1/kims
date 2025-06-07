/**
 * 모노폴리 플레이어를 관리하는 클래스
 */
export default class Player {
  /**
   * 플레이어를 초기화합니다.
   * @param {Phaser.Scene} scene - Phaser 장면
   * @param {string} id - 플레이어 ID
   * @param {number} position - 초기 위치
   */
  constructor(scene, id, position) {
    this.scene = scene;
    this.id = id;
    this.position = position;
    this.sprite = null;
    this.initSprite();
  }

  /**
   * 플레이어 스프라이트를 초기화합니다.
   */
  initSprite() {
    // TODO: 실제 플레이어 토큰 이미지
    this.sprite = this.scene.add.circle(50, 50, 10, 0xff0000); // 임시 빨간 원
  }

  /**
   * 플레이어를 이동시킵니다.
   * @param {number} steps - 이동할 칸 수
   */
  move(steps) {
    this.position = (this.position + steps) % 40;
    // TODO: 실제 보드 위치로 스프라이트 이동
    this.sprite.setPosition(this.position * 20 + 50, 50); // 임시 이동
  }
}