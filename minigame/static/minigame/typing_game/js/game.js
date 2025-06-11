// 파일 경로: /home/schizos/study_site/minigame/static/minigame/js/games/typing_game/game.js
// 파일 설명: '큐트 사이버펑크 타자' 게임의 전체 로직을 담고 있는 Phaser 3 스크립트.
//
// - 구조: 4개의 Scene(장면)으로 구성
//   1. PreloadScene: 게임에 필요한 모든 이미지, 사운드 등의 리소스를 미리 불러옵니다.
//   2. MainMenuScene: 게임 시작 화면을 담당합니다.
//   3. GameScene: 핵심 게임 플레이 로직을 모두 처리합니다. (단어 생성, 입력, 점수 계산 등)
//   4. GameOverScene: 게임이 끝났을 때 점수를 보여주고 재시작 옵션을 제공합니다.
//
// - 주요 기능:
//   - DOM <input> 요소를 활용한 원활한 한글 타자 입력 처리
//   - 물리 엔진을 이용한 단어 하강 및 바닥 충돌 감지
//   - 점수 및 패널티 시스템, 특수 단어(고득점) 기능
//   - 파티클 효과를 이용한 시각적 피드백

import Phaser from 'phaser';

// =================================================================
// 1. PreloadScene: 리소스 로딩 장면
// =================================================================
class PreloadScene extends Phaser.Scene {
    constructor() {
        super('PreloadScene');
    }

    preload() {
        // 웹팩이 static 폴더를 기준으로 경로를 잡으므로, 올바른 상대 경로를 사용합니다.
        const basePath = '/static/minigame/typing_game/assets/';

        // 로딩 중 텍스트 표시
        this.add.text(400, 300, 'Loading Assets...', { fontSize: '20px', fill: '#ffffff' }).setOrigin(0.5);

        // --- 여기에 실제 에셋 파일들을 준비해서 넣어야 합니다 ---
        // ※ 아래는 예시이며, 실제 파일이 없으면 404 오류가 발생합니다.
        // ※ 이미지가 없다면, 우선 이 코드들을 주석 처리하고 배경색으로 테스트할 수 있습니다.

        // 이미지 로드
        this.load.image('background', `${basePath}images/background.png`);
        this.load.image('ground', `${basePath}images/ground.png`); // 바닥에 놓을 투명한 이미지
        this.load.image('particle', `${basePath}images/particle.png`); // 성공 시 터질 파티클

        // 사운드 로드
        this.load.audio('bgm', `${basePath}audio/bgm.mp3`);
        this.load.audio('success_sfx', `${basePath}audio/success.mp3`);
        this.load.audio('miss_sfx', `${base_path}audio/miss.mp3`);
    }

    create() {
        this.scene.start('MainMenuScene');
    }
}

// =================================================================
// 2. MainMenuScene: 메인 메뉴 장면
// =================================================================
class MainMenuScene extends Phaser.Scene {
    constructor() {
        super('MainMenuScene');
    }

    create() {
        // 배경 이미지 또는 색상
        this.add.image(400, 300, 'background').setOrigin(0.5);
        // this.cameras.main.setBackgroundColor('#1A1A2E'); // 이미지가 없을 경우

        // 게임 제목
        this.add.text(400, 200, '큐트 사이버펑크 타자', {
            fontSize: '48px',
            fontFamily: '"CookieRun", sans-serif',
            fill: '#00FFFF'
        }).setOrigin(0.5);

        // 게임 시작 버튼
        const startButton = this.add.text(400, 350, '게임 시작', {
            fontSize: '32px',
            fill: '#28a745',
            backgroundColor: '#ffffff',
            padding: { x: 20, y: 10 }
        }).setOrigin(0.5).setInteractive();

        startButton.on('pointerover', () => startButton.setStyle({ fill: '#ffffff', backgroundColor: '#28a745'}));
        startButton.on('pointerout', () => startButton.setStyle({ fill: '#28a745', backgroundColor: '#ffffff'}));

        // 시작 버튼 클릭 시 GameScene으로 이동
        startButton.on('pointerdown', () => {
            this.sound.play('bgm', { loop: true, volume: 0.5 }); // 배경음악 재생
            this.scene.start('GameScene');
        });
    }
}

// =================================================================
// 3. GameScene: 핵심 게임 플레이 장면
// =================================================================
class GameScene extends Phaser.Scene {
    constructor() {
        super('GameScene');
    }

    init() {
        // 게임 변수 초기화
        this.score = 0;
        this.lives = 5;
        this.words = [
            "컴퓨터", "프로그래밍", "자바스크립트", "파이썬", "인공지능",
            "사이버펑크", "네온사인", "미래도시", "안드로이드",
            {text: "쿠키런킹덤", special: true}, {text: "어셈블리", special: true}
        ];
    }

