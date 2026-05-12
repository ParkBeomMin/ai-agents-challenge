from pathlib import Path

import pytest

from waeyong_core import (
    ActivityFeasibility,
    ActivityGuide,
    CreativeQuestionGuide,
    CuriosityRequest,
    ImageNeedDecision,
    LearningRecordInput,
    LearningRepository,
    ParentCoachPack,
    QuestionAnalysis,
    StudySubject,
    WaeyongWorkflow,
    get_activity_branch_label,
    get_workflow_progress_message,
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


def _build_stubbed_workflow(image_needed: bool) -> WaeyongWorkflow:
    workflow = WaeyongWorkflow.__new__(WaeyongWorkflow)
    workflow._ensure_child_profile = lambda state: {
        "target_age": state["target_age"],
        "child_interests": [],
        "explanation_style": "짧고 재밌게",
        "learner_id": "",
    }
    workflow._analyze_question = lambda state: {
        "question_analysis": QuestionAnalysis(
            question_type="과학·자연",
            child_intent="비가 오는 이유가 궁금함",
            parent_need="쉽고 짧은 설명",
            difficulty_level="쉬움",
        )
    }
    workflow._convert_study_subject = lambda state: {
        "study_subject": StudySubject(
            title="비가 오는 원리",
            core_concept="구름 속 물방울이 커져 떨어진다.",
            learning_goal="비의 기본 원리를 이해한다.",
            keywords=["비", "구름", "물방울"],
        )
    }
    workflow._load_prior_learning = lambda state: {"prior_learning_notes": ""}
    workflow._generate_parent_coach = lambda state: {
        "coach_pack": ParentCoachPack(
            short_answer_30s="구름 속 물방울이 무거워지면 비가 돼.",
            story_answer_3min="구름 속 작은 물방울이 모이면 비가 돼.",
            play_and_picture_tip="손으로 비를 흉내 내 봐요.",
            parent_read_aloud_script="구름 속 물방울이 모여 비가 된단다.",
            phrases_to_avoid="몰라",
            say_instead="같이 알아보자",
            follow_up_questions=["구름은 왜 생길까?", "비 다음엔 뭐가 올까?", "물은 어디로 갈까?"],
            creative_question_guide=CreativeQuestionGuide(
                observation="창밖 빗방울을 같이 살펴볼까?",
                imagination="구름이 말을 할 수 있다면 뭐라고 할까?",
                comparison="비와 눈은 뭐가 다를까?",
                inquiry="물방울은 어떻게 커질까?",
            ),
            next_curiosity_topics=["구름은 왜 떠 있을까?", "눈은 왜 올까?", "번개는 왜 칠까?"],
        )
    }
    workflow._decide_activity_feasibility = lambda state: {
        "activity_feasibility": ActivityFeasibility(
            branch="observation_instead",
            reason="집에서 안전하게 관찰하기 좋음",
        )
    }
    workflow._generate_activity_guide = lambda state: {
        "activity_guide": ActivityGuide(
            title="빗방울 관찰 놀이",
            materials=["창문", "종이", "색연필"],
            steps=["빗방울을 본다.", "모양을 그린다."],
            safety_note="창문은 혼자 열지 않아요.",
            kind_label="관찰 놀이",
        )
    }
    workflow._decide_image_need = lambda state: {
        "image_need": ImageNeedDecision(
            need_image=image_needed,
            reason="테스트용 이미지 분기",
        )
    }
    workflow._create_image_card = lambda state: {
        "image_card_url": "image_card.png",
        "image_card_prompt_en": "rain cloud for kids",
        "image_card_prompts": ["rain cloud for kids"],
        "image_card_paths": ["image_card.png"],
    }
    workflow._skip_image_card = lambda state: {
        "image_card_url": "",
        "image_card_prompt_en": "",
        "image_card_prompts": [],
        "image_card_paths": [],
    }
    workflow._save_learning_record = lambda state: {
        "saved_record_id": 1,
        "related_question_suggestions": ["구름은 왜 하얄까?"],
        "result_payload": "{}",
    }
    workflow.graph = WaeyongWorkflow._build_graph(workflow)
    return workflow


def test_workflow_progress_messages_map_node_names_to_korean_labels() -> None:
    assert get_workflow_progress_message("analyze_question") == "질문을 분석하고 있어요."
    assert get_workflow_progress_message("generate_activity_guide") == "활동 가이드를 만들고 있어요."
    assert get_workflow_progress_message("create_image_card") == "이미지 카드를 만들고 있어요."
    assert (
        get_workflow_progress_message("skip_image_card")
        == "이미지 카드는 생략하고 기록을 정리하고 있어요."
    )
    assert get_workflow_progress_message("unknown") == "왜용이 답을 준비하고 있어요."


def test_workflow_progress_callback_reports_each_node_for_image_creation_branch() -> None:
    workflow = _build_stubbed_workflow(image_needed=True)
    progress_events: list[tuple[str, str]] = []

    workflow.run(
        CuriosityRequest(question="비는 왜 와?", target_age=5),
        thread_id="test-create-image",
        progress_callback=lambda node_name, message: progress_events.append(
            (node_name, message)
        ),
    )

    expected_nodes = [
        "ensure_child_profile",
        "analyze_question",
        "convert_study_subject",
        "load_prior_learning",
        "generate_parent_coach",
        "decide_activity_feasibility",
        "generate_activity_guide",
        "decide_image_need",
        "create_image_card",
        "save_learning_record",
    ]
    assert [node_name for node_name, _ in progress_events] == expected_nodes
    assert progress_events[-1] == (
        "save_learning_record",
        "학습 기록을 저장하고 있어요.",
    )


def test_workflow_progress_callback_reports_skip_image_branch() -> None:
    workflow = _build_stubbed_workflow(image_needed=False)
    progress_events: list[tuple[str, str]] = []

    workflow.run(
        CuriosityRequest(question="비는 왜 와?", target_age=5),
        thread_id="test-skip-image",
        progress_callback=lambda node_name, message: progress_events.append(
            (node_name, message)
        ),
    )

    assert progress_events[-2:] == [
        ("skip_image_card", "이미지 카드는 생략하고 기록을 정리하고 있어요."),
        ("save_learning_record", "학습 기록을 저장하고 있어요."),
    ]


def test_waeyong_core_does_not_keep_child_reaction_note_flow() -> None:
    core_py = Path(__file__).resolve().parents[1] / "waeyong_core.py"
    content = core_py.read_text(encoding="utf-8")

    assert "child_reaction_note" not in content
    assert "부모메모" not in content
