from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import CHARACTER_BUILDER_DESCRIPTION, CHARACTER_BUILDER_INSTRUCTION
from .tools import generate_character

MODEL = LiteLlm(model="openai/gpt-4o-mini")

def before_model_callback():
    print("🦄 캐릭터 생성중..")
    return None

character_builder_agent = Agent(
    name="character_builder_agent",
    model=MODEL,
    description=CHARACTER_BUILDER_DESCRIPTION,
    instruction=CHARACTER_BUILDER_INSTRUCTION,
    tools=[
        generate_character
    ],
    output_key="character_builder_agent_output",
    before_model_callback=before_model_callback
)