    create() {
        // --- 배경 및 UI 설정 ---
        this.add.image(400, 300, 'background').setOrigin(0.5);
        this.scoreText = this.add.text(16, 16, `점수: 0`, { fontSize: '24px', fill: '#ffffff' });
        this.livesText = this.add.text(784, 16, `목숨: ${this.lives}`, { fontSize: '24px', fill: '#ff4d4d' }).setOrigin(1, 0);

        // --- 물리 효과 설정 ---
        const ground = this.physics.add.staticImage(400, 600, 'ground').setVisible(false);
        this.wordGroup = this.physics.add.group();
        this.physics.add.collider(this.wordGroup, ground, this.handleWordMiss, null, this);

        // --- 한글 입력 필드 설정 ---
        this.inputElement = this.add.dom(400, 550).createFromHTML('<input type="text" id="typing-input" style="width: 300px; padding: 10px; font-size: 18px;">');
        this.inputElement.setOrigin(0.5);
        const inputField = this.inputElement.node;
        inputField.focus(); // 자동으로 입력 필드에 포커스

        // --- 단어 생성 타이머 ---
        this.wordTimer = this.time.addEvent({
            delay: 2000,
            callback: this.spawnWord,
            callbackScope: this,
            loop: true
        });

        // --- 키보드 이벤트 리스너 ---
        this.input.keyboard.on('keydown-ENTER', this.checkWord, this);
    }

    spawnWord() {
        const wordData = Phaser.Utils.Array.GetRandom(this.words);
        const x = Phaser.Math.Between(100, 700);
        const wordText = (typeof wordData === 'string') ? wordData : wordData.text;

        const style = { fontSize: '28px', fill: '#ffffff' };
        if (wordData.special) {
            style.fill = '#FFD700'; // 특수 단어는 금색으로
            style.fontStyle = 'bold';
        }

        const wordObject = this.add.text(x, 50, wordText, style).setOrigin(0.5);
        this.wordGroup.add(wordObject);
        this.physics.world.enable(wordObject);
        wordObject.body.setVelocityY(100);
    }

    checkWord() {
        const typedWord = this.inputElement.node.value.trim();
        if (!typedWord) return;

        let found = false;
        this.wordGroup.getChildren().forEach(wordObject => {
            if (!found && wordObject.text === typedWord) {
                // 점수 계산 (특수 단어는 2배)
                const isSpecial = wordObject.style.fill === '#FFD700';
                const scoreToAdd = typedWord.length * 10 * (isSpecial ? 2 : 1);
                this.score += scoreToAdd;
                this.scoreText.setText(`점수: ${this.score}`);
                
                // 시각/청각 효과
                this.sound.play('success_sfx');
                // this.createParticles(wordObject.x, wordObject.y); // 파티클 효과

                wordObject.destroy();
                found = true;
            }
        });

        this.inputElement.node.value = ''; // 입력 필드 초기화
    }
    
    handleWordMiss(ground, wordObject) {
        this.lives--;
        this.livesText.setText(`목숨: ${this.lives}`);
        this.sound.play('miss_sfx');
        wordObject.destroy();

        if (this.lives <= 0) {
            this.sound.stopByKey('bgm');
            this.scene.start('GameOverScene', { finalScore: this.score });
        }
    }
}

// =================================================================
// 4. GameOverScene: 게임 오버 장면
// =================================================================
class GameOverScene extends Phaser.Scene {
    constructor() {
        super('GameOverScene');
    }

    init(data) {
        this.finalScore = data.finalScore;
    }

    create() {
        this.cameras.main.setBackgroundColor('#1A1A2E');
        this.add.text(400, 200, '게임 오버', { fontSize: '64px', fill: '#ff4d4d' }).setOrigin(0.5);
        this.add.text(400, 300, `최종 점수: ${this.finalScore}`, { fontSize: '32px', fill: '#ffffff' }).setOrigin(0.5);

        const restartButton = this.add.text(400, 400, '다시하기', {
            fontSize: '32px', fill: '#28a745', backgroundColor: '#ffffff', padding: { x: 20, y: 10 }
        }).setOrigin(0.5).setInteractive();

        restartButton.on('pointerover', () => restartButton.setStyle({ fill: '#ffffff', backgroundColor: '#28a745'}));
        restartButton.on('pointerout', () => restartButton.setStyle({ fill: '#28a745', backgroundColor: '#ffffff'}));
        restartButton.on('pointerdown', () => this.scene.start('MainMenuScene'));
    }
}

// =================================================================
// Phaser 게임 전체 설정
// =================================================================
const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    parent: 'phaser-game-container',
    dom: {
        createContainer: true
    },
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 }, // 단어 자체에 속도를 부여하므로 전역 중력은 0
            debug: false
        }
    },
    scene: [PreloadScene, MainMenuScene, GameScene, GameOverScene]
};

// 게임 인스턴스 생성
const game = new Phaser.Game(config);