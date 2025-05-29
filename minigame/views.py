"""
minigame/views.py
- 학생 미니게임 메뉴
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def minigame_index(request):
    # 게임 종류는 DB 또는 하드코딩 가능
    games = [
        {"name": "수학 퀴즈", "desc": "시간 내에 정답 맞추기"},
        {"name": "빠른 타자", "desc": "단어를 빨리 입력해보자!"},
        {"name": "기억력 게임", "desc": "카드를 순서대로 기억해서 맞히기"},
    ]
    return render(request, "minigame_index.html", {"games": games})
def play_game(request, game_name):
    return render(request, "play_game.html", {"game_name": game_name})