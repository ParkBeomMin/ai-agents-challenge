from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import FOURTH_ILLUST_BUILDER_AGENT_DESCRIPTION, FOURTH_ILLUST_BUILDER_AGENT_INSTRUCTION
from .tools import generate_fourth_illust
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest

MODEL = LiteLlm(model="openai/gpt-4o-mini")

def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest):
    print("🎨 네번째 삽화 생성중..")
    return None

fourth_illust_builder_agent = Agent(
    name="fourth_illust_builder_agent",
    model=MODEL,
    description=FOURTH_ILLUST_BUILDER_AGENT_DESCRIPTION,
    instruction=FOURTH_ILLUST_BUILDER_AGENT_INSTRUCTION,
    tools=[
        generate_fourth_illust
    ],
    before_model_callback=before_model_callback,
    output_key="fourth_illust_builder_agent_output"
)