from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext

from .prompt import EDITOR_AGENT_DESCRIPTION, EDITOR_AGENT_INSTRUCTION
from .tools import build_finished_storybook_markdown

MODEL = LiteLlm(model="openai/gpt-4o-mini")


def before_agent_callback(callback_context: CallbackContext):
    print("🌈 동화 최종 정리중...")
    return None


editor_agent = Agent(
    name="editor_agent",
    model=MODEL,
    description=EDITOR_AGENT_DESCRIPTION,
    instruction=EDITOR_AGENT_INSTRUCTION,
    before_agent_callback=before_agent_callback,
    tools=[
        build_finished_storybook_markdown,
    ],
)