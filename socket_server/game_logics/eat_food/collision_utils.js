// socket_server/game_logics/eat_food/collision_utils.js
// 'eat_food' 미니게임의 서버 측 충돌 감지 등 유틸리티 함수 모음

/**
 * 두 원 간의 충돌을 확인합니다.
 * @param {number} c1_x 첫 번째 원의 x 좌표
 * @param {number} c1_y 첫 번째 원의 y 좌표
 * @param {number} c1_r 첫 번째 원의 반지름
 * @param {number} c2_x 두 번째 원의 x 좌표
 * @param {number} c2_y 두 번째 원의 y 좌표
 * @param {number} c2_r 두 번째 원의 반지름
 * @returns {boolean} 충돌 시 true, 아니면 false
 */
export function checkCircleCircleCollision(c1_x, c1_y, c1_r, c2_x, c2_y, c2_r) {
    const distSq = (c1_x - c2_x) ** 2 + (c1_y - c2_y) ** 2;
    const radiiSumSq = (c1_r + c2_r) ** 2;
    return distSq < radiiSumSq;
}

/**
 * 두 사각형 간의 충돌을 확인합니다 (AABB 방식).
 * @param {number} r1_x 첫 번째 사각형의 좌상단 x 좌표
 * @param {number} r1_y 첫 번째 사각형의 좌상단 y 좌표
 * @param {number} r1_w 첫 번째 사각형의 너비
 * @param {number} r1_h 첫 번째 사각형의 높이
 * @param {number} r2_x 두 번째 사각형의 좌상단 x 좌표
 * @param {number} r2_y 두 번째 사각형의 좌상단 y 좌표
 * @param {number} r2_w 두 번째 사각형의 너비
 * @param {number} r2_h 두 번째 사각형의 높이
 * @returns {boolean} 충돌 시 true, 아니면 false
 */
export function checkRectRectCollision(r1_x, r1_y, r1_w, r1_h, r2_x, r2_y, r2_w, r2_h) {
    return (r1_x < r2_x + r2_w && r1_x + r1_w > r2_x &&
            r1_y < r2_y + r2_h && r1_y + r1_h > r2_y);
}

/**
 * 원과 사각형 간의 충돌을 확인합니다.
 * @param {number} circle_x 원의 중심 x 좌표
 * @param {number} circle_y 원의 중심 y 좌표
 * @param {number} circle_r 원의 반지름
 * @param {number} rect_x 사각형의 좌상단 x 좌표
 * @param {number} rect_y 사각형의 좌상단 y 좌표
 * @param {number} rect_w 사각형의 너비
 * @param {number} rect_h 사각형의 높이
 * @returns {boolean} 충돌 시 true, 아니면 false
 */
export function checkCircleRectCollision(circle_x, circle_y, circle_r, rect_x, rect_y, rect_w, rect_h) {
    // 사각형의 변 중에서 원의 중심에 가장 가까운 점(closestX, closestY)을 찾습니다.
    const closestX = Math.max(rect_x, Math.min(circle_x, rect_x + rect_w));
    const closestY = Math.max(rect_y, Math.min(circle_y, rect_y + rect_h));

    // 가장 가까운 점과 원의 중심 사이의 거리를 계산합니다.
    const distanceSq = (circle_x - closestX) ** 2 + (circle_y - closestY) ** 2;

    // 거리가 원의 반지름보다 작으면 충돌입니다.
    return distanceSq < (circle_r * circle_r);
}

/**
 * 주어진 좌표가 캔버스 경계 내에 있는지 확인합니다 (여백 포함).
 * @param {number} x 확인할 x 좌표
 * @param {number} y 확인할 y 좌표
 * @param {number} elementRadius 요소의 반지름 (경계 계산 시 고려)
 * @param {object} config 게임 설정 객체 (CANVAS_WIDTH, CANVAS_HEIGHT, EDGE_MARGIN 포함)
 * @returns {boolean} 경계 내에 있으면 true, 아니면 false
 */
export function isPositionWithinCanvasBounds(x, y, elementRadius, config) {
    return (elementRadius + config.EDGE_MARGIN <= x && x <= config.CANVAS_WIDTH - elementRadius - config.EDGE_MARGIN &&
            elementRadius + config.EDGE_MARGIN <= y && y <= config.CANVAS_HEIGHT - elementRadius - config.EDGE_MARGIN);
}

// 필요한 경우 여기에 더 많은 유틸리티 함수를 추가할 수 있습니다.
// 예: 두 점 사이의 거리 계산, 각도 계산 등