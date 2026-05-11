"""LangGraph node functions for 별빛탐구."""

from __future__ import annotations

import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from starlight.models import LearningContent, LearningLogEntry, ObservationInput, Quiz, SkyObject, State, WeatherCondition
from starlight.tools.learning_log import append_learning_log
from starlight.tools.visible_sky import list_visible_objects
from starlight.tools.weather import WeatherUnavailableError, fetch_weather

logger = logging.getLogger(__name__)

SkyMode = str  # "good" | "moderate" | "indoor"


def _classify_weather(w: WeatherCondition) -> tuple[str, bool, SkyMode]:
    """Return (status label, indoor_learning_mode, sky_list_mode)."""
    precip = w.precipitation
    cloud = w.cloud_cover
    if precip > 0 or cloud >= 70.0:
        return "관측 어려움 (실내 학습 모드)", True, "indoor"
    if cloud <= 30.0:
        return "관측 가능", False, "good"
    return "관측 보통 (밝은 천체 위주)", False, "moderate"


def _merge_pipeline_error(state: State, message: str) -> str:
    prev = (state.get("pipeline_error") or "").strip()
    return f"{prev}\n{message}".strip() if prev else message


def check_weather_node(state: State) -> dict:
    inp = state["observation_input"]
    assert isinstance(inp, ObservationInput)
    try:
        weather, note = fetch_weather(inp.date, inp.time, inp.latitude, inp.longitude)
        return {"weather_condition": weather, "weather_note": note}
    except WeatherUnavailableError as e:
        return {
            "weather_condition": None,
            "weather_note": "",
            "pipeline_error": _merge_pipeline_error(state, str(e)),
        }


def evaluate_observation_node(state: State) -> dict:
    w = state.get("weather_condition")
    if w is None:
        return {
            "observation_status": "날씨 정보 없음 (실측 분기 생략)",
            "indoor_mode": False,
        }
    status, indoor_mode, _sky = _classify_weather(w)
    return {"observation_status": status, "indoor_mode": indoor_mode}


def evaluate_observation_mode(state: State) -> SkyMode:
    """Return visibility mode for sky tool."""
    w = state.get("weather_condition")
    if w is None:
        return "good"
    return _classify_weather(w)[2]


def list_visible_objects_node(state: State) -> dict:
    inp = state["observation_input"]
    assert isinstance(inp, ObservationInput)
    mode = evaluate_observation_mode(state)
    objs = list_visible_objects(inp.date, inp.time, inp.latitude, inp.longitude, mode)
    return {"visible_objects": objs}


class _LearningBatch(BaseModel):
    contents: list[LearningContent] = Field(description="각 관측 대상별 학습 콘텐츠")


class _QuizBatch(BaseModel):
    quizzes: list[Quiz] = Field(description="학습 콘텐츠와 대응되는 객관식 퀴즈")


def generate_learning_content_node(state: State) -> dict:
    objs = state.get("visible_objects") or []
    if not objs:
        return {"learning_contents": []}
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {
            "learning_contents": [],
            "pipeline_error": _merge_pipeline_error(state, "OPENAI_API_KEY가 필요합니다."),
        }

    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0.3)
    structured = llm.with_structured_output(_LearningBatch)
    lines = "\n".join(
        f"- {o.name} ({o.object_type}): 방향 {o.direction}, 난이도 {o.difficulty}"
        for o in objs
    )
    sys = SystemMessage(
        content=(
            "당신은 초보자를 위한 한국어 천문 교육가입니다. "
            "각 천체/별자리마다 짧고 정확한 학습 설명을 작성합니다. "
            "별자리는 실제 물리적 근접이 아니라 시각적 패턴임을 필요 시 설명합니다. "
            "각 항목의 concept 필드에 핵심 과학 개념을 한 줄로 요약하세요."
        )
    )
    human = HumanMessage(
        content=(
            "다음 관측 대상들에 대해 LearningContent 리스트를 생성하세요(대상 개수와 동일하게). "
            "title은 한 줄, explanation은 3~5문장, key_terms는 3~5개.\n\n" + lines
        )
    )
    try:
        batch = structured.invoke([sys, human])
        contents = batch.contents
        if len(contents) != len(objs):
            by_name = {c.object_name: c for c in contents}
            missing = [o.name for o in objs if o.name not in by_name]
            return {
                "learning_contents": [],
                "pipeline_error": _merge_pipeline_error(
                    state,
                    f"학습 콘텐츠 개수 불일치 또는 누락: {missing}",
                ),
            }
        return {"learning_contents": contents}
    except Exception as e:
        logger.warning("LLM learning content failed: %s", e)
        return {
            "learning_contents": [],
            "pipeline_error": _merge_pipeline_error(state, f"학습 콘텐츠 생성 실패: {e}"),
        }


