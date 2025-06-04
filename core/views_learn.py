"""Views for concept learning pages."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def learn_home(request):
    """Simple entry page for learning content."""
    return render(request, "learn_home.html")

