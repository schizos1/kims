"""
- 학생 상점, 아이템/용돈 신청 샘플
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Item, Purchase


@login_required
def store_main(request):
    items = Item.objects.filter(is_active=True)
    return render(request, "store/main.html", {"items": items})