def generate_quiz_node(state: State) -> dict:
    contents = state.get("learning_contents") or []
    if not contents:
        return {"quizzes": []}
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {
            "quizzes": [],
            "pipeline_error": _merge_pipeline_error(state, "OPENAI_API_KEY가 필요합니다."),
        }

    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0.2)
    structured = llm.with_structured_output(_QuizBatch)
    text = "\n\n".join(
        f"[{c.object_name}] {c.title}\n개념: {c.concept}\n설명: {c.explanation}\n용어: {', '.join(c.key_terms)}"
        for c in contents
    )
    sys = SystemMessage(
        content=(
            "당신은 한국어 객관식 출제자입니다. 각 학습 블록마다 정확히 1문제씩 만듭니다. "
            "choices는 정확히 4개이고, answer는 정답 선택지의 번호(1~4)입니다. "
            "반드시 choices[answer-1]의 내용이 explanation과 논리적으로 일치해야 하며, 정답과 해설이 서로 모순되면 안 됩니다."
        )
    )
    human = HumanMessage(
        content="아래 학습 내용만 근거로 퀴즈를 만들 것.\n\n" + text
    )
    try:
        batch = structured.invoke([sys, human])
        quizzes = batch.quizzes
        if len(quizzes) != len(contents):
            return {
                "quizzes": [],
                "pipeline_error": _merge_pipeline_error(
                    state, "퀴즈 개수가 학습 블록과 일치하지 않습니다."
                ),
            }
        for q in quizzes:
            if len(q.choices) != 4 or not (1 <= q.answer <= 4):
                return {
                    "quizzes": [],
                    "pipeline_error": _merge_pipeline_error(
                        state, "퀴즈 형식이 올바르지 않습니다(4지선다·정답 1~4)."
                    ),
                }
        return {"quizzes": quizzes}
    except Exception as e:
        logger.warning("LLM quiz failed: %s", e)
        return {
            "quizzes": [],
            "pipeline_error": _merge_pipeline_error(state, f"퀴즈 생성 실패: {e}"),
        }


def build_final_answer_node(state: State) -> dict:
    inp = state["observation_input"]
    assert isinstance(inp, ObservationInput)
    w = state.get("weather_condition")
    status = state.get("observation_status", "")
    indoor = state.get("indoor_mode", False)
    objs = state.get("visible_objects") or []
    contents = state.get("learning_contents") or []
    quizzes = state.get("quizzes") or []
    weather_note = state.get("weather_note", "")

    lines: list[str] = []
    lines.append("## 입력 정보")
    lines.append(f"- 날짜: {inp.date}")
    lines.append(f"- 시간: {inp.time}")
    lines.append(f"- 위도: {inp.latitude}")
    lines.append(f"- 경도: {inp.longitude}")
    lines.append("")
    lines.append("## 관측 조건")
    lines.append(f"- 상태: {status}")
    if w is not None:
        lines.append(
            f"- 구름: {w.cloud_cover:.0f}%, 강수: {w.precipitation:.1f}, 시정: {w.visibility}, 기온: {w.temperature:.1f}°C"
        )
        lines.append(f"- 관측 적합도 점수: {w.observation_score}/100 ({weather_note})")
    else:
        lines.append("- 날씨: OpenWeather를 사용하지 못했습니다. 천체 목록은 날씨 분기 없이 기본(`good`) 추천으로 구성했습니다.")
    if indoor:
        lines.append(
            "- 안내: 기상 조건이 까다로워 실제 관측 대신 개념 학습 중심으로 구성했습니다. 다음 맑은 밤을 추천합니다."
        )
    pe = state.get("pipeline_error")
    if pe:
        lines.append("")
        lines.append("## 생성 오류")
        lines.append(pe.strip())
    lines.append("")
    lines.append("## 오늘의 관측·학습 대상")
    for i, o in enumerate(objs, start=1):
        lines.append(f"{i}. **{o.name}**")
        lines.append(f"   - 유형: {o.object_type}")
        lines.append(f"   - 방향(참고): {o.direction}")
        lines.append(f"   - 관측 난이도: {o.difficulty}")
        if o.learning_concept:
            lines.append(f"   - 학습 개념(참고): {o.learning_concept}")
        lines.append("")
    lines.append("## 학습 설명")
    for c in contents:
        lines.append(f"### {c.object_name} — {c.title}")
        lines.append(f"- 핵심 개념: {c.concept}")
        lines.append(f"- 설명: {c.explanation}")
        if c.key_terms:
            lines.append(f"- 핵심 용어: {', '.join(c.key_terms)}")
        lines.append("")
    lines.append("## 객관식 퀴즈")
    for i, q in enumerate(quizzes, start=1):
        lines.append(f"**Q{i}.** {q.question}")
        for j, ch in enumerate(q.choices, start=1):
            lines.append(f"{j}. {ch}")
        lines.append(f"- 정답: {q.answer}")
        lines.append(f"- 해설: {q.explanation}")
        lines.append("")
    return {"final_answer": "\n".join(lines).strip()}


def save_learning_log_node(state: State) -> dict:
    inp = state.get("observation_input")
    if not isinstance(inp, ObservationInput):
        return {}
    objs = state.get("visible_objects") or []
    quizzes = state.get("quizzes") or []
    entry = LearningLogEntry(
        date=inp.date,
        time=inp.time,
        latitude=inp.latitude,
        longitude=inp.longitude,
        observation_status=state.get("observation_status", ""),
        object_names=[o.name for o in objs],
        quiz_count=len(quizzes),
    )
    try:
        path = append_learning_log(entry)
        logger.info("Learning log saved to %s", path)
    except OSError as e:
        logger.warning("Could not save learning log: %s", e)
    return {}
