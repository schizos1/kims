"""트로피 앱의 관리자 설정 모듈로, 트로피와 사용자 트로피의 관리자 인터페이스를 정의합니다."""
from django.contrib import admin
from .models import Trophy, UserTrophy

@admin.register(Trophy)
class TrophyAdmin(admin.ModelAdmin):
    """트로피 모델의 관리자 인터페이스

    Attributes:
        list_display: 관리자 목록에 표시할 필드
        list_filter: 필터링 가능한 필드
        search_fields: 검색 가능한 필드
    """
    list_display = ('name', 'description', 'condition_type', 'condition_value', 'points')
    list_filter = ('condition_type', 'created_at')
    search_fields = ('name', 'description', 'required_subject')

    # ModelAdmin 내의 Meta 클래스는 일반적으로 사용되지 않으며,
    # 모델 자체의 Meta 클래스 정보가 활용됩니다.
    # 필요에 따라 주석 처리하거나 삭제해도 됩니다.
    # class Meta:
    #     verbose_name = "트로피"
    #     verbose_name_plural = "트로피 목록"

@admin.register(UserTrophy)
class UserTrophyAdmin(admin.ModelAdmin):
    """사용자 트로피 모델의 관리자 인터페이스

    Attributes:
        list_display: 관리자 목록에 표시할 필드
        list_filter: 필터링 가능한 필드
        search_fields: 검색 가능한 필드
    """
    list_display = ('user', 'trophy', 'awarded_at', 'is_hidden')
    list_filter = ('awarded_at', 'is_hidden')
    search_fields = ('user__username', 'trophy__name')

    # ModelAdmin 내의 Meta 클래스는 일반적으로 사용되지 않으며,
    # 모델 자체의 Meta 클래스 정보가 활용됩니다.
    # 필요에 따라 주석 처리하거나 삭제해도 됩니다.
    # class Meta:
    #     verbose_name = "사용자 트로피"
    #     verbose_name_plural = "사용자 트로피 목록"