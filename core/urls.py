from django.urls import path
from . import views
from .views_learn import learn_start_view, learn_detail_view
from .views_wrong import wrong_list_view, wrong_detail_view
from .views_stats import user_stats_view
from .views import CustomLoginView
from . import views, views_stats, views_trophy

urlpatterns = [
    path('quiz/batch/', views.batch_quiz_view, name='quiz_batch'),
    path('wrongnote/', views.wrongnote_view, name='wrongnote'),
    path('learn/start/', views_stats.learn_start_view, name='learn_start'),
    path('learn/<str:subject>/<int:lesson_id>/', views_stats.learn_detail_view, name='learn_detail'),
    path('wrong/', views_stats.wrong_list_view, name='wrong_list'),
    path('wrong/<int:question_id>/', views_stats.wrong_detail_view, name='wrong_detail'),
    path('user/<int:user_id>/stats/', views_stats.user_stats_view, name='user_stats'),
    path('user/<int:user_id>/trophies/', views_trophy.trophy_collection_view, name='user_trophies'),  # ✅ 추가
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
]

