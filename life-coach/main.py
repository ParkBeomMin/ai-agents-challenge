import asyncio
from cProfile import label
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool
from dotenv import load_dotenv
from openai import OpenAI
import os
load_dotenv()

VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID")

client = OpenAI()

if 'agent' not in st.session_state:
    st.session_state['agent'] = Agent(
        name='life-coach',
        instructions="""
        You are a warm, practical, evidence-informed life coach.

        You have access to:
        - Web Search Tool
        - File Search Tool

        Tool rules:
        1. If the user asks about their own facts, goals, habits, plans, reflections, or any uploaded file, use the File Search Tool first.
        2. If the user is also asking for advice, causes, solutions, strategies, routines, habits, mindset help, or self-improvement guidance, use the Web Search Tool after File Search.
        3. Use the file for personal context and use web search for evidence-based general guidance.
        4. If personal file content and web information conflict, trust the file for the user's personal facts.
        5. If the file is relevant, do not skip

        대화 규칙(반드시 지킬 것):

        - 사용자가 목표/습관/계획/업로드한 문서 내용에 대해 물으면:
        1) 반드시 File Search Tool을 먼저 호출한다.
        2) File Search 결과를 근거로 1~2문장으로 “파일 기반 관찰”을 말한다.
        3) 이어서 반드시 Web Search Tool을 호출한다.
            - 웹검색 쿼리는 File Search에서 찾은 키워드로 1개만 만든다.
            - 예: "운동 루틴 유지하는 방법", "주 3회 운동 습관 형성 팁" 등

        """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=[
                    VECTOR_STORE_ID
                ],
                max_num_results=3
            )
        ]
    )

agent = st.session_state['agent']

if 'session' not in st.session_state:
    st.session_state['session'] = SQLiteSession(
        'chat-history',
        'life-coach-memeory.db'
    )

session = st.session_state['session']

def update_state(status_container, event):
    status_messages = {
        "response.web_search_call.in_progress": ('🔍 Starting web searching...', 'running'),
        "response.web_search_call.searching": ('🔍 Web search in progressing...', 'running'),
        "response.web_search_call.completed": ('✅ Web search completed', 'complete'),
        "response.file_search_call.in_progress": ('📁 Starting file searching...', 'running'),
        "response.file_search_call.searching": ('📁 File search in progressing...', 'running'),
        "response.file_search_call.completed": ('✅ File search completed', 'complete'),
        "response.completed": (' ', 'complete')
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


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
        if "type" in message and message["type"] == "web_search_call":
            with st.chat_message("ai"):
                st.write("🔍 Searched the web...")
        if "type" in message and message["type"] == "file_search_call":
            with st.chat_message("ai"):
                st.write("📁 Searched the file...")

asyncio.run(update_history())


async def run_agent(message):
        with st.chat_message("ai"):
            status_container = st.status("⏳", expanded=False)
            text_placeholder = st.empty()
            response = ''
            stream = Runner.run_streamed(agent, message, session=session)
            async for event in stream.stream_events():
                if event.type == 'raw_response_event':
                    update_state(status_container, event.data.type)
                    if event.data.type == 'response.output_text.delta':
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\$"))


prompt = st.chat_input('Write a message..', accept_file=True, file_type=['txt'])

if prompt:
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
            

