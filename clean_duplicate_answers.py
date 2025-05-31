"""UserAnswerLog의 중복 항목을 정리하는 스크립트"""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "study_site.settings")
import django
django.setup()

from quiz.models import UserAnswerLog
from django.db.models import Count, Max # Count 임포트 추가

def clean_duplicates():
    """UserAnswerLog에서 중복된 (user_id, question_id) 항목을 최신 제출(timestamp 기준)만 남기고 삭제"""
    try:
        # 중복된 (user_id, question_id) 쌍과 각 쌍의 개수, 최신 timestamp 찾기
        duplicates_info = (
            UserAnswerLog.objects.values('user_id', 'question_id')
            .annotate(
                entry_count=Count('id'),
                latest_timestamp=Max('timestamp')
            )
            .filter(entry_count__gt=1)
        )

        if not duplicates_info:
            print("처리할 중복 항목이 없습니다.")
            return

        for dup_info in duplicates_info:
            user_id = dup_info['user_id']
            question_id = dup_info['question_id']
            latest_ts_for_group = dup_info['latest_timestamp']

            # 해당 (user_id, question_id) 조합의 모든 항목 중,
            # 가장 최신 timestamp를 가진 항목들 중에서 pk(id)가 가장 큰 (혹은 작은, 일관성만 있다면) 하나를 식별
            # 여기서는 latest_timestamp를 가진 첫 번째 항목을 유지한다고 가정
            # 더 확실하게는, latest_timestamp를 가진 항목이 여러 개일 경우 그 중 하나만 남기는 로직 필요
            # 예: latest_timestamp를 가진 항목 중 id가 가장 작은(혹은 큰) 것을 유지
            
            # 동일 user_id, question_id, latest_timestamp를 가진 항목들 중 하나(예: id가 가장 작은 것)를 선택하여 ID를 가져옴
            # 또는 latest_timestamp를 가진 항목이 정확히 하나라고 가정할 수 있다면 이 단계는 더 단순해짐
            
            # 가장 최신 timestamp를 가진 항목들 가져오기
            latest_entries_for_group = UserAnswerLog.objects.filter(
                user_id=user_id,
                question_id=question_id,
                timestamp=latest_ts_for_group
            ).order_by('id') # timestamp가 같다면 id가 작은 것을 기준으로 삼음 (혹은 -id로 큰 것)

            if not latest_entries_for_group.exists():
                # 이 경우는 이론상 발생하기 어려움 (duplicates_info에서 latest_timestamp를 가져왔으므로)
                print(f"경고: user_id={user_id}, question_id={question_id}에 대한 최신 항목을 찾을 수 없습니다.")
                continue
            
            # 유지할 최신 항목의 ID (동일 timestamp가 여러개면 그 중 첫번째)
            id_to_keep = latest_entries_for_group.first().id

            # 유지할 ID를 제외하고 해당 (user, question) 조합의 모든 항목 삭제
            deleted_count, _ = UserAnswerLog.objects.filter(
                user_id=user_id,
                question_id=question_id
            ).exclude(id=id_to_keep).delete()

            if deleted_count > 0:
                print(f"중복 정리: user_id={user_id}, question_id={question_id}, {deleted_count}개 항목 삭제, ID {id_to_keep} 유지")
            else:
                # 이 경우는 중복이 실제로 제거되지 않았음을 의미할 수 있음 (로직 재검토 필요)
                # 또는 duplicates_info는 count > 1 이지만, id_to_keep 외에 삭제할 것이 없는 경우
                print(f"정보: user_id={user_id}, question_id={question_id}, 추가로 삭제된 항목 없음 (ID {id_to_keep} 유지).")


        print("중복 정리 완료.")

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    clean_duplicates()