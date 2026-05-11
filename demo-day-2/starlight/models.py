"""Pydantic models for 별빛탐구 agent state and IO."""

from __future__ import annotations

from typing import List, NotRequired, TypedDict

from pydantic import BaseModel, Field


class ObservationInput(BaseModel):
    """User observation context (MVP required fields)."""

    date: str = Field(description="관측 날짜 YYYY-MM-DD")
    time: str = Field(description="관측 시간 HH:MM (24h)")
    latitude: float = Field(description="위도")
    longitude: float = Field(description="경도")


class WeatherCondition(BaseModel):
    cloud_cover: float = Field(description="구름량 0-100%")
    precipitation: float = Field(description="강수량 mm 또는 강수 확률")
    visibility: str = Field(description="시정 상태")
    temperature: float = Field(description="기온 °C")
    observation_score: int = Field(ge=0, le=100, description="관측 적합도 0-100")


class SkyObject(BaseModel):
    name: str = Field(description="천체 또는 별자리 이름")
    object_type: str = Field(description="천체 유형")
    direction: str = Field(description="관측 방향")
    difficulty: str = Field(description="관측 난이도")
    learning_concept: str = Field(default="", description="연결 학습 개념")


class LearningContent(BaseModel):
    object_name: str = Field(description="관측 대상 이름")
    title: str = Field(description="학습 콘텐츠 제목")
    concept: str = Field(description="핵심 개념")
    explanation: str = Field(description="학습 설명")
    key_terms: List[str] = Field(default_factory=list, description="핵심 용어")


class Quiz(BaseModel):
    question: str = Field(description="객관식 문제")
    choices: List[str] = Field(description="선택지")
    answer: int = Field(description="정답 번호 1-based index")
    explanation: str = Field(description="정답 해설")


class LearningLogEntry(BaseModel):
    """Persisted learning session summary."""

    date: str
    time: str
    latitude: float
    longitude: float
    observation_status: str
    object_names: List[str]
    quiz_count: int


class State(TypedDict):
    """LangGraph shared state."""

    observation_input: NotRequired[ObservationInput]
    weather_condition: NotRequired[WeatherCondition | None]
    weather_note: NotRequired[str]
    observation_status: NotRequired[str]
    indoor_mode: NotRequired[bool]
    visible_objects: NotRequired[List[SkyObject]]
    learning_contents: NotRequired[List[LearningContent]]
    quizzes: NotRequired[List[Quiz]]
    pipeline_error: NotRequired[str]
    final_answer: NotRequired[str]
