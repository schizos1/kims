from django.urls import path
from . import views

urlpatterns = [
    path('my/', views.my_trophies, name='my_trophies'),
    # ... (트로피 상세/랭킹 등)
]
