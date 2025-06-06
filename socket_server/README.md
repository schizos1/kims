# Socket Game Server

이 서버는 Pixi.js 기반 미니게임을 위한 Node.js + Socket.IO 서버입니다.

## 주요 설정
- `NPC_SPAWN_INTERVAL`: 15초마다 NPC가 추가됩니다.
- `OBSTACLE_MOVE_INTERVAL`: 10초마다 장애물이 새로 배치됩니다.
- `OBSTACLE_COUNT_MIN`/`MAX`: 장애물 개수 범위입니다.
- `INITIAL_FOOD_COUNT`: 초기 음식 개수 (5개). NPC가 늘어나면 음식도 한 개씩 증가합니다.

## 실행 방법
```bash
npm install
node server.js
```

## 구조
- `game_handlers/` : 각 게임별 Socket 이벤트 처리
- `game_logics/` : 게임 규칙 및 엔티티 관리 모듈
- `public/` : 클라이언트 HTML 및 JS