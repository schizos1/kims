# users/models.py (수정된 전체 파일)

from django.conf import settings # ✨ 이 줄을 추가해주세요 ✨
from django.db import models
from django.contrib.auth.models import User
# from django.templatetags.static import static # active_mascot_image_url 에서 기본 이미지 경로를 위해 필요시

class Theme(models.Model):
    """선택 테마 모델, 캐릭터, 색상, 배경 등을 정의합니다."""
    name = models.CharField(max_length=30, unique=True, verbose_name="테마 이름")
    display_name = models.CharField(max_length=30, verbose_name="표시 이름")
    description = models.CharField(max_length=100, blank=True, verbose_name="테마 설명")
    bg_color = models.CharField(max_length=15, blank=True, verbose_name="배경 색상")
    main_color = models.CharField(max_length=15, blank=True, verbose_name="주요 색상")
    mascot_image = models.ImageField(upload_to='theme_mascots/', blank=True, null=True, verbose_name="마스코트 이미지")# Theme의 마스코트는 URLField
    preview_image = models.URLField(blank=True, verbose_name="미리보기 이미지 URL")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")

    def __str__(self):
        return self.display_name

    class Meta:
        db_table = 'users_theme' # Theme 모델은 'users_theme' 테이블 사용
        verbose_name = "테마"
        verbose_name_plural = "테마 목록"

class Mascot(models.Model):
    """관리자가 업로드하는 갤러리 마스코트 모델입니다."""
    name = models.CharField(max_length=50, unique=True, verbose_name="마스코트 이름")
    image = models.ImageField(upload_to='mascots/gallery/', verbose_name="마스코트 이미지") # Mascot의 이미지는 ImageField
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")

    def __str__(self):
        return self.name # Mascot 모델은 'name' 필드를 사용

    class Meta:
        db_table = 'users_mascot' # Mascot 모델은 'users_mascot' 테이블 사용 (또는 이 줄을 삭제하여 Django 기본값 사용)
        verbose_name = "갤러리 마스코트"
        verbose_name_plural = "갤러리 마스코트 목록"

class UserProfile(models.Model):
    """사용자 프로필 모델, 사용자별 추가 정보와 테마/마스코트 선택을 저장합니다."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="사용자")
    nickname = models.CharField(max_length=20, default='Guest', verbose_name="닉네임")
    mascot_name = models.CharField(max_length=20, blank=True, verbose_name="마스코트 애칭") 
    selected_theme = models.ForeignKey(
        Theme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="선택된 테마"
    )
    selected_mascot = models.ForeignKey(
        Mascot, 
        null=True,
        blank=True,
        on_delete=models.SET_NULL, 
        verbose_name="선택 마스코트"
    )
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name="마지막 접속")
    points = models.IntegerField(default=0, verbose_name="포인트")
    login_count = models.IntegerField(default=0, verbose_name="로그인 횟수")
    points_used = models.IntegerField(default=0, verbose_name="사용한 포인트")
    minigame_win_count = models.IntegerField(default=0, verbose_name="미니게임 승리 수")
    minigame_loss_count = models.IntegerField(default=0, verbose_name="미니게임 패배 수")

    def __str__(self):
        return self.nickname

    @property
    def active_mascot_image_url(self):
        """현재 사용자에게 표시될 마스코트 이미지 URL을 결정합니다."""
        if self.selected_mascot and self.selected_mascot.image:
            return self.selected_mascot.image.url
        elif self.selected_theme and self.selected_theme.mascot_image: # 테마의 mascot_image는 URLField
            return self.selected_theme.mascot_image
        # 기본 이미지 예시 (static 파일 사용 시)
        # from django.templatetags.static import static
        # return static('images/default_mascot.png') 
        return None # 또는 적절한 기본 이미지 URL 문자열

    class Meta:
        db_table = 'users_userprofile'
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필 목록"

class PointTransaction(models.Model):
    """포인트 거래(획득/사용) 내역을 기록하는 모델입니다."""
    TRANSACTION_TYPES = [
        ('allowance_request', '용돈 신청'),
        ('trophy_award', '트로피 획득'),
        ('shop_purchase', '상점 구매'),
        ('minigame_fee', '미니게임 참가비'),
        ('minigame_reward', '미니게임 보상'),
        ('admin_adjustment', '관리자 조정'),
        # 필요에 따라 다른 유형 추가 가능
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='point_transactions',
        verbose_name="사용자"
    )
    transaction_type = models.CharField(
        max_length=50, 
        choices=TRANSACTION_TYPES, 
        verbose_name="거래 유형"
    )
    points_changed = models.IntegerField(verbose_name="포인트 변경량") # 사용 시 음수, 획득 시 양수
    description = models.CharField(max_length=255, blank=True, verbose_name="설명") # 예: "퀴즈 마스터 트로피 획득"
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="거래 시각")

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()}: {self.points_changed}P ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        db_table = 'users_pointtransaction'
        verbose_name = "포인트 거래 내역"
        verbose_name_plural = "포인트 거래 내역 목록"
        ordering = ['-timestamp'] # 최신 거래가 위로 오도록 정렬