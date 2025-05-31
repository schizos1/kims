from django.urls import path
from . import views

app_name = 'trophies'

urlpatterns = [
    path('my/', views.my_trophies, name='my_trophies'),
    # ... (트로피 상세/랭킹 등)
]
