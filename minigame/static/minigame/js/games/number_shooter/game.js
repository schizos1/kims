/**
 * @fileoverview Number Shooter "원숭이 바나나" (PixiJS 8.x, Howler.js 2.2.4)
 * @desc 종료버튼 상단 우측, 클릭 이펙트/넉넉한 hitArea/중복방지/팝업, 난이도 버튼도 일렬 정렬
 */

document.addEventListener('DOMContentLoaded', async () => {
    const canvas = document.getElementById('number-shooter-canvas');
    if (!canvas) {
        console.error('캔버스 엘리먼트를 찾을 수 없어요!');
        return;
    }

    // PixiJS 8.x 앱 생성
    const app = new PIXI.Application();
    await app.init({
        view: canvas,
        width: 800,
        height: 600,
        backgroundColor: 0x14231c,
        antialias: true,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
    });
    window.__PIXI_DEVTOOLS__ = { app };

    // 사운드
    const sounds = {
        shoot: new Howl({ src: ['/static/minigame/number_shooter/sound/shoot.mp3'] }),
        correct: new Howl({ src: ['/static/minigame/number_shooter/sound/collect.mp3'] }),
        wrong: new Howl({ src: ['/static/minigame/number_shooter/sound/wrong.mp3'] }),
        bgm: new Howl({ src: ['/static/minigame/number_shooter/sound/bgm.mp3'], loop: true, volume: 0.32 }),
        start: new Howl({ src: ['/static/minigame/number_shooter/sound/start.mp3'] }),
    };
    const startBgmOnce = () => {
        if (!sounds.bgm.playing()) sounds.bgm.play();
        window.removeEventListener('click', startBgmOnce);
        window.removeEventListener('keydown', startBgmOnce);
    };
    window.addEventListener('click', startBgmOnce);
    window.addEventListener('keydown', startBgmOnce);

    // 컬러/이모지 팔레트
    const BLOCK_COLORS = [0xfffd62, 0x93c2fd, 0xf6b5e5, 0xa6f7c5, 0xffbfa5, 0xeeeeee, 0xbaf6ff, 0xffe382];
    const GLOW_COLORS  = [0x66ffff, 0x93c2fd, 0xf6b5e5, 0xa6f7c5, 0xffbfa5, 0xbbfffd, 0xa0e0ff, 0xffe382];
    const TEXT_COLORS  = ["#233", "#274c8b", "#484888", "#9c3a3a", "#256d82", "#444", "#228b8b", "#927142"];
    const CUTE_EMOJIS  = ["🍭", "🦊", "🌈", "🦄", "🍬", "🐣", "🧸", "💎", "🍀", "🍉", "🍩", "🎈", "🥕", "🍦", "🐧", "🦕", "🥑", "🐙", "🌻", "🍓", "🧁", "🦋"];

    // 별 파티클(배경)
    for (let i = 0; i < 40; i++) {
        const star = new PIXI.Text({
            text: "⭐",
            style: {
                fontFamily: 'Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif',
                fontSize: Math.random() * 18 + 10,
                fill: "#fff",
            }
        });
        star.x = Math.random() * app.screen.width;
        star.y = Math.random() * app.screen.height;
        star.alpha = 0.4 + Math.random() * 0.5;
        app.stage.addChild(star);
    }

    // ==== 게임종료 버튼(상단 우측, 클릭이펙트/넉넉한 hitArea) ====
    const endBtn = new PIXI.Container();
    endBtn.name = "endBtn";
    const btnBg = new PIXI.Graphics().roundRect(-58, -22, 116, 44, 19).fill({ color: 0xff44b3 });
    btnBg.filters = [
        new PIXI.filters.GlowFilter({ color: 0xffbe2f, distance: 12, outerStrength: 1.6 }),
        new PIXI.filters.DropShadowFilter({ distance: 6, blur: 2, color: 0x8e4300, alpha: 0.22 })
    ];
    const btnText = new PIXI.Text({
        text: "게임종료",
        style: { fontFamily: 'Luckiest Guy', fontSize: 25, fill: '#fff' }
    });
    btnText.anchor.set(0.5);
    endBtn.addChild(btnBg, btnText);
    // [!!] 위치: 우측 상단 모서리(pivot) 맞추기
    endBtn.pivot.set(endBtn.width, 0);
    endBtn.position.set(app.screen.width - 16, 28); // 오른쪽에서 16px, 위에서 28px
    endBtn.zIndex = 99;
    app.stage.sortableChildren = true;
    // 클릭 hitArea 넉넉하게
    endBtn.hitArea = new PIXI.RoundedRectangle(-endBtn.width, 0, endBtn.width + 40, endBtn.height + 10, 20);
    endBtn.eventMode = 'static';
    endBtn.cursor = 'pointer';

    // === 클릭 이펙트 ===
    endBtn.on('pointerdown', () => {
        btnBg.tint = 0xff79ae; // 진하게
        endBtn.scale.set(0.94);
    });
    endBtn.on('pointerup', () => {
        btnBg.tint = 0xffffff;
        endBtn.scale.set(1.0);
    });
    endBtn.on('pointerupoutside', () => {
        btnBg.tint = 0xffffff;
        endBtn.scale.set(1.0);
    });

    // ==== 문제 UI (Glow 필터) ====
    const problemContainer = new PIXI.Container();
    const neon = new PIXI.filters.GlowFilter({ color: 0xa5ffc1, distance: 18, outerStrength: 2 });
    const problemBg = new PIXI.Graphics()
        .roundRect(-170, -45, 340, 90, 30)
        .fill({ color: 0x23652d, alpha: 0.96 });
    problemBg.filters = [neon];
    const problemText = new PIXI.Text({
        text: '',
        style: {
            fontFamily: 'Luckiest Guy',
            fontSize: 44,
            fill: '#fff',
            stroke: { color: "#38f79b", width: 6 }
        }
    });
    problemText.anchor.set(0.5);
    problemContainer.addChild(problemBg, problemText);
    problemContainer.position.set(app.screen.width / 2, 150);
    app.stage.addChild(problemContainer);

    // ==== 점수 UI ====
    let score = 0;
    const scoreBox = new PIXI.Container();
    const scoreBg = new PIXI.Graphics()
        .roundRect(0, 0, 168, 40, 16)
        .fill({ color: 0x18351f, alpha: 0.89 });
    scoreBg.filters = [new PIXI.filters.GlowFilter({ color: 0xfffd62, distance: 12, outerStrength: 1.3 })];
    const scoreText = new PIXI.Text({
        text: `SCORE: ${score}`,
        style: {
            fontFamily: 'Orbitron',
            fontSize: 26,
            fill: "#fffd62",
            fontWeight: 'bold',
        }
    });
    scoreText.anchor.set(0.5);
    scoreText.position.set(84, 21);
    scoreBox.addChild(scoreBg, scoreText);
    scoreBox.position.set(16, 16);
    app.stage.addChild(scoreBox);
    const scoreDom = document.getElementById('score');
    if (scoreDom) scoreDom.textContent = `Score: ${score}`;

    // ==== 난이도 버튼 ====
    let digits = 1;
    const digitButtons = [];
    ["1자리", "2자리", "3자리"].forEach((label, idx) => {
        const btn = new PIXI.Container();
        const bg = new PIXI.Graphics()
            .roundRect(-38, -20, 76, 40, 16)
            .fill({ color: idx + 1 === digits ? 0xf6bb41 : 0x265c2f });
        const txt = new PIXI.Text({ text: label, style: { fontFamily: 'Luckiest Guy', fontSize: 22, fill: "#fff" } });
        txt.anchor.set(0.5);
        btn.addChild(bg, txt);
        btn.bg = bg;
        // 더 왼쪽에 정렬, 종료버튼과 겹치지 않음
        btn.position.set(app.screen.width - 300 - (2 - idx) * 84, 28);
        btn.eventMode = 'static';
        btn.cursor = 'pointer';
        btn.on('pointertap', () => {
            digits = idx + 1;
            digitButtons.forEach((b, j) => {
                b.bg.clear().roundRect(-38, -20, 76, 40, 16)
                    .fill({ color: j === idx ? 0xf6bb41 : 0x265c2f });
            });
            resetGame();
        });
        digitButtons.push(btn);
        app.stage.addChild(btn);
    });

    app.stage.addChild(endBtn); // 항상 가장 마지막에

    // ==== 게임 변수 ====
    let problem = {};
    let numbers = [];
    let particles = [];
    let player;
    let bananaSprite = null;
    let isReadyToShoot = true;
    let numberSpawnTimer = 0;

    // 문제 생성
    function generateProblem() {
        const opList = ['add', 'subtract', 'multiply'];
        const operation = opList[Math.floor(Math.random() * opList.length)];
        let a, b, result, text;
        if (operation === 'multiply') {
            a = Math.floor(Math.random() * 9) + 1;
            b = Math.floor(Math.random() * 9) + 1;
            result = a * b;
            text = `${a} × ${b} = ?`;
        } else {
            const max = Math.pow(10, digits) - 1;
            a = Math.floor(Math.random() * max) + 1;
            b = Math.floor(Math.random() * max) + 1;
            if (operation === 'add') {
                result = a + b;
                text = `${a} + ${b} = ?`;
            } else {
                if (a < b) [a, b] = [b, a];
                result = a - b;
                text = `${a} - ${b} = ?`;
            }
        }
        problem = { result, text, operation };
        problemText.text = text;
        if (!numbers.some(n => n.correct)) spawnNumber(true);
    }

    // 오답 숫자 생성
    function randomFakeNum(answer, digits, operation) {
        let max = operation === 'multiply' ? 81 : Math.pow(10, digits) * 2 - 1;
        let fake;
        do { fake = Math.floor(Math.random() * max); } while (fake === answer);
        return fake;
    }

    // 숫자 블록 생성
    function spawnNumber(forceCorrect = false) {
        if (problem.result === undefined) return;
        const colorIdx = Math.floor(Math.random() * BLOCK_COLORS.length);
        const isCorrect = forceCorrect || (Math.random() < 0.35 && !numbers.some(n => n.correct));
        let numValue = isCorrect ? problem.result : randomFakeNum(problem.result, digits, problem.operation);
        const chosenEmoji = CUTE_EMOJIS[Math.floor(Math.random() * CUTE_EMOJIS.length)];
        const container = new PIXI.Container();
        const rect = new PIXI.Graphics()
            .roundRect(-65, -40, 110, 70, 22)
            .fill({ color: BLOCK_COLORS[colorIdx] });
        rect.filters = [
            new PIXI.filters.DropShadowFilter({ distance: 5, blur: 2, alpha: 0.4, color: 0x000000 }),
            new PIXI.filters.GlowFilter({ color: GLOW_COLORS[colorIdx], distance: 13, outerStrength: 2 })
        ];
        const text = new PIXI.Text({
            text: `${numValue} ${chosenEmoji}`,
            style: {
                fontFamily: 'Orbitron, Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif',
                fontSize: 34,
                fill: TEXT_COLORS[colorIdx],
                fontWeight: 'bold'
            }
        });
        text.anchor.set(0.5);
        container.addChild(rect, text);
        container.position.set(Math.random() * (app.screen.width - 100) + 50, -44);
        container.vy = 0.95 + Math.random() * 0.35;
        container.correct = isCorrect;
        container.shakePower = 0;
        app.stage.addChild(container);
        numbers.push(container);
    }

    function clearNumbers() {
        numbers.forEach(num => num.destroy());
        numbers.length = 0;
    }

    // 플레이어(원숭이 이모지)
    player = new PIXI.Text({
        text: "🦧",
        style: {
            fontFamily: 'Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif',
            fontSize: 66,
        }
    });
    player.anchor.set(0.5);
    player.position.set(app.screen.width / 2, 550);
    app.stage.addChild(player);

    // 조작 (키보드+마우스)
    const keys = { left: false, right: false };
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') keys.left = true;
        else if (e.key === 'ArrowRight') keys.right = true;
        else if (e.key === ' ' && isReadyToShoot) throwBanana();
    });
    document.addEventListener('keyup', (e) => {
        if (e.key === 'ArrowLeft') keys.left = false;
        else if (e.key === 'ArrowRight') keys.right = false;
    });

    app.stage.eventMode = 'static';
    app.stage.hitArea = app.screen;
    app.stage.on('pointermove', (e) => {
        player.x = e.global.x;
    });
    app.stage.on('pointerdown', () => {
        if (isReadyToShoot) throwBanana();
    });

    // 바나나 던지기
    function throwBanana() {
        if (bananaSprite) return;
        isReadyToShoot = false;
        sounds.shoot.play();
        bananaSprite = new PIXI.Text({
            text: "🍌",
            style: {
                fontFamily: 'Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif',
                fontSize: 48,
            }
        });
        bananaSprite.anchor.set(0.5);
        bananaSprite.position.set(player.x, player.y - 18);
        bananaSprite.rotation = -Math.PI / 2 + 0.15 * (Math.random() - 0.5);
        app.stage.addChild(bananaSprite);
        setTimeout(() => { isReadyToShoot = true; }, 400);
    }
    
    // 정답/오답 처리
    function handleHit(num) {
        if (num.correct) {
            score += 10;
            sounds.correct.play();
            explodeParticles(num.x, num.y, 0xf6d86b);
            app.stage.removeChild(num);
            numbers.splice(numbers.indexOf(num), 1);
            num.destroy();
            generateProblem();
        } else {
            score = Math.max(0, score - 5);
            sounds.wrong.play();
            num.shakePower = 15;
        }
        scoreText.text = `SCORE: ${score}`;
        if (scoreDom) scoreDom.textContent = `Score: ${score}`;
    }

    // 파티클 효과
    function explodeParticles(x, y, color = 0xffe382) {
        for (let i = 0; i < 16; i++) {
            const emojiFire = Math.random() < 0.5 ? "🍌" : "✨";
            const p = new PIXI.Text({
                text: emojiFire,
                style: { fontSize: 22 + Math.random() * 10 }
            });
            p.tint = color;
            p.anchor.set(0.5);
            p.position.set(x, y);
            const particleObj = {
                sprite: p,
                vx: (Math.random() - 0.5) * 8.8,
                vy: (Math.random() - 0.5) * 8.8,
                life: 1.0,
            };
            particles.push(particleObj);
            app.stage.addChild(p);
        }
    }

    // PixiJS 팝업 메시지
    function showGameOverPopup(msg) {
        if (app.stage.getChildByName("gameover_popup")) {
            app.stage.removeChild(app.stage.getChildByName("gameover_popup"));
        }
        const popup = new PIXI.Container();
        popup.name = "gameover_popup";
        const bg = new PIXI.Graphics()
            .roundRect(-180, -60, 360, 120, 26)
            .fill({ color: 0x25332c, alpha: 0.96 });
        bg.filters = [new PIXI.filters.GlowFilter({ color: 0xfffd62, distance: 17, outerStrength: 2.2 })];
        const text = new PIXI.Text({
            text: msg,
            style: {
                fontFamily: 'Luckiest Guy',
                fontSize: 27,
                fill: '#fff',
                wordWrap: true,
                wordWrapWidth: 330,
                align: 'center'
            }
        });
        text.anchor.set(0.5);
        popup.addChild(bg, text);
        popup.position.set(app.screen.width / 2, app.screen.height / 2 - 10);
        popup.eventMode = 'static'; // 클릭 막기
        app.stage.addChild(popup);
        setTimeout(() => {
            if (app.stage.getChildByName("gameover_popup")) app.stage.removeChild(popup);
        }, 2500);
    }

    // 서버 전송 및 결과 안내
    async function reportScoreToServer(score) {
        try {
            const response = await fetch('/minigame/api/number_shooter/update_score/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ score }),
            });
            const data = await response.json();
            let msg = "게임이 종료되었습니다!";
            if (data) {
                if (data.point_awarded && data.point_awarded > 0) {
                    msg += `\n+${data.point_awarded} 포인트!`;
                }
                if (data.trophies_awarded && data.trophies_awarded.length > 0) {
                    msg += `\n트로피 획득: ${data.trophies_awarded.join(", ")}`;
                }
            }
            showGameOverPopup(msg);
        } catch (e) {
            showGameOverPopup("점수 저장 실패! 네트워크 오류입니다.");
        }
    }

    // 게임종료 버튼 이벤트 (중복방지+클릭 이펙트)
    endBtn.on('pointertap', async () => {
        if (endBtn.eventMode !== 'static') return;
        endBtn.eventMode = null;
        btnBg.tint = 0xffffff;
        endBtn.scale.set(1.0);

        await reportScoreToServer(score);
        setTimeout(() => {
            endBtn.eventMode = 'static';
        }, 2600);
    });

    // 게임 리셋
    function resetGame() {
        score = 0;
        scoreText.text = `SCORE: ${score}`;
        if (scoreDom) scoreDom.textContent = `Score: ${score}`;
        clearNumbers();
        generateProblem();
        endBtn.eventMode = 'static';
        if (app.stage.getChildByName("gameover_popup")) app.stage.removeChild(app.stage.getChildByName("gameover_popup"));
    }

    // 통합 게임 루프
    app.ticker.add((ticker) => {
        const delta = ticker.deltaTime;
        if (keys.left) player.x -= 7 * delta;
        if (keys.right) player.x += 7 * delta;
        player.x = Math.max(38, Math.min(app.screen.width - 38, player.x));
        if (bananaSprite) {
            bananaSprite.y -= 13 * delta;
            bananaSprite.x += Math.sin(Date.now() / 100) * 1.5;
            bananaSprite.scale.set(1 + Math.sin(Date.now() / 120) * 0.05, 1 + Math.cos(Date.now() / 90) * 0.03);
            if (bananaSprite.y < -20) {
                bananaSprite.destroy();
                bananaSprite = null;
            } else {
                for (let i = numbers.length - 1; i >= 0; i--) {
                    const num = numbers[i];
                    const dx = bananaSprite.x - num.x;
                    const dy = bananaSprite.y - num.y;
                    if (Math.sqrt(dx*dx + dy*dy) < 45) {
                        handleHit(num);
                        if (bananaSprite) {
                            bananaSprite.destroy();
                            bananaSprite = null;
                        }
                        break;
                    }
                }
            }
        }
        for (let i = numbers.length - 1; i >= 0; i--) {
            const num = numbers[i];
            num.y += num.vy * delta;
            if (num.shakePower > 0.3) {
                num.x += Math.random() * num.shakePower * (Math.random() > 0.5 ? 1 : -1);
                num.shakePower *= 0.81;
            }
            if (num.y > app.screen.height + 50) {
                app.stage.removeChild(num);
                numbers.splice(i, 1);
                num.destroy();
            }
        }
        for (let i = particles.length - 1; i >= 0; i--) {
            const p = particles[i];
            p.sprite.x += p.vx * delta;
            p.sprite.y += p.vy * delta;
            p.life -= 0.032 * delta;
            if (p.life <= 0) {
                p.sprite.destroy();
                particles.splice(i, 1);
            } else {
                p.sprite.alpha = p.life;
            }
        }
        numberSpawnTimer += ticker.deltaMS;
        if (numberSpawnTimer >= 1500) {
            spawnNumber();
            numberSpawnTimer = 0;
        }
    });

    // 게임 시작
    sounds.start.play();
    generateProblem();
});
