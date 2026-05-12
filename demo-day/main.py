from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import streamlit as st

from ui_helpers import (
    build_activity_steps_html,
    build_creative_question_guide_html,
    build_guidance_pair_html,
    build_material_list_html,
    build_loading_status_html,
    build_history_button_text,
    build_long_answer_block_html,
    build_question_chips_html,
    build_script_stack_html,
    build_summary_card_html,
    build_short_answer_card_html,
    format_multiline_markdown,
    get_long_answer_card_title,
    get_parent_coach_tab_labels,
    resolve_active_result_source,
    resolve_selected_record_id,
)
from waeyong_core import (
    DEFAULT_DB_PATH,
    DEFAULT_IMAGE_DIR,
    CuriosityRequest,
    CuriosityResult,
    LearningRepository,
    build_workflow,
    get_activity_branch_label,
    get_workflow_progress_message,
)


st.set_page_config(
    page_title="왜용",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .summary-card {
        background: #ffffff;
        border: 1px solid #e7edf5;
        border-radius: 18px;
        padding: 16px 18px;
        min-height: 120px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
      }
      .summary-card-label {
        font-size: 0.84rem;
        color: #5d6b82;
        font-weight: 700;
        margin-bottom: 8px;
      }
      .summary-card-value {
        font-size: 1.18rem;
        font-weight: 700;
        color: #243247;
        margin-bottom: 8px;
      }
      .summary-card-caption {
        font-size: 0.95rem;
        color: #4c5668;
        line-height: 1.6;
      }
      .answer-card {
        background: linear-gradient(180deg, #fff9e8 0%, #fffef7 100%);
        border: 1px solid rgba(222, 184, 135, 0.45);
        border-radius: 18px;
        padding: 18px 20px;
        margin-bottom: 10px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
      }
      .answer-card-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #8a5a00;
        margin-bottom: 8px;
      }
      .answer-card-body {
        font-size: 1.1rem;
        line-height: 1.75;
        color: #2f2f2f;
        white-space: pre-wrap;
      }
      .section-panel {
        border: 1px solid #e7edf5;
        border-radius: 20px;
        padding: 18px 18px 10px 18px;
        margin: 10px 0 18px 0;
        background: #ffffff;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
      }
      .parent-coach-spacer {
        height: 10px;
      }
      .result-section-gap {
        height: 18px;
      }
      .activity-guide-footer-gap {
        height: 14px;
      }
      .long-answer-block {
        background: #f8fbff;
        border: 1px solid #d7e6f7;
        border-radius: 16px;
        padding: 16px 18px;
        margin-bottom: 10px;
      }
      .long-answer-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #416487;
        margin-bottom: 8px;
      }
      .long-answer-body {
        line-height: 1.82;
        color: #2c3a4f;
      }
      .long-answer-paragraph {
        margin: 0 0 12px 0;
      }
      .long-answer-paragraph:last-child {
        margin-bottom: 0;
      }
      .script-stack {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .script-stack-item {
        display: block;
      }
      .script-bubble {
        border-radius: 18px;
        padding: 14px 16px;
        border: 1px solid #dfe8f3;
        background: #f8fbff;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
      }
      .script-bubble.parent {
        background: #fff8eb;
        border-color: #f1dfb5;
      }
      .script-bubble.child {
        background: #eef6ff;
        border-color: #d4e4f8;
      }
      .script-bubble.guide {
        background: #f7f8fc;
        border-color: #e1e5ef;
      }
      .script-speaker {
        font-size: 0.82rem;
        font-weight: 700;
        color: #456284;
        margin-bottom: 6px;
      }
      .script-text {
        font-size: 1rem;
        line-height: 1.75;
        white-space: pre-wrap;
      }
      .question-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 8px 0 6px 0;
      }
      .question-chip {
        background: #f2f7ff;
        border: 1px solid #cfdef2;
        border-radius: 999px;
        padding: 10px 14px;
        font-size: 0.95rem;
        line-height: 1.4;
      }
      .material-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-top: 8px;
      }
      .material-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        background: #f8fbff;
        border: 1px solid #d7e6f7;
        border-radius: 14px;
      }
      .material-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: #7ba7d9;
        flex-shrink: 0;
      }
      .material-text {
        color: #2c3a4f;
        line-height: 1.5;
        font-size: 0.96rem;
      }
      .activity-steps {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 8px;
      }
      .activity-step-item {
        display: grid;
        grid-template-columns: 34px minmax(0, 1fr);
        gap: 12px;
        align-items: flex-start;
        padding: 12px 14px;
        background: #fbfcff;
        border: 1px solid #dce7f4;
        border-radius: 16px;
      }
      .activity-step-number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 999px;
        background: #eaf2ff;
        color: #476486;
        font-size: 0.92rem;
        font-weight: 800;
        flex-shrink: 0;
      }
      .activity-step-text {
        color: #2c3a4f;
        line-height: 1.65;
        font-size: 0.97rem;
      }
      .guidance-card {
        padding: 14px 16px;
        border-radius: 16px;
        border: 1px solid #dfe7f2;
        background: #fbfcff;
        min-height: 100%;
      }
      .guidance-card.avoid {
        background: #fff8f6;
        border-color: #f0ddd8;
      }
      .guidance-card.instead {
        background: #f7fbff;
        border-color: #d8e6f5;
      }
      .guidance-card-title {
        font-size: 0.92rem;
        font-weight: 800;
        margin-bottom: 10px;
        color: #2b3a4d;
      }
      .guidance-card-body {
        color: #435264;
        line-height: 1.7;
        white-space: pre-wrap;
      }
      .guidance-pair {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
        margin-top: 18px;
        margin-bottom: 10px;
        padding-top: 18px;
        border-top: 1px solid #e4ebf3;
        align-items: stretch;
      }
      .guidance-panel {
        min-width: 0;
      }
      .guidance-panel-divider {
        padding-left: 0;
      }
      .creative-guide {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
        margin: 14px 0 10px 0;
      }
      .creative-guide-item {
        padding: 16px 18px;
        background: linear-gradient(180deg, #fcfdff 0%, #f5f9ff 100%);
        border: 1px solid #d9e6f5;
        border-radius: 16px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
      }
      .creative-guide-label {
        display: inline-block;
        margin-bottom: 8px;
        padding: 4px 10px;
        border-radius: 999px;
        background: #eaf2ff;
        color: #476486;
        font-size: 0.82rem;
        font-weight: 700;
      }
      .creative-guide-text {
        color: #2c3a4f;
        line-height: 1.7;
        white-space: pre-wrap;
      }
      .loading-status {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 12px 0;
        padding: 12px 14px;
        border-radius: 14px;
        background: #f4f8fe;
        border: 1px solid #d9e5f3;
        color: #314155;
      }
      .loading-status-spinner {
        width: 16px;
        height: 16px;
        border-radius: 999px;
        border: 2px solid #c7d8ee;
        border-top-color: #4f7db3;
        flex-shrink: 0;
        animation: loading-status-spin 0.85s linear infinite;
      }
      .loading-status-text {
        font-size: 0.95rem;
        line-height: 1.5;
        font-weight: 600;
      }
      @keyframes loading-status-spin {
        from {
          transform: rotate(0deg);
        }
        to {
          transform: rotate(360deg);
        }
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] {
        margin-bottom: 10px;
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        min-height: 82px;
        border-radius: 16px;
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        text-align: left;
        white-space: normal;
        padding: 12px 14px;
        background: #fafcff;
        border: 1px solid #e2eaf4;
        box-shadow: none;
        color: #314155;
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        background: #f6f9fd;
        border-color: #d5e0ee;
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
        background: #eef4fb;
        border: 1px solid #cfdbeb;
        color: #243247;
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button > div {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: flex-start;
        width: 100%;
        text-align: left;
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] > button p {
        white-space: pre-wrap;
        text-align: left;
        line-height: 1.42;
        font-size: 0.92rem;
        margin: 0;
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] code {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 999px;
        background: #f2f6fb;
        border: 1px solid #dde6f0;
        color: #5b6e84;
        font-size: 0.74rem;
        font-weight: 700;
      }
      section[data-testid="stSidebar"] div[data-testid="stButton"] strong {
        display: block;
        margin: 7px 0 5px 0;
        color: #243247;
        font-size: 0.96rem;
        line-height: 1.38;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_workflow():
    return build_workflow(db_path=DEFAULT_DB_PATH, image_dir=DEFAULT_IMAGE_DIR)


@st.cache_resource
def get_repo() -> LearningRepository:
    return LearningRepository(DEFAULT_DB_PATH)


def render_history_sidebar(repo: LearningRepository, learner_id: str) -> None:
    st.sidebar.markdown("## 학습 기록")
    categories = repo.list_question_categories(learner_id)
    category_options = ["전체"] + [name for name, _ in categories]
    selected_category = st.sidebar.selectbox("카테고리", category_options)

    selected_category_value = None if selected_category == "전체" else selected_category
    records = repo.fetch_learning_records(
        learner_id=learner_id,
        category=selected_category_value,
        limit=20,
    )

    if categories:
        st.sidebar.caption("카테고리별 누적 질문 수")
        for category_name, count in categories:
            st.sidebar.write(f"- `{category_name}`: {count}")
    else:
        st.sidebar.caption("저장된 카테고리 기록이 아직 없습니다.")

    if not records:
        st.sidebar.info("표시할 학습 기록이 없습니다.")
        st.session_state["selected_record"] = None
        st.session_state["selected_record_detail"] = None
        st.session_state["selected_record_result"] = ""
        return

    available_ids = [record["id"] for record in records]
    selected_record_id = resolve_selected_record_id(
        available_ids=available_ids,
        current_selected_id=st.session_state.get("selected_record_id"),
    )

    st.sidebar.markdown("### 최근 기록")
    for record in records:
        record_id = record["id"]
        if st.sidebar.button(
            build_history_button_text(
                category=record["question_category"],
                question=record["question"],
                created_date=record["created_at"][:10],
            ),
            key=f"history-record-{record_id}",
            use_container_width=True,
            type="primary" if record_id == selected_record_id else "secondary",
        ):
            st.session_state["selected_record_id"] = resolve_selected_record_id(
                available_ids=available_ids,
                current_selected_id=selected_record_id,
                clicked_record_id=record_id,
            )
            st.session_state["active_result_source"] = "history"
            st.rerun()

    selected_record_id = resolve_selected_record_id(
        available_ids=available_ids,
        current_selected_id=st.session_state.get("selected_record_id"),
    )

    st.session_state["selected_record_id"] = selected_record_id
    st.session_state["selected_record"] = next(
        record for record in records if record["id"] == selected_record_id
    )
    detail = repo.fetch_learning_record_detail(selected_record_id)
    st.session_state["selected_record_detail"] = detail
    payload = (detail or {}).get("result_payload") or ""
    st.session_state["selected_record_result"] = payload


def render_result(result: CuriosityResult) -> None:
    st.markdown("## 결과")

    analysis_col, subject_col, branch_col = st.columns(3)
    with analysis_col:
        st.markdown(
            build_summary_card_html(
                "질문 유형",
                result.question_analysis.question_type,
                result.question_analysis.child_intent,
            ),
            unsafe_allow_html=True,
        )
    with subject_col:
        st.markdown(
            build_summary_card_html(
                "학습 주제",
                result.study_subject.title,
                result.study_subject.core_concept,
            ),
            unsafe_allow_html=True,
        )
    with branch_col:
        st.markdown(
            build_summary_card_html(
                "활동 분기",
                get_activity_branch_label(result.activity_feasibility.branch),
                result.activity_feasibility.reason,
            ),
            unsafe_allow_html=True,
        )

    if result.prior_learning_notes:
        with st.expander("이전 학습 연결 보기"):
            st.text(result.prior_learning_notes)

    st.markdown('<div class="result-section-gap"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### 부모 코치 패키지")
        st.markdown('<div class="parent-coach-spacer"></div>', unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(list(get_parent_coach_tab_labels()))

        with tab1:
            st.markdown(
                build_short_answer_card_html("바로 이렇게 말해보세요", result.coach_pack.short_answer_30s),
                unsafe_allow_html=True,
            )
            st.caption(result.coach_pack.play_and_picture_tip)

        with tab2:
            st.markdown(
                build_long_answer_block_html(
                    get_long_answer_card_title(),
                    result.coach_pack.story_answer_3min,
                ),
                unsafe_allow_html=True,
            )

        with tab3:
            st.markdown(
                build_script_stack_html(result.coach_pack.parent_read_aloud_script),
                unsafe_allow_html=True,
            )
            st.markdown(
                build_guidance_pair_html(
                    avoid_body=result.coach_pack.phrases_to_avoid,
                    instead_body=result.coach_pack.say_instead,
                ),
                unsafe_allow_html=True,
            )

        with tab4:
            st.markdown("#### 되물음 3개")
            st.markdown(
                build_question_chips_html(result.coach_pack.follow_up_questions),
                unsafe_allow_html=True,
            )

            guide = result.coach_pack.creative_question_guide
            st.markdown("#### 창의 질문 가이드")
            st.markdown(
                build_creative_question_guide_html(
                    observation=guide.observation,
                    imagination=guide.imagination,
                    comparison=guide.comparison,
                    inquiry=guide.inquiry,
                ),
                unsafe_allow_html=True,
            )

    with st.container(border=True):
        st.markdown("### 활동 가이드")
        materials_col, steps_col = st.columns([1, 2])
        with materials_col:
            st.markdown("#### 준비물")
            st.markdown(
                build_material_list_html(result.activity_guide.materials),
                unsafe_allow_html=True,
            )
        with steps_col:
            st.markdown("#### 방법")
            st.markdown(
                build_activity_steps_html(result.activity_guide.steps),
                unsafe_allow_html=True,
            )
        st.markdown('<div class="activity-guide-footer-gap"></div>', unsafe_allow_html=True)
        st.info(result.activity_guide.safety_note)

    with st.container(border=True):
        st.markdown("### 이미지 카드")
        if result.image_need.need_image and result.image_card_url:
            image_path = Path(result.image_card_url)
            if image_path.exists():
                st.image(str(image_path), caption=image_path.name, use_container_width=True)
            else:
                st.warning("이미지 생성이 요청되었지만 파일을 찾지 못했습니다.")
            with st.expander("이미지 프롬프트 보기"):
                st.code(result.image_card_prompt_en)
        elif result.image_need.need_image:
            st.warning(
                "이미지 카드가 필요하다고 판단되었지만, 생성에 실패했거나 파일을 저장하지 못했습니다."
            )
        else:
            st.caption(f"이미지 생략: {result.image_need.reason}")

    related_question_chips = build_question_chips_html(result.related_question_suggestions)
    if related_question_chips:
        with st.container(border=True):
            st.markdown("### 다음 호기심 주제")
            st.markdown(
                related_question_chips,
                unsafe_allow_html=True,
            )

def main() -> None:
    st.title("왜용")
    st.write(
        "아이의 질문을 부모와 아이가 함께 탐구하는 대화로 바꿔주는 "
        "호기심 학습 코치 MVP입니다."
    )

    repo = get_repo()

    with st.sidebar:
        st.markdown("## 아이 프로필")
        target_age = st.slider("만 나이", min_value=3, max_value=8, value=5)
        child_interests = st.text_input(
            "관심사",
            placeholder="예: 공룡, 자동차, 우주",
        )
        explanation_style = st.selectbox(
            "설명 스타일",
            options=["짧고 재밌게", "차분하고 친절하게", "호기심을 더 자극하게"],
        )
        learner_id = st.text_input(
            "learner_id",
            placeholder="같은 아이 기록을 묶고 싶을 때만 입력",
        )

    with st.form("waeyong_form", clear_on_submit=False):
        question = st.text_area(
            "아이 질문",
            height=120,
            placeholder="예: 비는 왜 내려요?",
        )
        submitted = st.form_submit_button("왜용?", use_container_width=True)

    loading_placeholder = st.empty()

    if submitted:
        if not question.strip():
            st.session_state.pop("latest_result", None)
            st.warning("아이 질문을 입력해 주세요.")
        else:
            request = CuriosityRequest(
                question=question.strip(),
                target_age=target_age,
                child_interests=child_interests,
                explanation_style=explanation_style,
                learner_id=learner_id,
            )
            try:
                with loading_placeholder.container():
                    progress_status_placeholder = st.empty()
                    progress_status_placeholder.markdown(
                        build_loading_status_html(get_workflow_progress_message("ensure_child_profile")),
                        unsafe_allow_html=True,
                    )

                    def update_progress_status(_node_name: str, message: str) -> None:
                        progress_status_placeholder.markdown(
                            build_loading_status_html(message),
                            unsafe_allow_html=True,
                        )

                    workflow = get_workflow()
                    result = workflow.run(
                        request,
                        thread_id=f"{learner_id or 'guest'}-{uuid4().hex[:8]}",
                        progress_callback=update_progress_status,
                    )
                loading_placeholder.empty()
                st.session_state["latest_result"] = result.model_dump()
                st.session_state["active_result_source"] = "latest"
            except Exception as exc:
                loading_placeholder.empty()
                st.session_state.pop("latest_result", None)
                message = str(exc)
                if "OPENAI_API_KEY" in message or "Missing credentials" in message:
                    st.error(
                        "OPENAI API 키를 찾지 못했습니다. `.env` 또는 셸 환경변수에 "
                        "`OPENAI_API_KEY`를 설정해 주세요."
                    )
                else:
                    st.error(f"왜용 실행 중 오류가 발생했습니다: {message}")

    render_history_sidebar(repo, learner_id)

    latest_result = st.session_state.get("latest_result")
    selected_record_result = st.session_state.get("selected_record_result")
    active_result_source = resolve_active_result_source(
        preferred_source=st.session_state.get("active_result_source"),
        latest_result=latest_result,
        selected_record_result=selected_record_result or "",
    )
    if active_result_source == "history":
        render_result(CuriosityResult.model_validate_json(selected_record_result))
    elif active_result_source == "latest":
        render_result(CuriosityResult.model_validate(latest_result))


if __name__ == "__main__":
    main()
