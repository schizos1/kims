from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

def quick_login(request):
    # 빠른 로그인 화면
    return render(request, "quick_login.html")

def quick_login_action(request, username):
    # 사용자 별 패스워드 매핑
    pw_map = {
        "kimrin": "0424",
        "kimik": "0928",
        "admin": "khan0829##@"
    }
    password = pw_map.get(username)
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        if username == "admin":
            return redirect("/admin_dashboard/")
        else:
            return redirect("/student_dashboard/")
    return redirect("/")

def student_dashboard(request):
    # 비로그인 → 홈으로 이동
    if not request.user.is_authenticated:
        return redirect("/")
    # 관리자 → 관리자 대시보드로
    if request.user.username == "admin":
        return redirect("/admin_dashboard/")
    
    # UserProfile이 있는 경우(OneToOneField) 확장정보 추가
    userprofile = getattr(request.user, 'userprofile', None)
    context = {
        "user": request.user,          # Django 기본 User 객체
        "userprofile": userprofile,    # 확장 모델: 닉네임, 테마, 마스코트 등
        # "user_trophy_count": ...,    # 추후 트로피, 포인트 등 추가 가능
        # "user_point": ...,
        # "user_quiz_count": ...,
    }
    return render(request, "student_dashboard.html", context)

def admin_dashboard(request):
    if not request.user.is_authenticated or request.user.username != "admin":
        return redirect("/")
    return render(request, "admin_dashboard.html", {"user": request.user})
