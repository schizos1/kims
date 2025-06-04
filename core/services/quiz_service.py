"""Business logic related to quiz progress and stats."""
from quiz.models import UserAnswerLog


def calculate_user_stats(user):
    """Return basic quiz statistics for the given user."""
    total_answered = UserAnswerLog.objects.filter(user=user).count()
    correct = UserAnswerLog.objects.filter(user=user, is_correct=True).count()
    return {
        "total_answered": total_answered,
        "correct": correct,
        "accuracy": correct / total_answered if total_answered else 0,
    }