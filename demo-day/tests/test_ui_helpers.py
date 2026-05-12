from ui_helpers import (
    build_guidance_card_html,
    build_guidance_pair_html,
    build_activity_steps_html,
    build_creative_question_guide_html,
    build_paragraph_cards_html,
    build_material_list_html,
    build_question_chips_html,
    build_script_stack_html,
    build_summary_card_html,
    build_history_button_label,
    build_history_button_text,
    build_long_answer_block_html,
    build_short_answer_card_html,
    format_multiline_markdown,
    get_long_answer_card_title,
    get_parent_coach_tab_labels,
    parse_script_turns,
    resolve_active_result_source,
    resolve_selected_record_id,
)


def test_get_parent_coach_tab_labels_uses_short_and_long_answer_labels() -> None:
    assert get_parent_coach_tab_labels() == (
        "짧은 답",
        "긴 답",
        "대화 스크립트",
        "대화 확장",
    )


def test_format_multiline_markdown_preserves_paragraph_breaks() -> None:
    text = "첫 문장입니다.\n둘째 문장입니다.\n\n다음 문단입니다."

    formatted = format_multiline_markdown(text)

    assert formatted == "첫 문장입니다.  \n둘째 문장입니다.\n\n다음 문단입니다."


def test_parse_script_turns_splits_parent_and_child_lines() -> None:
    script = "아이: 왜 비가 와?\n부모: 구름 속 물방울이 떨어지는 거야.\n같이 하늘을 볼까?"

    turns = parse_script_turns(script)

    assert turns == [
        {"speaker": "아이", "text": "왜 비가 와?"},
        {"speaker": "부모", "text": "구름 속 물방울이 떨어지는 거야."},
        {"speaker": "안내", "text": "같이 하늘을 볼까?"},
    ]


def test_build_short_answer_card_html_contains_title_and_body() -> None:
    html = build_short_answer_card_html("짧은 답", "비는 구름의 물방울이 떨어지는 거야.")

    assert "짧은 답" in html
    assert "비는 구름의 물방울이 떨어지는 거야." in html
    assert "answer-card" in html


def test_build_long_answer_block_html_keeps_single_answer_block() -> None:
    html = build_long_answer_block_html("긴 답", "첫 문단입니다.\n\n둘째 문단입니다.")

    assert "long-answer-block" in html
    assert "긴 답" in html
    assert "첫 문단입니다." in html
    assert "둘째 문단입니다." in html
    assert "paragraph-card" not in html
    assert "long-answer-paragraph" in html


def test_build_long_answer_block_html_auto_splits_single_paragraph_story() -> None:
    html = build_long_answer_block_html(
        "긴 답",
        "옛날 옛적 하늘에는 많은 색깔들이 있었단다. 그런데 어느 날 태양이 하늘을 비추었어. "
        "파란빛은 공기 중에서 더 잘 퍼졌지. 그래서 우리가 하늘을 파랗게 보는 거야.",
    )

    assert html.count("long-answer-paragraph") >= 2
    assert "파란빛은 공기 중에서 더 잘 퍼졌지." in html


def test_get_long_answer_card_title_returns_recommended_copy() -> None:
    assert get_long_answer_card_title() == "이어서 이렇게 이야기해보세요"


def test_build_question_chips_html_renders_each_question() -> None:
    html = build_question_chips_html(["왜 그럴까?", "같이 해볼까?"])

    assert "question-chip" in html
    assert "왜 그럴까?" in html
    assert "같이 해볼까?" in html


def test_build_question_chips_html_returns_empty_for_blank_items() -> None:
    html = build_question_chips_html(["", "  "])

    assert html == ""


def test_build_history_button_label_combines_category_and_question() -> None:
    label = build_history_button_label("과학·자연", "비는 왜 내려요?")

    assert label == "과학·자연 · 비는 왜 내려요?"


def test_build_script_stack_html_uses_vertical_bubbles() -> None:
    html = build_script_stack_html("아이: 왜 비가 와?\n부모: 구름 속 물방울이 떨어지는 거야.")

    assert "script-stack" in html
    assert "script-stack-item" in html
    assert "왜 비가 와?" in html
    assert "구름 속 물방울이 떨어지는 거야." in html
    assert "script-bubble" in html
    assert "script-row" not in html


