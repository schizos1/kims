from .models import UserProfile

def user_profile_for_base(request):
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            return {'user_profile_for_base': profile}
        except UserProfile.DoesNotExist:
            return {'user_profile_for_base': None}
    return {}