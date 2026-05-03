from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import SECOND_ILLUST_BUILDER_AGENT_DESCRIPTION, SECOND_ILLUST_BUILDER_AGENT_INSTRUCTION
from .tools import generate_second_illust
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest


MODEL = LiteLlm(model="openai/gpt-4o-mini")

def before_model_callback(callback_context: CallbackContext,
    llm_request: LlmRequest):
    print("🎨 두번째 삽화 생성중..")
    return None

second_illust_builder_agent = Agent(
    name="second_illust_builder_agent",
    model=MODEL,
    description=SECOND_ILLUST_BUILDER_AGENT_DESCRIPTION,
    instruction=SECOND_ILLUST_BUILDER_AGENT_INSTRUCTION,
    tools=[
        generate_second_illust
    ],
    before_model_callback=before_model_callback,
    output_key="second_illust_builder_agent_output"
)