"""로그인 이벤트에 대한 트로피 지급 시그널."""
import logging
from django.contrib.auth.signals import user_logged_in
from django.db.models import F
from django.db import transaction
from django.dispatch import receiver

from .utils import check_and_award_trophies
from users.models import UserProfile

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def award_trophy_on_login(sender, user, request, **kwargs):
    """사용자 로그인 시 트로피 지급을 처리한다."""
    try:
        with transaction.atomic():
            profile = UserProfile.objects.get(user=user)
            profile.login_count = F('login_count') + 1
            profile.save(update_fields=['login_count'])
            logger.debug("Login count incremented for %s", user.username)
            check_and_award_trophies(user)
    except UserProfile.DoesNotExist:
        logger.error("UserProfile not found for %s", user.username)
    except Exception as exc:
        logger.error("Error checking trophies on login for %s: %s", user.username, exc)

