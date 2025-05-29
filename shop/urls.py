from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_main, name='shop_main'),
    # ... (상점/구매내역 등)
]
