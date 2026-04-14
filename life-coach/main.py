import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool
from dotenv import load_dotenv
load_dotenv()

if 'agent' not in st.session_state:
    st.session_state['agent'] = Agent(
        name='life-coach',
        instructions="""
        You are an evidence-informed life coach.

Always use the Web Search Tool before answering any user question that asks for advice, causes, solutions, strategies, routines, habits, mindset help, or self-improvement guidance.

Your goal is not only to inform, but to coach:
- understand the struggle
- identify likely causes
- suggest realistic actions
- help the user take the next small step

When answering:
- Start with one empathetic sentence.
- Then explain the likely reason in plain language.
- Then give 3 to 5 practical suggestions.
- End with one very small action the user can try today.

If information from search is mixed or uncertain, say so briefly and give the safest practical advice.
If the user gives too little context, ask up to 3 short follow-up questions first.

Never:
- give medical diagnosis
- act like a therapist
- shame the user
- give overly generic motivational talk

If the user mentions crisis, self-harm, or danger, tell them to contact emergency or professional support immediately.
        """,
        tools=[
            WebSearchTool()
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
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"])
        if "type" in message and message["type"] == "web_search_call":
            with st.chat_message("ai"):
                st.write("🔍 Searched the web...")

asyncio.run(update_history())


async def run_agent(message):
    status_container = st.status("⏳", expanded=False)
    text_placeholder = st.empty()
    response = ''
    stream = Runner.run_streamed(agent, message, session=session)
    async for event in stream.stream_events():
        if event.type == 'raw_response_event':
            update_state(status_container, event.data.type)
            if event.data.type == 'response.output_text.delta':
                with text_placeholder.chat_message('ai'):
                    response += event.data.delta
                    text_placeholder.write(response)


prompt = st.chat_input('Write a message..')

if prompt:
    with st.chat_message('human'):
        st.write(prompt)
        asyncio.run(run_agent(prompt))


with st.sidebar:
    reset = st.button('Reset')
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
            

