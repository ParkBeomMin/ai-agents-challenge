from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from .prompt import STORY_BOOK_MAKER_DESCRIPTION, STORY_BOOK_MAKER_INSTRUCTION
from .sub_agents.story_writer.agent import story_writer_agent
from .sub_agents.illustrator.agent import illustrator_agent

MODEL = LiteLlm(model="openai/gpt-4o-mini")

story_book_maker_agent = Agent(
    name="story_book_maker_agent",
    model=MODEL,
    description=STORY_BOOK_MAKER_DESCRIPTION,
    instruction=STORY_BOOK_MAKER_INSTRUCTION,
    tools=[
        AgentTool(agent=story_writer_agent),
        AgentTool(agent=illustrator_agent),
    ]
)

root_agent = story_book_maker_agent