# 파일 경로: /home/schizos/study_site/minigame/views.py
# ... (상단 주석 생략) ...
# - 수정 사항 (2025-06-08):
#   - minigame_index의 게임 목록에 '큐트 사이버펑크 타자' 게임 정보 반영.
#   - 템플릿에서 표시할 수 있도록 각 게임 딕셔너리에 'emoji' 키와 값을 추가.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# ... lobby 함수 생략 ...

@login_required
def minigame_index(request):
    """
    미니게임 인덱스 페이지
    - 각 미니게임 리스트를 전달
    """
    # 각 게임에 'emoji' 키 추가
    games = [
        {"name": "숫자 헌터", "desc": "하늘에서 쏟아지는 숫자들을 맞춰라", "key": "number_shooter", "emoji": "🔢"},
        {"name": "큐트 사이버펑크 타자", "desc": "네온 불빛 아래, 쏟아지는 단어들을 쳐내세요!", "key": "typing_game", "emoji": "⌨️"},
        {"name": "기억력 게임", "desc": "카드를 순서대로 기억해서 맞히기", "key": "memory_game", "emoji": "🧠"},
        {"name": "먹이 먹기", "desc": "친구와 함께 실시간으로 먹이 먹기!", "key": "eat_food", "emoji": "🐍"},
        {"name": "피아노", "desc": "캔버스와 웹오디오로 피아노를 연주해보자!", "key": "piano", "emoji": "🎹"},
        {"name": "낚시게임", "desc": "물고기를 잡고 도감을 모으는 재미! 포인트로 낚싯대 업그레이드도 가능!", "key": "fishing", "emoji": "🎣"},
        {"name": "이모지 배틀", "desc": "상대를 이모지로 맞혀 승리하자!", "key": "emoji_battle", "emoji": "✨"},
        {"name": "모노폴리", "desc": "부동산을 거래하며 부를 쌓아라!", "key": "monopoly", "emoji": "🏦"},
    ]
    return render(request, "minigame/minigame_index.html", {"games": games})
@login_required
def play_game(request, game_key):
    """
    각 게임별 실행 진입 뷰
    - game_key에 따라 맞는 템플릿을 렌더링
    - 먹이 먹기, 모노폴리는 모드/방ID 등 컨텍스트 추가
    """
    context = {
        "game_key": game_key,
        "user_username": request.user.username,
    }

    if game_key == "eat_food":
        game_mode = request.GET.get('mode', 'single')
        room_id = request.GET.get('room_id', None)
        context['game_mode'] = game_mode
        if game_mode == 'multi' and not room_id:
            room_id = 'default_room'
        context['room_id'] = room_id
        template_name = "minigame/eat_food_entry.html"
    elif game_key == "piano":
        template_name = "minigame/piano.html"
    elif game_key == "fishing":
        game_mode = request.GET.get('mode', 'single')
        context['game_mode'] = game_mode
        template_name = "minigame/fishing.html"
    elif game_key == "monopoly":
        game_mode = request.GET.get('mode', 'multi')  # 기본 멀티플레이
        room_id = request.GET.get('room_id', 'monopoly_room')
        context['game_mode'] = game_mode
        context['room_id'] = room_id
        template_name = "minigame/monopoly.html"
    else:
        # 'typing_game'을 포함한 다른 모든 게임들은 이 generic한 로직을 따릅니다.
        # game_key가 'typing_game'이면 'minigame/typing_game.html' 템플릿을 자동으로 렌더링합니다.
        template_name = f"minigame/{game_key}.html"

    return render(request, template_name, context)