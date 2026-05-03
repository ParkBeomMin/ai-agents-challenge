from google.adk.agents import ParallelAgent

from .first_illust_builder.agent import first_illust_builder_agent
from .second_illust_builder.agent import second_illust_builder_agent
from .third_illust_builder.agent import third_illust_builder_agent
from .fourth_illust_builder.agent import fourth_illust_builder_agent
from .fifth_illust_builder.agent import fifth_illust_builder_agent
from .cover_illust_builder.agent import cover_illust_builder_agent


illust_builder_agent = ParallelAgent(
    name="illust_builder_agent",
    sub_agents=[
        cover_illust_builder_agent,
        first_illust_builder_agent,
        second_illust_builder_agent,
        third_illust_builder_agent,
        fourth_illust_builder_agent,
        fifth_illust_builder_agent,
    ]
)