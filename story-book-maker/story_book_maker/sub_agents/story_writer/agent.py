from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import STORY_WRITER_DESCRIPTION, STORY_WRITER_INSTRUCTION
from pydantic import BaseModel, Field
from typing import List

class Character(BaseModel):
    name: str = Field(description="캐릭터 이름(스토리 전 페이지에서 동일하게 사용)")
    appearance: str = Field(description="외형 고정 설명(머리/색/옷/특징 등). 페이지/장면마다 바뀌지 않도록 잠금용으로 사용")

class StoryPage(BaseModel):
    page: int = Field(ge=1, le=5, description="페이지 번호(1~5)")
    text: str = Field(description="해당 페이지 본문 텍스트")
    visual: str = Field(description="일러스트를 위한 시각적 설명(구도/표정/배경/오브젝트/색감 포함)")

class StoryWriterOutput(BaseModel):
    title: str = Field(description="동화 제목")
    theme: str = Field(description="동화 테마(주제/교훈/분위기)")
    characters: List[Character] = Field(description="등장인물")
    pages: List[StoryPage] = Field(description="정확히 5페이지 구성의 페이지 배열")

MODEL = LiteLlm(model="openai/gpt-4o")

story_writer_agent = Agent(
    name="story_writer_agent",
    model=MODEL,
    description=STORY_WRITER_DESCRIPTION,
    instruction=STORY_WRITER_INSTRUCTION,
    output_key="story_writer_agent_output",
    output_schema=StoryWriterOutput
)
