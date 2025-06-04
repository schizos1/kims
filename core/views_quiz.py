"""Views handling quiz dashboards and related pages."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .utils import get_user_profile, get_attendance_context
from .services.quiz_service import calculate_user_stats


@login_required
def student_dashboard(request):
    """Render student dashboard with attendance and quiz stats."""
    if request.user.username == "admin":
        return redirect("/admin_dashboard/")

    user = request.user
    context = {
        "user": user,
        "userprofile": get_user_profile(user),
    }
    context.update(get_attendance_context(user))
    context.update(calculate_user_stats(user))
    return render(request, "student_dashboard.html", context)


@login_required
def admin_dashboard(request):
    """Render admin dashboard page."""
    if request.user.username != "admin":
        return redirect("/")
    return render(request, "admin_dashboard.html", {"user": request.user})
