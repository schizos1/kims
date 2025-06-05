# minigame/views.py
"""
미니게임 Views
- 로비
- 미니게임 인덱스
- 게임별 진입(먹이먹기, 피아노 등)
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def lobby(request):
    """미니게임 로비(테스트용, 실제 화면 있음)"""
    return render(request, "minigame/lobby.html")

@login_required
def minigame_index(request):
    """
    미니게임 인덱스 페이지
    - 각 미니게임 리스트를 전달
    """
    games = [
        {"name": "수학 퀴즈", "desc": "시간 내에 정답 맞추기", "key": "math_quiz"},
        {"name": "빠른 타자", "desc": "단어를 빨리 입력해보자!", "key": "typing_game"},
        {"name": "기억력 게임", "desc": "카드를 순서대로 기억해서 맞히기", "key": "memory_game"},
        {"name": "먹이 먹기", "desc": "친구와 함께 실시간으로 먹이 먹기!", "key": "eat_food"},
        {"name": "피아노", "desc": "캔버스와 웹오디오로 피아노를 연주해보자!", "key": "piano"},
        {"name": "낚시게임", "desc": "물고기를 잡고 도감을 모으는 재미! 포인트로 낚싯대 업그레이드도 가능!", "key": "fishing"},
        {"name": "이모지 배틀", "desc": "상대를 이모지로 맞혀 승리하자!", "key": "emoji_battle"},
    ]
    # templates/minigame/minigame_index.html 기준
    return render(request, "minigame/minigame_index.html", {"games": games})

@login_required
def play_game(request, game_key):
    """
    각 게임별 실행 진입 뷰
    - game_key에 따라 맞는 템플릿을 렌더링
    - 먹이 먹기는 모드/방ID 등 컨텍스트 추가
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
        # 피아노 미니게임: 별도 컨텍스트 없이 템플릿만 전달
        template_name = "minigame/piano.html"
    elif game_key == "fishing":
        game_mode = request.GET.get('mode', 'single')
        context['game_mode'] = game_mode
        template_name = "minigame/fishing.html"
    else:
        # 나머지 게임은 템플릿 네이밍 컨벤션 통일
        template_name = f"minigame/{game_key}.html"

    return render(request, template_name, context)
