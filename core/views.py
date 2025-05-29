from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

def quick_login(request):
    return render(request, "quick_login.html")

def quick_login_action(request, username):
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
    if not request.user.is_authenticated:
        return redirect("/")
    if request.user.username == "admin":
        return redirect("/admin_dashboard/")
    return render(request, "student_dashboard.html", {"user": request.user})

def admin_dashboard(request):
    if not request.user.is_authenticated or request.user.username != "admin":
        return redirect("/")
    return render(request, "admin_dashboard.html", {"user": request.user})
