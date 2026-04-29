from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import PROMPT_BUILDER_DESCRIPTION, PROMPT_BUILDER_INSTRUCTION
from pydantic import BaseModel, Field
from typing import List
from .tools import get_story_writer_agent_output

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
class PromptBuilderOutput(BaseModel):
    optimized_prompts: List[OptimizedPrompt] = Field(
        description="5페이지(1~5) 일러스트 생성용 최적화 프롬프트 목록"
    )
    negative_prompt: str = Field(
        default="text, caption, subtitle, watermark, logo, letters, words",
        description="공통 네거티브 프롬프트(이미지 내 텍스트/워터마크 등 금지)"
    )
    style_guide: StyleGuide = Field(description="전체 스타일 가이드(모든 장면에 공통 적용)")


prompt_builder_agent = Agent(
    name="prompt_builder_agent",
    model=MODEL,
    description=PROMPT_BUILDER_DESCRIPTION,
    instruction=PROMPT_BUILDER_INSTRUCTION,
    output_key="prompt_builder_agent_output",
    output_schema=PromptBuilderOutput,
    tools=[
        get_story_writer_agent_output
    ]
)