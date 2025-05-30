from django.utils.timezone import now
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import UserProfile

@receiver(user_logged_in)
def update_last_accessed(sender, user, request, **kwargs):
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.last_accessed = now()
    profile.save()
