from google.adk.agents import SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from .illust_generator.agent import illust_generator_agent
from .story_generator.agent import story_generator_agent
from .editor.agent import editor_agent


MODEL = LiteLlm(model="openai/gpt-4o-mini")

story_book_manager = SequentialAgent(
    name="story_book_manager",
    sub_agents=[
        story_generator_agent,
        illust_generator_agent,
        # editor_agent
    ]
)