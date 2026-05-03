from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from story_book_maker.sub_agents.story_book_manager.illust_generator.illust_builder.first_illust_builder.prompt import FIRST_ILLUST_BUILDER_AGENT_DESCRIPTION, FIRST_ILLUST_BUILDER_AGENT_INSTRUCTION
from .tools import generate_first_illust

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest

MODEL = LiteLlm(model="openai/gpt-4o-mini")

def before_model_callback(callback_context: CallbackContext,
    llm_request: LlmRequest):
    print("🎨 첫번째 삽화 생성중..")
    return None

first_illust_builder_agent = Agent(
    name="first_illust_builder_agent",
    model=MODEL,
    description=FIRST_ILLUST_BUILDER_AGENT_DESCRIPTION,
    instruction=FIRST_ILLUST_BUILDER_AGENT_INSTRUCTION,
    tools=[
        generate_first_illust
    ],
    before_model_callback=before_model_callback,
    output_key="first_illust_builder_agent_output"
)