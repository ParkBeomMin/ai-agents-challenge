from google.adk.agents import SequentialAgent
from .prompt import ILLUSTRATOR_DESCRIPTION
from .image_builder.agent import image_builder_agent
from .prompt_builder.agent import prompt_builder_agent


illustrator_agent = SequentialAgent(
    name="illustrator_agent",
    description=ILLUSTRATOR_DESCRIPTION,
    sub_agents=[
        prompt_builder_agent,
        image_builder_agent
    ]
   
)
