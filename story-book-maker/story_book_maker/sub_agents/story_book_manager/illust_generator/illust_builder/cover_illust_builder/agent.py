from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import COVER_ILLUST_BUILDER_AGENT_DESCRIPTION, COVER_ILLUST_BUILDER_AGENT_INSTRUCTION
from .tools import generate_cover_illust
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest


MODEL = LiteLlm(model="openai/gpt-4o-mini")

def before_model_callback(callback_context: CallbackContext,
    llm_request: LlmRequest):
    print("🎨 표지 생성중..")
    return None

cover_illust_builder_agent = Agent(
    name="cover_illust_builder_agent",
    model=MODEL,
    description=COVER_ILLUST_BUILDER_AGENT_DESCRIPTION,
    instruction=COVER_ILLUST_BUILDER_AGENT_INSTRUCTION,
    tools=[
        generate_cover_illust
    ],
    before_model_callback=before_model_callback,
    output_key="cover_illust_builder_agent_output"
)