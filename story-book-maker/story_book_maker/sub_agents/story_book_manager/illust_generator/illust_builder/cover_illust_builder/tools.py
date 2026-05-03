import base64
from google.genai import types
from openai import OpenAI
from google.adk.tools.tool_context import ToolContext

client = OpenAI()


async def generate_cover_illust(tool_context: ToolContext):

    prompt_builder_agent_output = tool_context.state.get("prompt_builder_agent_output")
    cover_prompts = prompt_builder_agent_output.get("cover_prompts")

    filename = f"cover_image.jpeg"
    
    image = client.images.generate(
            model="gpt-image-1.5",
            prompt=cover_prompts,
            n=1,
            quality="medium",
            moderation="low",
            output_format="jpeg",
            background="opaque",
            size="1024x1536",
        )

    image_bytes = base64.b64decode(image.data[0].b64_json)

    artifact = types.Part(
        inline_data=types.Blob(
            mime_type="image/jpeg",
            data=image_bytes,
        )
    )

    await tool_context.save_artifact(
        filename=filename,
        artifact=artifact,
    )


    return {
        "generated_image": filename,
        "status": "complete",
    }