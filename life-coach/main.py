import asyncio
from cProfile import label
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool, ImageGenerationTool
from agents.run_config import RunConfig, ModelInputData, CallModelData
from dotenv import load_dotenv
from openai import OpenAI
import base64
import os

load_dotenv()

VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID")

client = OpenAI()

# 에이전트 생성
if 'agent' not in st.session_state:
    st.session_state['agent'] = Agent(
        name='life-coach',
        instructions="""
        너는 사용자의 Life Coach야.

        사용자의 목표, 비전, 일기등을 참고해서 더 나은 방향으로 나아갈 수 있도록 조언, 팁, 동기부여를 해주고 task를 관리해줘야 해.

        You have access to:
        - Web Search Tool: Use this when the user asks a questions that isn't in your training data. Use this tool when the users asks about current or future events, when you think you don't know the answer, try searching for it in the web first.
        - File Search Tool: 개인 목표 및 일기 참조에 사용한다.
        - Image Generation Tool: 비전 보드 및 동기부여 이미지 생성에 사용한다.

        Rule:

        - 사용자가 자신의 목표나 비전, 일기 등에 대해 물어볼 때는 반드시 조언이나 팁, 동기부여를 같이 해주는데 너의 생각은 버리고 반드시 Web Search Tool을 활용해서 신뢰할만한 웹 검색 정보로 응답 해줘야해.

        - 사용자가 목표를 달성한다면 내용을 확인해서 축하 이미지를 만들어서 축하해줘야 해.

        - 사용자가 요청한 질문에 대해서는 되묻지 않고 바로 진행해야해.

        - 각 tool을 사용할 때는 한번만 호출한다.
        """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[
                    VECTOR_STORE_ID
                ],
                max_num_results=3
            ),
            ImageGenerationTool(
                tool_config={
                    "type": "image_generation",
                    "quality": "high",
                    "output_format": "jpeg",
                    "partial_images": 1,
                }
            )
        ]
    )

agent = st.session_state['agent']

# 메모리 생성
if 'session' not in st.session_state:
    st.session_state['session'] = SQLiteSession(
        'chat-history',
        'life-coach-memeory.db'
    )

session = st.session_state['session']

# 에이전트 상태 업데이트, UI에 보여주기 위함
def update_state(status_container, event):
    status_messages = {
        "response.web_search_call.in_progress": ('🔍 Starting web searching...', 'running'),
        "response.web_search_call.searching": ('🔍 Web search in progressing...', 'running'),
        "response.web_search_call.completed": ('✅ Web search completed', 'complete'),
        "response.file_search_call.in_progress": ('📁 Starting file searching...', 'running'),
        "response.file_search_call.searching": ('📁 File search in progressing...', 'running'),
        "response.file_search_call.completed": ('✅ File search completed', 'complete'),
        "response.image_generation_call.generating": (
            "🎨 Drawing image...",
            "running",
        ),
        "response.image_generation_call.in_progress": (
            "🎨 Drawing image...",
            "running",
        ),
        "response.completed": (' ', 'complete')
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)

# 메모리 업데이트
async def update_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"].replace("$", "\$"))
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])
        if "type" in message:
            type = message["type"]
            if type == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 Searched the web...")
            elif type == "file_search_call":
                with st.chat_message("ai"):
                    st.write("📁 Searched the file...")
            elif type == "image_generation_call":
                image = base64.b64decode(message["result"])
                with st.chat_message("ai"):
                    st.image(image)
        
        

asyncio.run(update_history())


def filtering_session(data: CallModelData) -> ModelInputData:
    items = list(data.model_data.input)
    out = []
    for item in items:
        if isinstance(item, dict) and item.get("type") == "image_generation_call":
            cleaned = dict(item)
            cleaned.pop("action", None)
            out.append(cleaned)
        else:
            out.append(item)
    return ModelInputData(input=out, instructions=data.model_data.instructions)


# 에이전트 실행
async def run_agent(message):
        with st.chat_message("ai"):
            status_container = st.status("⏳", expanded=False)
            image_placeholder = st.empty()
            text_placeholder = st.empty()
            response = ""

            st.session_state["image_placeholder"] = image_placeholder
            st.session_state["text_placeholder"] = text_placeholder

            stream = Runner.run_streamed(agent, message, session=session,
                run_config=RunConfig(call_model_input_filter=filtering_session))
            async for event in stream.stream_events():
                if event.type == 'raw_response_event':
                    update_state(status_container, event.data.type)
                    if event.data.type == 'response.output_text.delta':
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\$"))
                    if event.data.type == "response.image_generation_call.partial_image":
                        image = base64.b64decode(event.data.partial_image_b64)
                        image_placeholder.image(image)

# 사용자 입력
prompt = st.chat_input('Write a message..', accept_file=True, file_type=['txt'])

if prompt:

    if "image_placeholder" in st.session_state:
        st.session_state["image_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    for file in prompt.files:
        if file.type.startswith('text/'):
            with st.chat_message('ai'):
                with st.status('📁 Uploading file...') as status:
                    uploaded_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose="user_data"
                    )
                    status.update(label='Attaching file...')
                    client.vector_stores.files.create(
                        vector_store_id=VECTOR_STORE_ID,
                        file_id=uploaded_file.id
                    )
                    status.update(label='File uploaded', state='complete')
    if prompt.text:
        with st.chat_message('human'):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))
        


with st.sidebar:
    reset = st.button('Reset')
    if reset:
        asyncio.run(session.clear_session())
        st.session_state.clear()
        st.rerun()
    st.write(asyncio.run(session.get_items()))
            

