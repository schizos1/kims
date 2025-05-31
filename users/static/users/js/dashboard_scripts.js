// users/static/users/js/dashboard_scripts.js
document.addEventListener('DOMContentLoaded', function() {
    const fancyButtons = document.querySelectorAll('.fancy-button');

    fancyButtons.forEach(function(button) {
        const hoverSoundId = button.dataset.soundHover;
        const clickSoundId = button.dataset.soundClick;

        // data-sound-hover/click 속성이 없으면 null 대신 빈 문자열로 처리하여 오류 방지
        const hoverAudioElement = hoverSoundId ? document.getElementById('sound-' + hoverSoundId) : null;
        const clickAudioElement = clickSoundId ? document.getElementById('sound-' + clickSoundId) : null;

        if (hoverAudioElement) {
            button.addEventListener('mouseenter', function() {
                hoverAudioElement.currentTime = 0;
                hoverAudioElement.play().catch(function(error) {
                    // console.warn("마우스오버 사운드 재생 실패:", error);
                });
            });
        }

        if (clickAudioElement) {
            button.addEventListener('click', function(event) {
                // A 태그인 경우 (링크)
                if (button.tagName === 'A' && button.href) {
                    // 새 탭에서 열리는 링크가 아니고, JavaScript 링크가 아닌 경우에만 기본 동작 막기
                    if (button.target !== '_blank' && !button.href.startsWith('javascript:')) {
                        event.preventDefault(); 
                        clickAudioElement.currentTime = 0;
                        const soundPromise = clickAudioElement.play();

                        if (soundPromise !== undefined) {
                            soundPromise.then(_ => {
                                // 사운드 재생 성공 후 또는 즉시 (짧은 사운드의 경우) 페이지 이동
                                window.location.href = button.href;
                            }).catch(error => {
                                // console.warn("클릭 사운드 재생 실패 (A태그):", error);
                                window.location.href = button.href; // 사운드 실패해도 이동
                            });
                        } else { // Promise 미지원 또는 기타 경우
                            window.location.href = button.href; // 즉시 이동
                        }
                    } else { // 새 탭 링크 등은 사운드만 재생하고 기본 동작 따름
                         clickAudioElement.currentTime = 0;
                         clickAudioElement.play().catch(function(error) {});
                    }
                } 
                // BUTTON 태그 (폼 제출 버튼 등)
                else if (button.tagName === 'BUTTON' && button.type === 'submit') {
                    // 폼 제출 버튼의 경우, 사운드 재생 후 폼이 바로 제출되어 소리가 끊길 수 있음.
                    // 여기서는 사운드만 재생 시도하고 폼 제출은 기본 동작에 맡김.
                    // 더 나은 UX를 위해서는 event.preventDefault() 후 사운드 재생 완료 콜백에서
                    // button.closest('form').submit()을 호출해야 할 수 있음.
                    clickAudioElement.currentTime = 0;
                    clickAudioElement.play().catch(function(error) {
                        // console.warn("클릭 사운드 재생 실패 (submit버튼):", error);
                    });
                } 
                // 기타 버튼 (type="button")
                else if (button.tagName === 'BUTTON') {
                    clickAudioElement.currentTime = 0;
                    clickAudioElement.play().catch(function(error) {
                        // console.warn("클릭 사운드 재생 실패 (button):", error);
                    });
                }
            });
        }
    });
});