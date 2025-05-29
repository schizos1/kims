from django.contrib.auth.models import User
from users.models import UserProfile

if not User.objects.filter(username="kimrin").exists():
    u1 = User.objects.create_user(username="kimrin", password="0424")
    UserProfile.objects.create(user=u1, nickname="김린")
    print("김린 생성 완료!")

if not User.objects.filter(username="kimik").exists():
    u2 = User.objects.create_user(username="kimik", password="0928")
    UserProfile.objects.create(user=u2, nickname="김익")
    print("김익 생성 완료!")
