from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from users.models import UserProfile, PointTransaction
from trophies.utils import check_and_award_trophies
import json

@csrf_exempt
@login_required
def update_number_shooter_score(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        score = int(data.get('score', 0))
        profile = request.user.profile

        # 최고점수는 계속 갱신(최대 5000점 제한)
        old_best = getattr(profile, 'number_shooter_best', 0)
        if score > old_best:
            profile.number_shooter_best = min(score, 5000)
            profile.save(update_fields=['number_shooter_best'])

        # ⭐️ 여기부터 포인트 “매번” 지급 ⭐️
        # 예시: 500점마다 300포인트 (최대 5000점까지)
        score_capped = min(score, 5000)
        points_awarded = (score_capped // 500) * 300
        point_given = 0

        if points_awarded > 0:
            # 바로 포인트 지급 (누적)
            profile.points += points_awarded
            profile.save(update_fields=['points'])
            # PointTransaction 기록
            PointTransaction.objects.create(
                user=request.user,
                transaction_type='minigame_reward',
                points_changed=points_awarded,
                description=f"넘버슈터 점수 {score_capped}점 보상"
            )
            point_given = points_awarded

        # 트로피 지급은 기존대로
        check_and_award_trophies(request.user)

        return JsonResponse({
            'result': 'ok',
            'point_awarded': point_given,
        })
    return JsonResponse({'error': 'bad request'}, status=400)