def test_build_summary_card_html_contains_value_and_caption() -> None:
    html = build_summary_card_html("질문 유형", "과학·자연", "비가 오는 이유를 알고 싶어함")

    assert "summary-card" in html
    assert "질문 유형" in html
    assert "과학·자연" in html
    assert "비가 오는 이유를 알고 싶어함" in html


def test_build_material_list_html_renders_pretty_material_items() -> None:
    html = build_material_list_html(["종이컵", "물", "스푼"])

    assert "material-list" in html
    assert "material-item" in html
    assert "종이컵" in html
    assert "물" in html
    assert "스푼" in html


def test_build_activity_steps_html_renders_numbered_steps() -> None:
    html = build_activity_steps_html(
        ["컵에 물을 담아요.", "색연필로 물의 변화를 그려봐요."]
    )

    assert "activity-steps" in html
    assert "activity-step-item" in html
    assert "activity-step-number" in html
    assert "1" in html
    assert "2" in html
    assert "컵에 물을 담아요." in html
    assert "색연필로 물의 변화를 그려봐요." in html


def test_build_guidance_card_html_renders_advice_card() -> None:
    html = build_guidance_card_html(
        title="피하면 좋은 말",
        body='"빛이 산란해서 이렇게 된거야"',
        tone="avoid",
    )

    assert "guidance-card" in html
    assert "guidance-card avoid" in html
    assert "피하면 좋은 말" in html
    assert "&quot;빛이 산란해서 이렇게 된거야&quot;" in html


def test_build_guidance_pair_html_renders_split_layout() -> None:
    html = build_guidance_pair_html(
        avoid_body="이렇게 말하면 단정적으로 들릴 수 있어요.",
        instead_body="아이 눈높이로 풀어서 말해보세요.",
    )

    assert "guidance-pair" in html
    assert "guidance-panel-divider" in html
    assert "피하면 좋은 말" in html
    assert "대신 이렇게 말해보세요" in html
    assert "이렇게 말하면 단정적으로 들릴 수 있어요." in html
    assert "아이 눈높이로 풀어서 말해보세요." in html


def test_build_creative_question_guide_html_renders_guide_cards() -> None:
    html = build_creative_question_guide_html(
        observation="무엇이 보이는지 같이 찾아봐요.",
        imagination="만약 색이 바뀐다면 어떨지 상상해봐요.",
        comparison="어제와 오늘을 비교해봐요.",
        inquiry="직접 해보면 어떤 결과가 나올지 물어봐요.",
    )

    assert "creative-guide" in html
    assert "creative-guide-item" in html
    assert "관찰" in html
    assert "상상" in html
    assert "비교" in html
    assert "탐구" in html
    assert "무엇이 보이는지 같이 찾아봐요." in html
    assert "직접 해보면 어떤 결과가 나올지 물어봐요." in html


def test_build_history_button_text_combines_title_and_meta() -> None:
    text = build_history_button_text(
        category="과학·자연",
        question="비는 왜 내려요?",
        created_date="2026-05-12",
    )

    assert text == "`과학·자연`\n**비는 왜 내려요?**\n2026-05-12"


def test_resolve_selected_record_id_prefers_clicked_record() -> None:
    selected = resolve_selected_record_id(
        available_ids=[3, 5, 8],
        current_selected_id=3,
        clicked_record_id=8,
    )

    assert selected == 8


def test_resolve_active_result_source_prefers_latest_when_requested() -> None:
    source = resolve_active_result_source(
        preferred_source="latest",
        latest_result={"question": "새 질문"},
        selected_record_result='{"question":"최근 기록"}',
    )

    assert source == "latest"


def test_resolve_active_result_source_prefers_history_when_requested() -> None:
    source = resolve_active_result_source(
        preferred_source="history",
        latest_result={"question": "새 질문"},
        selected_record_result='{"question":"최근 기록"}',
    )

    assert source == "history"
