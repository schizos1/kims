// Phaser eat_food_single.js - 충돌 안정화, 시각 효과, 장애물 겹침 방지 강화

let selectedEmoji = '🐶';

const config = {
    type: Phaser.AUTO,
    width: 1280,
    height: 720,
    parent: 'phaser-game',
    backgroundColor: '#000000',
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    },
    scene: {
        preload: preload,
        create: create,
        update: update
    }
};

let player, cursors, foodGroup, obstacleGroup, monsterGroup, sounds;
let score = 0;
// foodCount 변수는 score와 중복되므로 제거해도 무방합니다.
// let foodCount = 0; 
let scoreText;

const game = new Phaser.Game(config);

function preload() {
    this.load.audio('eat', '/static/minigame/eat_food/sound/food.mp3');
    this.load.audio('hit', '/static/minigame/eat_food/sound/attack.mp3');
    this.load.audio('disappear', '/static/minigame/eat_food/sound/disapear.mp3');
    this.load.audio('bgm', '/static/minigame/eat_food/sound/bgm.mp3');
}

function create() {
    sounds = {
        eat: this.sound.add('eat'),
        hit: this.sound.add('hit'),
        disappear: this.sound.add('disappear'),
        bgm: this.sound.add('bgm', { loop: true })
    };
    sounds.bgm.play();

    scoreText = this.add.text(10, 10, '점수: 0 / 50', { fontSize: '20px', fontFamily: 'Arial', color: '#ffffff' });

    player = this.add.text(640, 360, selectedEmoji, { fontSize: '60px' });
    this.physics.add.existing(player);
    player.body.setCollideWorldBounds(true);

    cursors = this.input.keyboard.createCursorKeys();

    foodGroup = this.physics.add.group();
    // obstacleGroup을 Container를 다룰 수 있도록 일반 그룹으로 변경합니다.
    obstacleGroup = this.physics.add.group({ immovable: true, allowGravity: false });
    monsterGroup = this.physics.add.group();

    generateObstacles(this);
    generateFood(this);
    spawnInitialMonsters(this);

    this.physics.add.overlap(player, foodGroup, eatFood, null, this);
    this.physics.add.collider(player, obstacleGroup);
    this.physics.add.collider(player, monsterGroup, hitMonster, null, this);
    
    // 몬스터와 장애물이 겹치지 않도록 충돌 설정 추가
    this.physics.add.collider(monsterGroup, obstacleGroup);

    this.time.addEvent({ delay: 10000, loop: true, callback: () => generateObstacles(this) });
    this.time.addEvent({ delay: 30000, loop: true, callback: () => { spawnMonster(this); generateFood(this); } });
}

function update() {
    const speed = 200;
    player.body.setVelocity(0);
    if (cursors.left.isDown) player.body.setVelocityX(-speed);
    else if (cursors.right.isDown) player.body.setVelocityX(speed);
    if (cursors.up.isDown) player.body.setVelocityY(-speed);
    else if (cursors.down.isDown) player.body.setVelocityY(speed);

    monsterGroup.getChildren().forEach(monster => {
        // 몬스터가 비활성화 상태이면 움직이지 않도록 처리
        if (!monster.active) return;
        const nearest = getNearestFood(monster);
        if (nearest) {
            const angle = Phaser.Math.Angle.Between(monster.x, monster.y, nearest.x, nearest.y);
            const speed = 60;
            monster.body.setVelocity(Math.cos(angle) * speed, Math.sin(angle) * speed);
        }
    });
}

function getNearestFood(monster) {
    let nearest = null;
    let minDist = Number.MAX_VALUE;
    foodGroup.getChildren().forEach(food => {
        if (!food.active) return; // 비활성화된 음식은 제외
        const dist = Phaser.Math.Distance.Between(monster.x, monster.y, food.x, food.y);
        if (dist < minDist) {
            minDist = dist;
            nearest = food;
        }
    });
    return nearest;
}

function generateFood(scene) {
    const foodEmoji = ['🍎','🍌','🍕','🍭','🐨','🐒','🍓','🥐','🍇','🍔'];
    let attempts = 0;
    while (foodGroup.getChildren().length < 10 && attempts < 100) {
        const emoji = Phaser.Utils.Array.GetRandom(foodEmoji);
        const x = Phaser.Math.Between(50, 1230);
        const y = Phaser.Math.Between(50, 670);
        const temp = scene.add.text(x, y, emoji, { fontSize: '32px' });
        scene.physics.add.existing(temp);
        
        // ★★★ 변경점 1: 모든 음식의 점수를 1점으로 통일 ★★★
        temp.setData('value', 1); 
        
        temp.body.setCollideWorldBounds(true);
        temp.body.setImmovable(true);

        let overlap = false;
        // 생성될 음식이 다른 오브젝트와 겹치는지 확인
        scene.physics.overlap(temp, obstacleGroup, () => overlap = true);
        scene.physics.overlap(temp, foodGroup, () => overlap = true);
        scene.physics.overlap(temp, monsterGroup, () => overlap = true);

        if (!overlap) {
            foodGroup.add(temp);
            scene.tweens.add({ targets: temp, y: temp.y - 5, yoyo: true, repeat: -1, duration: 500 });
        } else {
            temp.destroy();
        }
        attempts++;
    }
}

