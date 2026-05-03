from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import PROMPT_BUILDER_DESCRIPTION, PROMPT_BUILDER_INSTRUCTION
from pydantic import BaseModel, Field
from typing import List
from .tools import get_story_writer_agent_output

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest

MODEL = LiteLlm(model="openai/gpt-4.1-nano")

class StyleGuide(BaseModel):
    art_style: str = Field(description="그림 스타일(아동 그림책, 수채화/파스텔 등)")
    color_palette: str = Field(description="색감 팔레트(파스텔 톤, 따뜻한 색 위주 등)")
    lighting: str = Field(description="조명(부드러운 자연광 등)")
    line_style: str = Field(description="선 스타일(부드러운 라인, 과한 디테일 금지 등)")
    consistency_rules: str = Field(description="캐릭터/배경 일관성 규칙(절대 바꾸면 안 되는 요소)")

class OptimizedPrompt(BaseModel):
    scene_id: int = Field(ge=1, le=5, description="페이지/장면 ID (1~5)")
    enhanced_prompt: str = Field(
        description="해당 페이지 일러스트 생성을 위한 최적화 프롬프트(텍스트 오버레이 금지 포함)"
    )
class CharacterPrompt(BaseModel):
    name: str
    appearance: str
class PromptBuilderOutput(BaseModel):
    optimized_prompts: List[OptimizedPrompt] = Field(
        description="5페이지(1~5) 일러스트 생성용 최적화 프롬프트 목록"
    )
    character_prompts: CharacterPrompt = Field(description="동화 캐릭터 생성용 프롬프트")
    cover_prompts: str = Field(description="동화 커버 생성용 프롬프트")
    style_guide: StyleGuide = Field(description="전체 스타일 가이드(모든 장면에 공통 적용)")


def before_agent_callback(
    callback_context: CallbackContext):
    print("🧑‍💻 이미지 생성 프롬프트 생성중...")
    return None

prompt_builder_agent = Agent(
    name="prompt_builder_agent",
    model=MODEL,
    description=PROMPT_BUILDER_DESCRIPTION,
    instruction=PROMPT_BUILDER_INSTRUCTION,
    output_key="prompt_builder_agent_output",
    output_schema=PromptBuilderOutput,
    tools=[
        get_story_writer_agent_output
    ],
    before_agent_callback=before_agent_callback
)