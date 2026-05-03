from google.adk.agents import SequentialAgent

from .prompt_builder.agent import prompt_builder_agent
from .story_writer.agent import story_writer_agent

story_generator_agent = SequentialAgent(
    name="story_generator_agent",
    sub_agents=[
        story_writer_agent,
        prompt_builder_agent
    ]
)