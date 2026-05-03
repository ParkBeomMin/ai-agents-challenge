from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import FIFTH_ILLUST_BUILDER_AGENT_DESCRIPTION, FIFTH_ILLUST_BUILDER_AGENT_INSTRUCTION
from .tools import generate_fifth_illust
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest


MODEL = LiteLlm(model="openai/gpt-4o-mini")

def before_model_callback(callback_context: CallbackContext,
    llm_request: LlmRequest):
    print("🎨 다섯번째 삽화 생성중..")
    return None

fifth_illust_builder_agent = Agent(
    name="fifth_illust_builder_agent",
    model=MODEL,
    description=FIFTH_ILLUST_BUILDER_AGENT_DESCRIPTION,
    instruction=FIFTH_ILLUST_BUILDER_AGENT_INSTRUCTION,
    tools=[
        generate_fifth_illust
    ],
    before_model_callback=before_model_callback,
    output_key="fifth_illust_builder_agent_output"
)