function eatFood(player, food) {
    if (!food.active) return;
    score += food.getData('value');
    sounds.eat.play();

    player.scene.tweens.add({
        targets: food,
        scale: 0,
        alpha: 0,
        duration: 300,
        onComplete: () => food.destroy()
    });

    scoreText.setText(`점수: ${score} / 50`);

    if (score >= 50) {
        scoreText.setText('🎉 게임 종료!');
        player.scene.scene.pause();
    }

    // 음식이 부족할 경우 즉시 재생성
    if (foodGroup.countActive(true) < 10) {
        generateFood(player.scene);
    }
}

// ★★★ 변경점 2: 장애물에 입체감 추가 ★★★
function generateObstacles(scene) {
    // 기존 장애물 모두 제거
    obstacleGroup.clear(true, true);
    
    let attempts = 0;
    while (obstacleGroup.getChildren().length < 6 && attempts < 100) {
        const x = Phaser.Math.Between(100, 1180);
        const y = Phaser.Math.Between(100, 620);
        const width = Phaser.Math.Between(100, 200);
        const height = Phaser.Math.Between(40, 70);
        
        // 입체 효과를 위한 설정
        const shadowOffset = 8; // 그림자 거리
        const mainColor = Phaser.Display.Color.RandomRGB(100, 255); // 너무 어둡지 않은 색상
        const shadowColor = Phaser.Display.Color.ValueToColor(mainColor.color).darken(30).color; // 본체보다 어두운 그림자 색상

        // 컨테이너를 사용해 본체와 그림자를 하나로 묶음
        const obstacleContainer = scene.add.container(x, y);
        const graphics = scene.add.graphics();

        // 1. 그림자 그리기 (아래쪽 레이어)
        graphics.fillStyle(shadowColor);
        graphics.fillRect(-width / 2, -height / 2 + shadowOffset, width, height);

        // 2. 본체 그리기 (위쪽 레이어)
        graphics.fillStyle(mainColor.color);
        graphics.fillRect(-width / 2, -height / 2, width, height);
        
        obstacleContainer.add(graphics);
        obstacleContainer.setSize(width, height); // 물리 엔진이 인식할 크기 설정
        
        scene.physics.add.existing(obstacleContainer); // 컨테이너에 물리 속성 부여
        obstacleContainer.body.setImmovable(true);

        // 다른 장애물과 겹치는지 확인
        let overlap = false;
        scene.physics.overlap(obstacleContainer, obstacleGroup, () => {
            overlap = true;
        });

        if (!overlap) {
            obstacleGroup.add(obstacleContainer);
        } else {
            // 겹치면 컨테이너와 그래픽스 모두 파괴
            obstacleContainer.destroy();
        }
        attempts++;
    }
}


function spawnInitialMonsters(scene) {
    for (let i = 0; i < 4; i++) {
        spawnMonster(scene);
    }
}

function spawnMonster(scene) {
    let x, y, overlap;
    let attempts = 0;
    do {
        x = Phaser.Math.Between(50, 1230);
        y = Phaser.Math.Between(50, 670);
        // 임시 몬스터를 만들어 장애물과 겹치는지 확인
        const tempMonsterBounds = new Phaser.Geom.Rectangle(x-30, y-30, 60, 60);
        overlap = false;
        obstacleGroup.getChildren().forEach(obstacle => {
            if (Phaser.Geom.Intersects.RectangleToRectangle(tempMonsterBounds, obstacle.getBounds())) {
                overlap = true;
            }
        });
        attempts++;
    } while (overlap && attempts < 50);

    // 겹치지 않는 위치에 몬스터 생성
    const monster = scene.add.text(x, y, '👹', { fontSize: '60px' });
    scene.physics.add.existing(monster);
    monster.body.setBounce(0);
    monster.body.setCollideWorldBounds(true);
    monster.body.immovable = true;
    monster.body.pushable = false;
    monster.setData('angry', false);
    monsterGroup.add(monster);

    // 몬스터가 음식을 먹는 로직
    scene.physics.add.overlap(monster, foodGroup, (m, food) => {
        if (food.active) {
            sounds.disappear.play();
            food.destroy();
            // 음식이 부족하면 다시 생성
            if (foodGroup.countActive(true) < 10) {
                generateFood(scene);
            }
        }
    });
}

function hitMonster(player, monster) {
    if (!monster.getData('angry')) {
        monster.setData('angry', true);
        monster.setTint(0xff0000);
        sounds.hit.play();
        
        // 몬스터의 속도를 잠시 0으로 만들어 튕겨나가는 효과를 명확하게 함
        monster.body.setVelocity(0, 0);

        player.scene.time.delayedCall(300, () => {
            monster.clearTint();
            monster.setData('angry', false); // 일정 시간 후 화난 상태 해제
        });
    }

    const pushBack = 300;
    const dx = player.x - monster.x;
    const dy = player.y - monster.y;
    const angle = Math.atan2(dy, dx);

    player.body.setVelocity(Math.cos(angle) * pushBack, Math.sin(angle) * pushBack);
}