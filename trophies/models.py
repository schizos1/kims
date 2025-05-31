"""트로피 앱의 모델 모듈로, 트로피와 사용자 트로피를 정의합니다."""
from django.db import models
from django.conf import settings
from django.utils import timezone

class Trophy(models.Model):
    """트로피 모델, 트로피 정보와 획득 조건을 정의합니다.

    Attributes:
        name: 트로피 이름, 최대 100자, 고유해야 함
        description: 트로피 설명
        icon: 트로피 아이콘 CDN URL
        condition_type: 트로피 획득 조건 유형
        condition_value: 조건 충족을 위한 수치
        required_subject: 과목별 조건용 과목 이름
        points: 트로피 획득 시 부여 포인트
        sound_effect: 획득 시 재생할 사운드 효과 CDN URL
        created_at: 트로피 생성일
        updated_at: 트로피 수정일
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="트로피 이름")
    description = models.TextField(verbose_name="트로피 설명")
    icon = models.URLField(max_length=200, default='', blank=True, verbose_name="아이콘 URL")
    condition_type = models.CharField(
        max_length=50,
        choices=[
            ('login_days', '로그인 일수'),
            ('total_quiz', '총 문제풀이 수'),
            ('subject_quiz', '과목별 문제풀이 수'),
            ('right_rate', '정답률'),
            ('total_wrong', '총 오답 수'),
            ('streak', '연속 출석 일수'),
            ('point_used', '사용한 포인트'),
        ],
        default='login_days',
        verbose_name="조건 유형"
    )
    condition_value = models.IntegerField(default=0, verbose_name="조건 수치")
    required_subject = models.CharField(max_length=50, default='', blank=True, verbose_name="필요 과목")
    points = models.IntegerField(default=0, verbose_name="획득 포인트")
    sound_effect = models.URLField(max_length=200, default='', blank=True, verbose_name="사운드 효과 URL")
    created_at = models.DateTimeField(
        default=timezone.now,  # 기존 행에 현재 시간 기본값 설정
        verbose_name="생성일"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        db_table = 'trophies_trophy'
        verbose_name = "트로피"
        verbose_name_plural = "트로피 목록"

    def __str__(self):
        return self.name

class UserTrophy(models.Model):
    """사용자 트로피 모델, 사용자와 트로피의 관계를 정의합니다.

    Attributes:
        user: 사용자 (ForeignKey)
        trophy: 트로피 (ForeignKey)
        awarded_at: 트로피 획득 시간
        is_hidden: 마이페이지에서 숨김 여부
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_trophies',
        verbose_name="사용자"
    )
    trophy = models.ForeignKey(
        'Trophy',
        on_delete=models.CASCADE,
        related_name='user_trophies',
        verbose_name="트로피"
    )
    awarded_at = models.DateTimeField(auto_now_add=True, verbose_name="획득일")
    is_hidden = models.BooleanField(default=False, verbose_name="숨김 여부")

    class Meta:
        db_table = 'trophies_usertrophy'
        unique_together = ('user', 'trophy')
        verbose_name = "사용자 트로피"
        verbose_name_plural = "사용자 트로피 목록"

    def __str__(self):
        return f"{self.user.username} - {self.trophy.name}"