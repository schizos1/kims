"""
테마 더미 데이터 자동 등록 스크립트
- 바다속, 미쿠, 사이버, 파스텔, 공포 스타일
- mascot_image/preview_image는 샘플 이미지 URL로 대체(운영 시 CDN 등으로 교체)
"""

from users.models import Theme

THEMES = [
    {
        "name": "sea",
        "display_name": "바다속 스타일",
        "description": "푸른 바다와 해양 생물들이 가득한 시원한 테마",
        "bg_color": "#e6f7fa",
        "main_color": "#3cc7d4",
        "mascot_image": "https://cdn.pixabay.com/photo/2017/01/31/13/14/sea-2025695_1280.png",  # 예시
        "preview_image": "https://cdn.pixabay.com/photo/2017/01/31/13/14/sea-2025695_1280.png",
    },
    {
        "name": "miku",
        "display_name": "미쿠 스타일",
        "description": "초록 파스텔과 미쿠 캐릭터 감성, 산뜻하고 발랄한 테마",
        "bg_color": "#e1f7f3",
        "main_color": "#23ced2",
        "mascot_image": "https://static.zerochan.net/Hatsune.Miku.full.1982439.jpg",  # 예시
        "preview_image": "https://static.zerochan.net/Hatsune.Miku.full.1982439.jpg",
    },
    {
        "name": "cyber",
        "display_name": "사이버 스타일",
        "description": "형광/블루톤의 하이테크 미래 배경, 반짝이는 이펙트",
        "bg_color": "#121730",
        "main_color": "#00ffe4",
        "mascot_image": "https://cdn.pixabay.com/photo/2020/01/31/20/56/robot-4805353_1280.jpg",  # 예시
        "preview_image": "https://cdn.pixabay.com/photo/2020/01/31/20/56/robot-4805353_1280.jpg",
    },
    {
        "name": "pastel",
        "display_name": "파스텔 스타일",
        "description": "따뜻하고 부드러운 파스텔톤 컬러, 편안한 느낌",
        "bg_color": "#fffaf6",
        "main_color": "#ffd6ee",
        "mascot_image": "https://cdn.pixabay.com/photo/2016/11/22/20/31/balloons-1853650_1280.jpg",  # 예시
        "preview_image": "https://cdn.pixabay.com/photo/2016/11/22/20/31/balloons-1853650_1280.jpg",
    },
    {
        "name": "horror",
        "display_name": "공포 스타일",
        "description": "스산하고 어두운 배경, 공포/괴담 특화 테마",
        "bg_color": "#19191c",
        "main_color": "#e14545",
        "mascot_image": "https://cdn.pixabay.com/photo/2016/09/04/20/29/skull-1648952_1280.jpg",  # 예시
        "preview_image": "https://cdn.pixabay.com/photo/2016/09/04/20/29/skull-1648952_1280.jpg",
    },
]

for t in THEMES:
    obj, created = Theme.objects.get_or_create(
        name=t["name"],
        defaults={
            "display_name": t["display_name"],
            "description": t["description"],
            "bg_color": t["bg_color"],
            "main_color": t["main_color"],
            "mascot_image": t["mascot_image"],
            "preview_image": t["preview_image"],
            "is_active": True,
        }
    )
    if created:
        print(f"테마 [{t['display_name']}] 생성 완료!")
    else:
        print(f"테마 [{t['display_name']}] 이미 존재.")
