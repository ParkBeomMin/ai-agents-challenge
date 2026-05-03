from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm


from .prompt import STORY_BOOK_MAKER_DESCRIPTION, STORY_BOOK_MAKER_INSTRUCTION
from .sub_agents.story_book_manager.agent import story_book_manager
from .sub_agents.story_book_manager.illust_generator.agent import illust_generator_agent

MODEL = LiteLlm(model="openai/gpt-4o-mini")

story_book_maker_agent = Agent(
    name="story_book_maker_agent",
    model=MODEL,
    description=STORY_BOOK_MAKER_DESCRIPTION,
    instruction=STORY_BOOK_MAKER_INSTRUCTION,
    tools=[
        AgentTool(agent=story_book_manager),
        AgentTool(agent=illust_generator_agent),
    ]
)

root_agent = story_book_maker_agent