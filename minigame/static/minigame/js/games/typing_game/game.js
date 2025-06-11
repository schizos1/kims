// 파일 경로: /home/schizos/study_site/minigame/static/minigame/js/games/typing_game/game.js
// 1단계 개발 계획 전체 적용 버전 (1920x1080 반응형, 비주얼 업그레이드)

import Phaser from 'phaser';
import { WORDS } from './words.js';

// 네온 이펙트 (파티클 대체)
function emitWordParticles(scene, x, y) {
    const fx = scene.add.text(x, y, '✨', {
        fontSize: '56px', fill: '#00FFF7', fontStyle: 'bold'
    }).setOrigin(0.5).setShadow(0, 0, '#00FFF7', 15);
    scene.tweens.add({
        targets: fx,
        alpha: { from: 1, to: 0 },
        y: y - 40,
        scale: { from: 1, to: 2.2 },
        duration: 420,
        onComplete: () => fx.destroy()
    });
}

function createStarfield(scene) {
    scene.cameras.main.setBackgroundColor('#1A1A2E');
    for (let i = 0; i < 200; i++) {
        const x = Phaser.Math.Between(0, scene.scale.width);
        const y = Phaser.Math.Between(0, scene.scale.height);
        const size = Phaser.Math.Between(1, 3);
        const star = scene.add.rectangle(x, y, size, size, 0xffffff);
        scene.tweens.add({
            targets: star,
            alpha: { from: 0.2, to: 1 },
            duration: Phaser.Math.Between(1000, 3000),
            yoyo: true,
            repeat: -1
        });
    }
}

class PreloadScene extends Phaser.Scene {
    constructor() { super('PreloadScene'); }
    preload() {
        const basePath = '/static/minigame/typing_game/assets/';
        this.add.text(this.scale.width/2, this.scale.height/2, 'Loading...', { fontSize: '36px', fill: '#fff' }).setOrigin(0.5);
        this.load.image('ground', `${basePath}images/ground.png`);
        this.load.audio('bgm', [`${basePath}audio/bgm.mp3`]);
        this.load.audio('success_sfx', [`${basePath}audio/success.mp3`]);
        this.load.audio('miss_sfx', [`${basePath}audio/miss.mp3`]);
    }
    create() { this.scene.start('MainMenuScene'); }
}

class MainMenuScene extends Phaser.Scene {
    constructor() { super('MainMenuScene'); }
    create() {
        createStarfield(this);
        const centerX = this.scale.width / 2;
        const centerY = this.scale.height / 2;
        this.add.text(centerX, centerY - 140, '큐트 사이버펑크 타자', {
            fontSize: 'clamp(40px,10vw,120px)', fontFamily: '"CookieRun",sans-serif', fill: '#00FFFF'
        }).setOrigin(0.5).setShadow(5, 5, '#FF00FF', 15);

        const startButton = this.add.text(centerX, centerY + 80, '게임 시작', {
            fontSize: 'clamp(30px,4vw,64px)', fill: '#28a745',
            backgroundColor: '#fff', padding: { x: 40, y: 20 }
        }).setOrigin(0.5).setInteractive().setShadow(2,2,'#fff',6);

        startButton.on('pointerover', () => startButton.setStyle({ fill: '#fff', backgroundColor: '#28a745' }));
        startButton.on('pointerout', () => startButton.setStyle({ fill: '#28a745', backgroundColor: '#fff' }));
        startButton.on('pointerdown', () => {
            if (this.sound.context.state === 'suspended') this.sound.context.resume();
            if (!this.sound.get('bgm') || !this.sound.get('bgm').isPlaying) {
                this.sound.play('bgm', { loop: true, volume: 0.6 });
            }
            this.scene.start('GameScene');
        });

        this.input.keyboard.once('keydown', () => {
            if (this.sound.context.state === 'suspended') this.sound.context.resume();
        });
        this.input.once('pointerdown', () => {
            if (this.sound.context.state === 'suspended') this.sound.context.resume();
        });
    }
}

