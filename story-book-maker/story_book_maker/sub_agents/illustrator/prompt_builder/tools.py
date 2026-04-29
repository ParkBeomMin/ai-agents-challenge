import json
from google.adk.tools.tool_context import ToolContext

def get_story_writer_agent_output(tool_context: ToolContext):
    story_writer_agent_output = tool_context.state.get('story_writer_agent_output')
    return json.dumps(story_writer_agent_output)
    # return story_writer_agent_output.model_dump_json()