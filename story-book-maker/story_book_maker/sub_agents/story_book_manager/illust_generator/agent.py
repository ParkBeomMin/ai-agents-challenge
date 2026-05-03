from google.adk.agents import SequentialAgent

from story_book_maker.sub_agents.story_book_manager.illust_generator.illust_builder.agent import illust_builder_agent

from .character_builder.agent import character_builder_agent

from .promp import ILLUST_GENERATOR_DESCRIPTION



illust_generator_agent = SequentialAgent(
    name="illust_generator_agent",
    description=ILLUST_GENERATOR_DESCRIPTION,
    sub_agents=[
        # character_builder_agent,
        illust_builder_agent
    ]
)