class GameScene extends Phaser.Scene {
    constructor() { super('GameScene'); }
    init() {
        this.score = 0;
        this.lives = 5;
        this.wordList = WORDS;
        this.wordInterval = 2000;
        this.totalWords = 0;
        this.correctWords = 0;
        this.timers = [];
    }
    create() {
        createStarfield(this);
        const w = this.scale.width, h = this.scale.height;
        this.add.text(50, 50, 'SCORE', { fontSize: '40px', fill: '#FF00FF' }).setShadow(2, 2, '#FF00FF', 10);
        this.scoreText = this.add.text(170, 50, '0', { fontSize: '40px', fill: '#fff' }).setShadow(2, 2, '#fff', 10);
        this.accuracyText = this.add.text(w-40, 50, `정확도: 100%`, {
            fontSize: '40px', fill: '#81fffe'
        }).setOrigin(1,0).setShadow(2,2,'#81fffe',10);

        const ground = this.physics.add.staticImage(w/2, h, 'ground').setVisible(false).setSize(w, 10).setOffset(0,-5);
        this.wordGroup = this.physics.add.group();
        this.physics.add.collider(this.wordGroup, ground, this.handleWordMiss, null, this);

        if (this.typingInput) this.typingInput.destroy();
        this.typingInput = this.add.dom(w/2, h-80).createFromHTML(
            '<input type="text" id="typing-input" style="width: clamp(200px,30vw,500px); padding: 15px; font-size: 24px;">'
        );
        setTimeout(()=>{
            const inputField = document.getElementById('typing-input');
            if(inputField){ inputField.setAttribute('autocomplete','off'); inputField.focus();}
        }, 300);

        // 1분마다 속도 증가
        this.levelTimer = this.time.addEvent({
            delay: 60000,
            callback: () => {
                this.wordInterval = Math.max(600, this.wordInterval - 450);
                if (this.wordTimer) {
                    this.wordTimer.remove(false);
                    this.wordTimer = this.time.addEvent({
                        delay: this.wordInterval,
                        callback: this.spawnWord,
                        callbackScope: this,
                        loop: true
                    });
                    this.timers.push(this.wordTimer);
                }
            },
            callbackScope: this,
            loop: true
        });
        this.timers.push(this.levelTimer);

        // 단어 생성 타이머
        this.wordTimer = this.time.addEvent({
            delay: this.wordInterval,
            callback: this.spawnWord,
            callbackScope: this,
            loop: true
        });
        this.timers.push(this.wordTimer);

        this.input.keyboard.on('keydown-ENTER', this.checkWord, this);
        this.events.on('shutdown', () => this.cleanupAll());
        this.events.on('destroy', () => this.cleanupAll());
    }
    cleanupAll() {
        if (this.timers) {
            this.timers.forEach(t => { if (t) t.remove(false); });
            this.timers = [];
        }
        if (this.wordGroup) this.wordGroup.clear(true, true);
        if (this.typingInput) { this.typingInput.destroy(); this.typingInput = null; }
    }
    spawnWord() {
        if (!this.scene.isActive()) return;
        const wordText = Phaser.Utils.Array.GetRandom(this.wordList);
        const x = Phaser.Math.Between(120, this.scale.width-120);
        const style = { fontSize: '36px', fill: '#fff', fontFamily: 'sans-serif' };
        const wordObject = this.add.text(x, 100, wordText, style).setOrigin(0.5).setShadow(3, 3, '#000', 5);
        this.wordGroup.add(wordObject);
        this.physics.world.enable(wordObject);
        wordObject.body.setVelocityY(Phaser.Math.Between(80, 200));
        wordObject.body.setAllowGravity(false);
        this.totalWords++;
        this.updateAccuracy();
    }
    checkWord() {
        const inputField = document.getElementById('typing-input');
        if (!inputField) return;
        const typedWord = inputField.value.trim();
        if (!typedWord) return;
        let found = false;
        this.wordGroup.getChildren().slice().forEach(wordObject => {
            if (wordObject.active && wordObject.text === typedWord) {
                const scoreToAdd = typedWord.length * 10;
                this.score += scoreToAdd;
                this.scoreText.setText(this.score);
                if (this.sound.get('success_sfx')) this.sound.play('success_sfx', {volume: 0.7});
                wordObject.destroy();
                found = true;
                this.correctWords++;
                this.updateAccuracy();
            }
        });
        inputField.value = '';
    }
    updateAccuracy() {
        const acc = this.totalWords === 0 ? 100 : Math.round((this.correctWords / this.totalWords) * 100);
        this.accuracyText.setText(`정확도: ${acc}%`);
    }
    handleWordMiss = (wordObject, ground) => {
        if (!wordObject.active) return;
        this.lives--;
        emitWordParticles(this, wordObject.x, wordObject.y);
        if (this.sound.get('miss_sfx')) this.sound.play('miss_sfx', {volume: 0.8});
        wordObject.destroy();
        if (this.lives <= 0) {
            if (this.sound.get('bgm')) this.sound.stopByKey('bgm');
            this.cleanupAll && this.cleanupAll();
            this.scene.start('GameOverScene', {
                finalScore: this.score,
                totalWords: this.totalWords,
                correctWords: this.correctWords
            });
        }
    }
}

class GameOverScene extends Phaser.Scene {
    constructor() { super('GameOverScene'); }
    init(data) {
        this.finalScore = data.finalScore || 0;
        this.totalWords = data.totalWords || 0;
        this.correctWords = data.correctWords || 0;
    }
    create() {
        createStarfield(this);
        const centerX = this.scale.width / 2, centerY = this.scale.height / 2;
        this.add.text(centerX, centerY-120, '게임 오버', { fontSize: '96px', fill: '#ff4d4d' }).setOrigin(0.5).setShadow(5,5,'#000',10);
        this.add.text(centerX, centerY, `최종 점수: ${this.finalScore}`, { fontSize: '48px', fill: '#fff' }).setOrigin(0.5).setShadow(3,3,'#000',7);
        const acc = this.totalWords === 0 ? 100 : Math.round((this.correctWords / this.totalWords) * 100);
        this.add.text(centerX, centerY + 60, `정확도: ${acc}% (${this.correctWords} / ${this.totalWords})`, {
            fontSize: '38px', fill: '#81fffe'
        }).setOrigin(0.5).setShadow(2,2,'#222',8);

        const restartButton = this.add.text(centerX, centerY+140, '다시하기', {
            fontSize: 'clamp(30px,4vw,64px)', fill: '#28a745', backgroundColor: '#fff', padding: { x: 40, y: 20 }
        }).setOrigin(0.5).setInteractive().setShadow(2,2,'#fff',5);
        restartButton.on('pointerover', () => restartButton.setStyle({ fill: '#fff', backgroundColor: '#28a745'}));
        restartButton.on('pointerout', () => restartButton.setStyle({ fill: '#28a745', backgroundColor: '#fff'}));
        restartButton.on('pointerdown', () => this.scene.start('MainMenuScene'));
    }
}

const config = {
    type: Phaser.AUTO,
    scale: {
        mode: Phaser.Scale.RESIZE,
        parent: 'phaser-game-container',
        autoCenter: Phaser.Scale.CENTER_BOTH,
        width: 1920,
        height: 1080
    },
    dom: { createContainer: true },
    physics: { default: 'arcade', arcade: { debug: false } },
    scene: [PreloadScene, MainMenuScene, GameScene, GameOverScene]
};
const game = new Phaser.Game(config);


