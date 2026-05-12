from pathlib import Path

import pytest

from waeyong_core import (
    CuriosityRequest,
    LearningRecordInput,
    LearningRepository,
    get_activity_branch_label,
    normalize_request,
    normalize_topic_key,
)


def test_normalize_request_clamps_age_and_splits_interests() -> None:
    request = CuriosityRequest(
        question="하늘은 왜 파래요?",
        target_age=99,
        child_interests="공룡, 자동차",
        explanation_style="",
    )

    normalized = normalize_request(request)

    assert normalized.target_age == 8
    assert normalized.child_interests == ["공룡", "자동차"]
    assert normalized.explanation_style == "짧고 재밌게"


def test_curiosity_request_rejects_blank_question() -> None:
    with pytest.raises(ValueError):
        CuriosityRequest(question="   ", target_age=5)


def test_normalize_topic_key_compacts_whitespace() -> None:
    assert normalize_topic_key("  비   내림 의   원리  ") == "비 내림 의 원리"


def test_learning_repository_initializes_and_filters_records(tmp_path: Path) -> None:
    repo = LearningRepository(tmp_path / "learning.db")
    repo.save_learning_record(
        LearningRecordInput(
            learner_id="kid-01",
            question="비는 왜 내려?",
            study_title="비 내림의 원리 이해하기",
            core_concept="수증기가 물방울이 되어 떨어진다.",
            target_age=5,
            description_excerpt="비는 구름의 물방울이 떨어지는 거야.",
            outcome_summary="코치패키지·활동",
            question_category="과학·자연",
            result_payload='{"question":"비는 왜 내려?"}',
        )
    )

    categories = repo.list_question_categories("kid-01")
    records = repo.fetch_learning_records("kid-01", "과학·자연", limit=10)
    detail = repo.fetch_learning_record_detail(records[0]["id"])

    assert categories == [("과학·자연", 1)]
    assert len(records) == 1
    assert records[0]["question"] == "비는 왜 내려?"
    assert detail["result_payload"] == '{"question":"비는 왜 내려?"}'


def test_get_activity_branch_label_returns_korean_label() -> None:
    assert get_activity_branch_label("safe_home_experiment") == "집에서 해보는 안전 실험"
    assert get_activity_branch_label("observation_instead") == "관찰 놀이로 이어가기"
    assert get_activity_branch_label("dialogue_only") == "대화·역할 놀이 중심"
    assert get_activity_branch_label("unknown") == "unknown"
