import base64
import io
from google.genai import types
from openai import OpenAI
from google.adk.tools.tool_context import ToolContext

client = OpenAI()


async def generate_third_illust(tool_context: ToolContext):

    prompt_builder_agent_output = tool_context.state.get("prompt_builder_agent_output")
    optimized_prompts = prompt_builder_agent_output.get("optimized_prompts")
    character_prompts = prompt_builder_agent_output.get("character_prompts")

    prompt = optimized_prompts[2]
    scene_id = prompt.get("scene_id")
    enhanced_prompt = prompt.get("enhanced_prompt")
    filename = f"scene_{scene_id}_image.jpeg"
    
    image = client.images.generate(
            model="gpt-image-1.5",
            prompt=f"## 캐릭터 {character_prompts} ## 삽화 {enhanced_prompt}",
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
        "scene_id": scene_id,
        "generated_image": filename,
        "status": "complete",
    }