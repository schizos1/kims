# quiz/management/commands/normalize_math_lessons.py

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from quiz.models import Subject, Lesson, Question # models.py 위치에 따라 임포트 경로 조정 필요

class Command(BaseCommand):
    help = '수학 과목의 "한 자리 수 곱셈" 관련 유사 단원명을 표준화하고, 연결된 문제들을 재지정 후 이전 단원을 삭제합니다.'

    def handle(self, *args, **options):
        subject_name_to_normalize = "수학"
        # ★ 대표 단원명 (이 이름으로 통일합니다. 데이터베이스에 이 이름의 단원이 없다면 새로 생성됩니다.)
        canonical_lesson_name = "한 자리 수 곱셈" 

        # 여기에 정리하고 싶은 "한 자리 수 곱셈"의 다양한 유사/중복 단원명들을 정확히 적어주세요.
        # 대표 단원명 자체도 포함될 수 있습니다 (스크립트가 알아서 처리합니다).
        variant_lesson_names_to_merge = [
            "한 자리 수 곱셈",    # 대표 단원명과 같거나, 약간 다른 표현
            "한자리수 곱셈",    # 띄어쓰기 없음
            "한 자리 수의 곱셈", # 조사 '의' 포함
            # 추가적으로 발견되는 "한 자리 수 곱셈"의 다른 표현들을 여기에 추가하세요.
            # 이 목록에 있는 이름의 단원들이 모두 `canonical_lesson_name`으로 통합됩니다.
        ]

        self.stdout.write(self.style.NOTICE(
            f"'{subject_name_to_normalize}' 과목의 단원명 정규화를 시작합니다. "
            f"유사 단원들을 '{canonical_lesson_name}'으로 통합합니다..."
        ))

        try:
            # 1. 대상 과목 가져오기
            subject = Subject.objects.get(name=subject_name_to_normalize)
            self.stdout.write(f"'{subject.name}' 과목을 찾았습니다.")
        except Subject.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"오류: '{subject_name_to_normalize}' 과목을 찾을 수 없습니다. 스크립트를 종료합니다."))
            return

        # 2. 데이터베이스 변경 작업을 하나의 트랜잭션으로 묶어서 안전하게 처리
        try:
            with transaction.atomic():
                # 2a. 대표 단원(Canonical Lesson) 객체를 가져오거나 생성합니다.
                # 이 단원이 모든 유사 단원의 문제들을 통합할 기준 단원이 됩니다.
                canonical_lesson, created = Lesson.objects.get_or_create(
                    subject=subject,
                    unit_name=canonical_lesson_name,
                    defaults={
                        'grade': '', # 대표 단원의 학년 정보 (필요시 정확한 값으로 설정)
                        'concept': f'{canonical_lesson_name}에 대한 기본 개념입니다.' # 대표 단원의 개념 설명 (필요시 설정)
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"대표 단원 '{canonical_lesson.unit_name}' (ID: {canonical_lesson.id}, 과목: {subject.name})을 새로 생성했습니다."
                    ))
                else:
                    self.stdout.write(
                        f"대표 단원 '{canonical_lesson.unit_name}' (ID: {canonical_lesson.id}, 과목: {subject.name})을 찾았습니다."
                    )

                lessons_to_delete_pks = set() # 삭제할 유사 단원의 PK들을 저장 (중복 방지)

                # 2b. 유사 단원명 목록을 순회하며 처리
                for variant_name in variant_lesson_names_to_merge:
                    # 현재 과목 내에서 해당 유사 단원명을 가진 Lesson 객체들을 찾습니다.
                    # (이름이 완전히 똑같은 중복 단원이 여러 개 있을 수도 있습니다.)
                    lessons_with_variant_name = Lesson.objects.filter(subject=subject, unit_name=variant_name)

                    for lesson_to_process in lessons_with_variant_name:
                        # 만약 현재 처리 중인 단원이 대표 단원 그 자체라면, 건너뜁니다.
                        if lesson_to_process.id == canonical_lesson.id:
                            continue

                        self.stdout.write(
                            f"  처리 대상 유사 단원: '{lesson_to_process.unit_name}' (ID: {lesson_to_process.id})"
                        )

                        # 이 유사 단원에 연결된 모든 문제들을 대표 단원(canonical_lesson)으로 옮깁니다.
                        questions_to_move = Question.objects.filter(lesson=lesson_to_process)
                        updated_question_count = questions_to_move.update(lesson=canonical_lesson)

                        if updated_question_count > 0:
                            self.stdout.write(self.style.SUCCESS(
                                f"    -> '{lesson_to_process.unit_name}' 단원의 문제 {updated_question_count}개를 "
                                f"대표 단원 '{canonical_lesson.unit_name}'으로 이전했습니다."
                            ))
                        else:
                            self.stdout.write(
                                f"    -> '{lesson_to_process.unit_name}' 단원에는 이전할 문제가 없습니다."
                            )
                        
                        # 문제 이전이 완료된 이 유사 단원은 삭제 목록에 추가합니다.
                        lessons_to_delete_pks.add(lesson_to_process.pk)

                # 2c. 삭제 목록에 있는 모든 유사 단원들을 실제로 삭제합니다.
                if lessons_to_delete_pks:
                    self.stdout.write(f"\n  총 {len(lessons_to_delete_pks)}개의 이전된 유사 단원을 삭제합니다...")
                    deleted_count, _ = Lesson.objects.filter(pk__in=list(lessons_to_delete_pks)).delete()
                    self.stdout.write(self.style.SUCCESS(f"  {deleted_count}개의 단원을 성공적으로 삭제했습니다."))
                else:
                    self.stdout.write("\n  삭제할 추가 유사 단원이 없습니다.")

            self.stdout.write(self.style.SUCCESS(f"\n'{subject_name_to_normalize}' 과목의 '{canonical_lesson_name}' 관련 단원명 정규화 작업이 성공적으로 완료되었습니다."))

        except Exception as e: # 트랜잭션 내에서 다른 예기치 않은 오류 발생 시
            self.stderr.write(self.style.ERROR(f"단원 정리 작업 중 오류 발생: {e}"))
            # transaction.atomic() 블록 내에서 예외가 발생하면 자동으로 롤백됩니다.
            raise CommandError(f"작업 실패: {e}")