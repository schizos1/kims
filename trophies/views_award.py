from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect

from .utils import check_and_award_trophies


@login_required
def award_trophies(request):
    """수동으로 사용자의 트로피 지급을 트리거한다."""
    check_and_award_trophies(request.user)
    messages.success(request, "트로피 지급을 확인했습니다.")
    return redirect('trophies:my_trophies')

