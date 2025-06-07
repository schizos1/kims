// File: /static/minigame/js/games/monopoly/popupManager.js
// 역할: 알림, 선택, 안내 팝업 래핑 (MVP는 alert/confirm로 대체)

export default class PopupManager {
  static alert(msg) { alert(msg); }
  static confirm(msg) { return confirm(msg); }
  static prompt(msg, def = '') { return prompt(msg, def); }
  // 이후 커스텀 모달/애니/인포그래픽 등으로 확장 가능
}
