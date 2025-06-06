// == Number Shooter "원숭이 바나나" 에디션 (PIXI 6.x, Kids Final) ==
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('number-shooter-canvas');
    if (!canvas) {
        console.error('Canvas element not found!');
        return;
    }
    const app = new PIXI.Application({ view: canvas, width: 800, height: 600, backgroundColor: 0x14231c });
    window.__PIXI_DEVTOOLS__ = { app };

    // ==== 사운드: 모두 로컬 파일로 변경 ====
    const sounds = {
        shoot: new Howl({ src: ['/static/minigame/number_shooter/sound/shoot.mp3'] }),
        correct: new Howl({ src: ['/static/minigame/number_shooter/sound/collect.mp3'] }),
        wrong: new Howl({ src: ['/static/minigame/number_shooter/sound/wrong.mp3'] }),
        bgm: new Howl({ src: ['/static/minigame/number_shooter/sound/bgm.mp3'], loop: true, volume: 0.32 }),
        start: new Howl({ src: ['/static/minigame/number_shooter/sound/start.mp3'] })
    };
    sounds.bgm.play();

    // ==== 컬러 팔레트 ====
    const BLOCK_COLORS = [
        0xfffd62, 0x93c2fd, 0xf6b5e5, 0xa6f7c5, 0xffbfa5, 0xeeeeee, 0xbaf6ff, 0xffe382
    ];
    const GLOW_COLORS = [
        0x66ffff, 0x93c2fd, 0xf6b5e5, 0xa6f7c5, 0xffbfa5, 0xbbfffd, 0xa0e0ff, 0xffe382
    ];
    const TEXT_COLORS = [
        "#233", "#274c8b", "#484888", "#9c3a3a", "#256d82", "#444", "#228b8b", "#927142"
    ];

    // ==== 귀여운 랜덤 이모지 (숫자 옆용) ====
    const CUTE_EMOJIS = [
        "🍭", "🦊", "🌈", "🦄", "🍬", "🌟", "🐣", "🧸", "💎", "🍀", "🍉", "🍩", "🎈", "🥕", "🍦", "🐧", "🦕", "🥑", "🐙", "🌻", "🍓", "🧁", "🦋"
    ];

    // ==== 별 파티클(배경) ====
    for (let i = 0; i < 40; i++) {
        const star = new PIXI.Text("⭐", { fontSize: Math.random() * 18 + 10, alpha: 0.33 + Math.random() * 0.5 });
        star.x = Math.random() * 800;
        star.y = Math.random() * 600;
        star.alpha = 0.4 + Math.random() * 0.5;
        app.stage.addChild(star);
    }

    // ==== 문제 영역 (귀여운 스타일) ====
    const problemContainer = new PIXI.Container();
    const neon = new PIXI.filters.GlowFilter({ color: 0xa5ffc1, distance: 18, outerStrength: 2 });
    const problemBg = new PIXI.Graphics().beginFill(0x23652d, 0.96).drawRoundedRect(-170, -45, 340, 90, 30).endFill();
    problemBg.filters = [neon];
    const problemText = new PIXI.Text('', {
        fontFamily: 'Luckiest Guy',
        fontSize: 44,
        fill: ['#fff', '#fffd62'],
        stroke: "#38f79b",
        strokeThickness: 6
    });
    problemText.anchor.set(0.5);
    problemContainer.addChild(problemBg, problemText);
    problemContainer.x = 400; problemContainer.y = 90;
    app.stage.addChild(problemContainer);
    app.ticker.add(() => {
        problemContainer.y = 90 + Math.sin(Date.now()/340)*4;
    });

    // ==== 점수 UI (네온박스) ====
    let score = 0;
    const scoreBox = new PIXI.Container();
    const scoreBg = new PIXI.Graphics().beginFill(0x18351f, 0.89).drawRoundedRect(0, 0, 168, 40, 16).endFill();
    scoreBg.filters = [new PIXI.filters.GlowFilter({ color: 0xfffd62, distance: 12, outerStrength: 1.3 })];
    const scoreText = new PIXI.Text(`SCORE: ${score}`, {
        fontFamily: 'Orbitron',
        fontSize: 26,
        fill: "#fffd62",
        fontWeight: 'bold',
        align: 'center'
    });
    scoreText.x = 84; scoreText.y = 21; scoreText.anchor.set(0.5);
    scoreBox.addChild(scoreBg, scoreText);
    scoreBox.x = 16; scoreBox.y = 16;
    app.stage.addChild(scoreBox);
    document.getElementById('score').textContent = `Score: ${score}`;

    // ==== 난이도 버튼 ====
    let digits = 1;
    const digitButtons = [];
    ["1자리", "2자리", "3자리"].forEach((label, idx) => {
        const btn = new PIXI.Container();
        const bg = new PIXI.Graphics().beginFill(idx+1 === digits ? 0xf6bb41 : 0x265c2f).drawRoundedRect(-38, -20, 76, 40, 16).endFill();
        const txt = new PIXI.Text(label, { fontFamily: 'Luckiest Guy', fontSize: 22, fill: "#fff" });
        txt.anchor.set(0.5);
        btn.addChild(bg, txt);
        btn.x = 670 + idx * 84; btn.y = 28;
        btn.interactive = true; btn.buttonMode = true;
        btn.on('pointertap', () => {
            digits = idx + 1;
            digitButtons.forEach((b, j) => b.children[0].tint = j === idx ? 0xf6bb41 : 0x265c2f);
            resetGame();
        });
        digitButtons.push(btn);
        app.stage.addChild(btn);
    });

    // ==== 문제/숫자/게임 상태 ====
    let problem = {}, numbers = [];
    let player, isReadyToShoot = true, bananaSprite = null;

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
                result = a;
                a = a + b;
                text = `${a} - ${b} = ?`;
            }
        }
        problem = { result, text, operation };
        problemText.text = text;
        clearNumbers();
    }

    function randomFakeNum(answer, digits, operation) {
        let max = operation === 'multiply' ? 81 : Math.pow(10, digits) * 2;
        let fake;
        do {
            fake = Math.floor(Math.random() * max);
        } while (fake === answer);
        return fake;
    }

    // ==== 숫자 내려오기 (랜덤컬러, 네온 사각형, 랜덤 이모지) ====
    function spawnNumber() {
        if (!problem.result) return;
        const colorIdx = Math.floor(Math.random() * BLOCK_COLORS.length);
        const blockColor = BLOCK_COLORS[colorIdx];
        const glowColor = GLOW_COLORS[colorIdx];
        const textColor = TEXT_COLORS[colorIdx];

        const isCorrect = Math.random() < 0.35;
        let num = isCorrect ? problem.result : randomFakeNum(problem.result, digits, problem.operation);

        // 랜덤 이모지 붙이기!
        const chosenEmoji = CUTE_EMOJIS[Math.floor(Math.random() * CUTE_EMOJIS.length)];

        const container = new PIXI.Container();
        const rect = new PIXI.Graphics()
            .beginFill(blockColor)
            .drawRoundedRect(-38, -38, 76, 76, 22)
            .endFill();
        rect.filters = [
            new PIXI.filters.GlowFilter({
                color: glowColor,
                distance: 13,
                outerStrength: 2
            })
        ];
        const text = new PIXI.Text(`${num} ${chosenEmoji}`, {
            fontFamily: 'Orbitron, Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif',
            fontSize: 34,
            fill: textColor,
            fontWeight: 'bold'
        });
        text.anchor.set(0.5);
        container.addChild(rect, text);
        container.x = Math.random() * 700 + 50;
        container.y = -44;
        container.vy = 0.95 + Math.random() * 0.35;
        container.correct = isCorrect;
        container.shakePower = 0;
        app.stage.addChild(container);
        numbers.push(container);
    }

    function clearNumbers() {
        numbers.forEach(num => app.stage.removeChild(num));
        numbers.length = 0;
    }

    // ==== 숫자 움직임 ====
    app.ticker.add(() => {
        for (let i = numbers.length - 1; i >= 0; i--) {
            const num = numbers[i];
            num.y += num.vy;
            if (num.shakePower > 0.3) {
                num.x += Math.random() * num.shakePower * (Math.random() > 0.5 ? 1 : -1);
                num.shakePower *= 0.81;
            }
            if (num.y > 650) {
                app.stage.removeChild(num);
                numbers.splice(i, 1);
            }
        }
    });

    // ==== 플레이어 (원숭이 이모지) ====
    const playerEmoji = "🦧"; // 원숭이(orangutan)
    player = new PIXI.Text(playerEmoji, {
        fontFamily: 'Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif',
        fontSize: 66,
        align: 'center'
    });
    player.anchor.set(0.5);
    player.x = 400; player.y = 550;
    app.stage.addChild(player);

    // ==== 조작 ====
    const keys = { left: false, right: false, space: false };
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') keys.left = true;
        if (e.key === 'ArrowRight') keys.right = true;
        if (e.key === ' ' && isReadyToShoot) throwBanana();
    });
    document.addEventListener('keyup', (e) => {
        if (e.key === 'ArrowLeft') keys.left = false;
        if (e.key === 'ArrowRight') keys.right = false;
        if (e.key === ' ') keys.space = false;
    });
    app.view.addEventListener('mousemove', (e) => {
        const rect = app.view.getBoundingClientRect();
        player.x = e.clientX - rect.left;
    });
    app.ticker.add(() => {
        if (keys.left) player.x -= 7;
        if (keys.right) player.x += 7;
        player.x = Math.max(38, Math.min(762, player.x));
    });

    // ==== 바나나 던지기 (실제 슈팅) ====
    function throwBanana() {
        if (bananaSprite) return;
        isReadyToShoot = false;
        sounds.shoot.play();
        // 바나나 이모지 생성
        bananaSprite = new PIXI.Text("🍌", {
            fontFamily: 'Segoe UI Emoji, Apple Color Emoji, Noto Color Emoji, sans-serif',
            fontSize: 48,
            align: 'center'
        });
        bananaSprite.anchor.set(0.5);
        bananaSprite.x = player.x;
        bananaSprite.y = player.y - 18;
        bananaSprite.rotation = -Math.PI / 2 + 0.15 * (Math.random() - 0.5); // 위쪽 대각선 느낌!
        app.stage.addChild(bananaSprite);

        app.ticker.add(bananaMove);
        setTimeout(() => { isReadyToShoot = true; }, 400);
    }

    function bananaMove() {
        if (!bananaSprite) return;
        bananaSprite.y -= 13;
        bananaSprite.x += Math.sin(Date.now() / 100) * 1.5; // 약간 비틀비틀(원숭이스타일)
        bananaSprite.scale.set(1 + Math.sin(Date.now()/120)*0.05, 1 + Math.cos(Date.now()/90)*0.03);
        for (let i = numbers.length - 1; i >= 0; i--) {
            const num = numbers[i];
            if (Math.abs(bananaSprite.x - num.x) < 45 && Math.abs(bananaSprite.y - num.y) < 45) {
                handleHit(num, bananaSprite.x, bananaSprite.y);
                app.stage.removeChild(bananaSprite); bananaSprite = null;
                app.ticker.remove(bananaMove);
                return;
            }
        }
        if (bananaSprite.y < -20) {
            app.stage.removeChild(bananaSprite); bananaSprite = null;
            app.ticker.remove(bananaMove);
        }
    }
    app.view.addEventListener('click', () => {
        if (isReadyToShoot) throwBanana();
    });

    // ==== 정답/오답 처리 ====
    function handleHit(num, x, y) {
        if (num.correct) {
            score += 10;
            scoreText.text = `SCORE: ${score}`;
            document.getElementById('score').textContent = `Score: ${score}`;
            sounds.correct.play();
            explodeParticles(x, y, 0xf6d86b);
            app.stage.removeChild(num);
            numbers.splice(numbers.indexOf(num), 1);
            generateProblem();
        } else {
            score = Math.max(0, score - 5);
            scoreText.text = `SCORE: ${score}`;
            document.getElementById('score').textContent = `Score: ${score}`;
            sounds.wrong.play();
            num.shakePower = 15;
        }
    }

    // ==== 파티클 효과 ====
    function explodeParticles(x, y, color=0xffe382) {
        for (let i = 0; i < 16; i++) {
            const emojiFire = Math.random() < 0.5 ? "🍌" : "✨";
            const p = new PIXI.Text(emojiFire, { fontSize: 22 + Math.random() * 10 });
            p.x = x; p.y = y;
            p.vx = (Math.random() - 0.5) * 8.8;
            p.vy = (Math.random() - 0.5) * 8.8;
            p.alpha = 1;
            app.stage.addChild(p);
            app.ticker.add(function particleAnim() {
                p.x += p.vx; p.y += p.vy; p.alpha -= 0.032;
                if (p.alpha < 0) { app.stage.removeChild(p); this.destroy(); }
            });
        }
    }

    // ==== 게임 리셋 ====
    function resetGame() {
        score = 0; scoreText.text = `SCORE: ${score}`;
        document.getElementById('score').textContent = `Score: ${score}`;
        clearNumbers();
        generateProblem();
    }

    // ==== 1.5초마다 숫자 내려오기 ====
    setInterval(spawnNumber, 1500);

    // ==== 게임 시작 ====
    sounds.start.play();
    generateProblem();
});
