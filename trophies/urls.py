from django.urls import path
from . import views_display, views_award

app_name = 'trophies'

urlpatterns = [
    path('my/', views_display.my_trophies, name='my_trophies'),
    path('award/', views_award.award_trophies, name='award_trophies'),
]