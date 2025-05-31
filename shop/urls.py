# shop/urls.py
from django.urls import path
from . import views # 현재 디렉토리의 views.py를 가져옵니다.

app_name = 'shop' # 앱 네임스페이스를 'shop'으로 지정합니다.

urlpatterns = [
    # /shop/ 경로로 접속 시 views.shop_main 함수가 실행됩니다.
    # 이 URL의 이름은 'shop_main'입니다.
    path('', views.shop_main, name='shop_main'),

    # ... (다른 상점 관련 URL 패턴들이 있다면 여기에 추가됩니다.)
    # 예: path('item/<int:item_id>/', views.item_detail, name='item_detail'),
]