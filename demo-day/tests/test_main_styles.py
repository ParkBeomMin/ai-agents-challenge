from pathlib import Path


def test_long_answer_block_has_bottom_spacing() -> None:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    content = main_py.read_text(encoding="utf-8")

    block_start = content.index(".long-answer-block {")
    block_end = content.index("      .long-answer-title {", block_start)
    long_answer_block = content[block_start:block_end]

    assert "margin-bottom:" in long_answer_block


def test_activity_guide_does_not_render_title_and_branch_summary() -> None:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    content = main_py.read_text(encoding="utf-8")

    section_start = content.index('        st.markdown("### 활동 가이드")')
    section_end = content.index("        materials_col, steps_col = st.columns([1, 2])", section_start)
    activity_guide_header = content[section_start:section_end]

    assert "result.activity_guide.title" not in activity_guide_header
    assert "get_activity_branch_label(result.activity_feasibility.branch)" not in activity_guide_header


def test_guidance_pair_uses_top_separator_instead_of_middle_divider() -> None:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    content = main_py.read_text(encoding="utf-8")

    block_start = content.index(".guidance-pair {")
    block_end = content.index("      .guidance-panel {", block_start)
    guidance_pair_block = content[block_start:block_end]

    assert "border-top:" in guidance_pair_block
    assert "padding-top:" in guidance_pair_block

    divider_start = content.index(".guidance-panel-divider {")
    divider_end = content.index("      .creative-guide {", divider_start)
    divider_block = content[divider_start:divider_end]

    assert "border-left:" not in divider_block


def test_submit_flow_wires_progress_callback_into_workflow_run() -> None:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    content = main_py.read_text(encoding="utf-8")

    assert 'progress_status_placeholder = st.empty()' in content
    assert (
        'progress_status_placeholder.markdown(' in content
    )
    assert (
        'build_loading_status_html(get_workflow_progress_message("ensure_child_profile"))'
        in content
    )
    assert 'def update_progress_status(_node_name: str, message: str) -> None:' in content
    assert "build_loading_status_html(message)" in content
    assert "progress_callback=update_progress_status" in content
    assert 'st.spinner("왜용이 답을 준비하고 있어요...")' not in content


def test_loading_status_styles_define_inline_spinner() -> None:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    content = main_py.read_text(encoding="utf-8")

    assert ".loading-status {" in content
    assert ".loading-status-spinner {" in content
    assert "@keyframes loading-status-spin {" in content


def test_result_view_does_not_show_saved_record_success_banner() -> None:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    content = main_py.read_text(encoding="utf-8")

    assert "학습 기록이 저장되었습니다." not in content
    assert "st.success(" not in content


def test_main_form_does_not_render_optional_context_note_field() -> None:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    content = main_py.read_text(encoding="utf-8")

    assert "오늘 상황 메모 (선택)" not in content
    assert "child_reaction_note" not in content


def test_guidance_pair_has_bottom_spacing() -> None:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    content = main_py.read_text(encoding="utf-8")

    block_start = content.index(".guidance-pair {")
    block_end = content.index("      .guidance-panel {", block_start)
    guidance_pair_block = content[block_start:block_end]

    assert "margin-bottom:" in guidance_pair_block
