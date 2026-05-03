"""동화 본문과 세션 아티팩트를 합쳐 마크다운으로 반환."""

from __future__ import annotations

import base64
import json

from google.adk.tools.tool_context import ToolContext


def _artifact_to_data_url(part) -> str | None:
    if part is None:
        return None
    inline = getattr(part, "inline_data", None)
    if inline is None:
        return None
    data = getattr(inline, "data", None)
    if not data:
        return None
    mime = getattr(inline, "mime_type", None) or "image/jpeg"
    b64 = base64.standard_b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _pages_from_story(state: dict) -> list[dict]:
    sw = state.get("story_writer_agent_output")
    if not sw:
        return []
    pages = sw.get("pages")
    if not isinstance(pages, list):
        return []
    return sorted(pages, key=lambda p: p.get("page", 0))


async def build_finished_storybook_markdown(tool_context: ToolContext) -> str:
    """표지·1~5쪽 일러스트 아티팩트와 스토리 본문을 순서대로 묶은 마크다운을 만든다."""
    state = tool_context.state.to_dict()
    pages = _pages_from_story(state)
    sw = state.get("story_writer_agent_output") or {}
    title = sw.get("title") or "동화"

    lines: list[str] = [f"# {title}", ""]

    artifact_keys = await tool_context.list_artifacts()
    available = set(artifact_keys)

    cover_name = "cover_image.jpeg"
    if cover_name in available:
        part = await tool_context.load_artifact(cover_name)
        url = _artifact_to_data_url(part)
        if url:
            lines.append("## 표지")
            lines.append(f"![표지]({url})")
            lines.append("")
        else:
            lines.append("## 표지")
            lines.append("*(표지 이미지를 불러오지 못했습니다.)*")
            lines.append("")
    else:
        lines.append("## 표지")
        lines.append("*(표지 이미지 없음)*")
        lines.append("")

    missing: list[str] = []

    for page in pages:
        num = page.get("page")
        text = page.get("text") or ""
        if num is None:
            continue
        fn = f"scene_{int(num)}_image.jpeg"
        heading = f"{int(num)}쪽"

        lines.append(f"## {heading}")

        if fn in available:
            part = await tool_context.load_artifact(fn)
            url = _artifact_to_data_url(part)
            if url:
                lines.append(f"![장면 {num}]({url})")
                lines.append("")
            else:
                missing.append(fn)
                lines.append(f"*(이미지 로드 실패: {fn})*")
                lines.append("")
        else:
            missing.append(fn)
            lines.append(f"*(이미지 없음: {fn})*")
            lines.append("")

        lines.append(text)
        lines.append("")

    md = "\n".join(lines).strip() + "\n"

    payload = {
        "markdown": md,
        "missing_artifacts": missing,
        "artifact_keys": sorted(available),
    }
    return json.dumps(payload, ensure_ascii=False)