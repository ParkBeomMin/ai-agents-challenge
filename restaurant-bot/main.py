import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, InputGuardrailTripwireTriggered
from restaurant_agents.triage_agent import triage_agent
from dotenv import load_dotenv

load_dotenv()


if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent


# 메모리 생성
if 'session' not in st.session_state:
    st.session_state['session'] = SQLiteSession(
        'chat-history',
        'restaurant-bot-memeory.db'
    )

session = st.session_state['session']


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
        

asyncio.run(update_history())


# 에이전트 실행
async def run_agent(message):
        with st.chat_message("ai"):
            text_placeholder = st.empty()
            response = ""

            st.session_state["text_placeholder"] = text_placeholder

            try:
                stream = Runner.run_streamed(
                    st.session_state["agent"],
                    message, 
                    session=session
                    
                    )
                async for event in stream.stream_events():
                    if event.type == 'raw_response_event':
                        if event.data.type == 'response.output_text.delta':
                            response += event.data.delta
                            text_placeholder.write(response.replace("$", "\$"))
                    elif event.type == "agent_updated_stream_event":
                        if st.session_state["agent"].name != event.new_agent.name:
                            st.write(f"🤖 Transfered from {st.session_state["agent"].name} to {event.new_agent.name}")
                            st.session_state["agent"] = event.new_agent
                            text_placeholder = st.empty()
                            st.session_state["text_placeholder"] = text_placeholder
                            response = ""
            except InputGuardrailTripwireTriggered:
                st.write("도와드릴 수 없는 내용입니다.")

# 사용자 입력
prompt = st.chat_input('Write a message..')

if prompt:
    with st.chat_message('human'):
        st.write(prompt)
    asyncio.run(run_agent(prompt))
        


with st.sidebar:
    reset = st.button('Reset')
    if reset:
        asyncio.run(session.clear_session())
        st.session_state.clear()
        st.rerun()
    st.write(asyncio.run(session.get_items()))
            

