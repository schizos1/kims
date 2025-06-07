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
    this.sprite = this.scene.add.image(50, 50, 'player_token');
    this.sprite.setScale(0.2); // 크기 조정
  }

  /**
   * 플레이어를 이동시킵니다.
   * @param {number} steps - 이동할 칸 수
   */
  move(steps) {
    this.position = (this.position + steps) % 40;
    // TODO: 보드 타일에 맞는 좌표로 이동
    this.sprite.setPosition(this.position * 20 + 50, 50); // 임시 이동
  }
}