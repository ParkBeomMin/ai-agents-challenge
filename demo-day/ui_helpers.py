from __future__ import annotations

import re
from html import escape


def get_parent_coach_tab_labels() -> tuple[str, str, str, str]:
    return ("짧은 답", "긴 답", "대화 스크립트", "대화 확장")


def get_long_answer_card_title() -> str:
    return "이어서 이렇게 이야기해보세요"


def format_multiline_markdown(text: str) -> str:
    lines = (text or "").splitlines()
    formatted_lines: list[str] = []

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            next_is_content = False
            if index + 1 < len(lines):
                next_is_content = bool(lines[index + 1].strip())
            formatted_lines.append(f"{stripped}  " if next_is_content else stripped)
        elif formatted_lines and formatted_lines[-1] != "":
            formatted_lines.append("")

    return "\n".join(formatted_lines).strip()


def parse_script_turns(script: str) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    for line in (script or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" in stripped:
            speaker, text = stripped.split(":", 1)
            speaker = speaker.strip() or "안내"
            text = text.strip()
            if text:
                turns.append({"speaker": speaker, "text": text})
            continue
        turns.append({"speaker": "안내", "text": stripped})
    return turns


def build_short_answer_card_html(title: str, body: str) -> str:
    return (
        '<div class="answer-card">'
        f'<div class="answer-card-title">{escape(title)}</div>'
        f'<div class="answer-card-body">{escape(body)}</div>'
        "</div>"
    )


def build_script_bubbles_html(script: str) -> str:
    parts = ['<div class="script-bubbles">']
    for turn in parse_script_turns(script):
        speaker = turn["speaker"]
        role = "parent" if speaker == "부모" else "child" if speaker == "아이" else "guide"
        parts.append(
            '<div class="script-row">'
            f'<div class="script-bubble {role}">'
            f'<div class="script-speaker">{escape(speaker)}</div>'
            f'<div class="script-text">{escape(turn["text"])}</div>'
            "</div>"
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def build_script_stack_html(script: str) -> str:
    parts = ['<div class="script-stack">']
    for turn in parse_script_turns(script):
        speaker = turn["speaker"]
        role = "parent" if speaker == "부모" else "child" if speaker == "아이" else "guide"
        parts.append(
            '<div class="script-stack-item">'
            f'<div class="script-bubble {role}">'
            f'<div class="script-speaker">{escape(speaker)}</div>'
            f'<div class="script-text">{escape(turn["text"])}</div>'
            "</div>"
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def build_script_lines_html(script: str) -> str:
    parts = ['<div class="script-lines">']
    for turn in parse_script_turns(script):
        parts.append(
            '<div class="script-entry">'
            f'<div class="script-entry-speaker">{escape(turn["speaker"])}</div>'
            f'<div class="script-entry-text">{escape(turn["text"])}</div>'
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def split_paragraphs(text: str) -> list[str]:
    return [part.strip() for part in (text or "").split("\n\n") if part.strip()]


def split_long_answer_paragraphs(text: str) -> list[str]:
    normalized = (text or "").strip()
    if not normalized:
        return []

    explicit_paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    if len(explicit_paragraphs) > 1:
        return explicit_paragraphs

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
    if len(sentences) < 3:
        return [normalized]

    paragraphs: list[str] = []
    for index in range(0, len(sentences), 2):
        paragraphs.append(" ".join(sentences[index : index + 2]))
    return paragraphs


def build_paragraph_cards_html(title: str, body: str) -> str:
    parts = ['<div class="paragraph-cards">']
    for index, paragraph in enumerate(split_paragraphs(body), start=1):
        parts.append(
            '<div class="paragraph-card">'
            f'<div class="paragraph-card-title">{escape(title)} {index}</div>'
            f'<div class="paragraph-card-body">{escape(paragraph)}</div>'
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def build_long_answer_block_html(title: str, body: str) -> str:
    paragraphs = split_long_answer_paragraphs(body) or [""]
    paragraph_html = "".join(
        f'<p class="long-answer-paragraph">{escape(paragraph)}</p>'
        for paragraph in paragraphs
    )
    return (
        '<div class="long-answer-block">'
        f'<div class="long-answer-title">{escape(title)}</div>'
        f'<div class="long-answer-body">{paragraph_html}</div>'
        "</div>"
    )


def build_question_chips_html(questions: list[str]) -> str:
    normalized_questions = [question.strip() for question in questions if question and question.strip()]
    if not normalized_questions:
        return ""

    parts = ['<div class="question-chips">']
    for question in normalized_questions:
        parts.append(f'<div class="question-chip">{escape(question)}</div>')
    parts.append("</div>")
    return "".join(parts)


def build_material_list_html(materials: list[str]) -> str:
    parts = ['<div class="material-list">']
    for material in materials:
        parts.append(
            '<div class="material-item">'
            '<span class="material-dot"></span>'
            f'<span class="material-text">{escape(material)}</span>'
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def build_activity_steps_html(steps: list[str]) -> str:
    normalized_steps = [step.strip() for step in steps if step and step.strip()]
    if not normalized_steps:
        return ""

    parts = ['<div class="activity-steps">']
    for index, step in enumerate(normalized_steps, start=1):
        parts.append(
            '<div class="activity-step-item">'
            f'<div class="activity-step-number">{index}</div>'
            f'<div class="activity-step-text">{escape(step)}</div>'
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def build_guidance_card_html(title: str, body: str, tone: str = "neutral") -> str:
    tone_class = tone.strip() if tone.strip() else "neutral"
    return (
        f'<div class="guidance-card {escape(tone_class)}">'
        f'<div class="guidance-card-title">{escape(title)}</div>'
        f'<div class="guidance-card-body">{escape(body)}</div>'
        "</div>"
    )


def build_guidance_pair_html(avoid_body: str, instead_body: str) -> str:
    return (
        '<div class="guidance-pair">'
        '<div class="guidance-panel">'
        f'{build_guidance_card_html("피하면 좋은 말", avoid_body, "avoid")}'
        "</div>"
        '<div class="guidance-panel guidance-panel-divider">'
        f'{build_guidance_card_html("대신 이렇게 말해보세요", instead_body, "instead")}'
        "</div>"
        "</div>"
    )


def build_creative_question_guide_html(
    observation: str,
    imagination: str,
    comparison: str,
    inquiry: str,
) -> str:
    guide_items = [
        ("관찰", observation),
        ("상상", imagination),
        ("비교", comparison),
        ("탐구", inquiry),
    ]
    parts = ['<div class="creative-guide">']
    for label, text in guide_items:
        parts.append(
            '<div class="creative-guide-item">'
            f'<div class="creative-guide-label">{escape(label)}</div>'
            f'<div class="creative-guide-text">{escape(text)}</div>'
            "</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def build_history_button_label(category: str, question: str) -> str:
    category_text = (category or "미분류").strip() or "미분류"
    question_text = (question or "").strip()
    return f"{category_text} · {question_text}"


def build_history_button_text(category: str, question: str, created_date: str) -> str:
    category_text = (category or "미분류").strip() or "미분류"
    question_text = (question or "").strip()
    date_text = (created_date or "").strip()
    return f"`{category_text}`\n**{question_text}**\n{date_text}"


def resolve_selected_record_id(
    available_ids: list[int],
    current_selected_id: int | None,
    clicked_record_id: int | None = None,
) -> int | None:
    if clicked_record_id in available_ids:
        return clicked_record_id
    if current_selected_id in available_ids:
        return current_selected_id
    return available_ids[0] if available_ids else None


def resolve_active_result_source(
    preferred_source: str | None,
    latest_result: dict | None,
    selected_record_result: str,
) -> str | None:
    if preferred_source == "latest" and latest_result:
        return "latest"
    if preferred_source == "history" and selected_record_result:
        return "history"
    if latest_result:
        return "latest"
    if selected_record_result:
        return "history"
    return None


def build_summary_card_html(label: str, value: str, caption: str) -> str:
    return (
        '<div class="summary-card">'
        f'<div class="summary-card-label">{escape(label)}</div>'
        f'<div class="summary-card-value">{escape(value)}</div>'
        f'<div class="summary-card-caption">{escape(caption)}</div>'
        "</div>"
    )


def build_history_card_html(title: str, meta: str, active: bool = False) -> str:
    active_class = " active" if active else ""
    return (
        f'<div class="history-card{active_class}">'
        f'<div class="history-card-title">{escape(title)}</div>'
        f'<div class="history-card-meta">{escape(meta)}</div>'
        "</div>"
    )
