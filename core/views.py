"""Core views handling basic login actions."""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login


def quick_login(request):
    """Render the quick login page."""
    return render(request, "quick_login.html")


def quick_login_action(request, username):
    """Authenticate and log in the given user."""
    pw_map = {
        "kimrin": "0424",
        "kimik": "0928",
        "admin": "khan0829##@",
        "test": "0928",
    }
    password = pw_map.get(username)
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        if username == "admin":
            return redirect("/admin_dashboard/")
        return redirect("/student_dashboard/")
    return redirect("/")

