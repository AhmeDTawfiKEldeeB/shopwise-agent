import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (str(SRC), str(ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from Agent.agent import ask, build_agent  # noqa: E402

st.set_page_config(page_title="ShopWise Agent", page_icon="🛍️", layout="wide")


@st.cache_resource
def get_agent():
    return build_agent()


def load_thread_state(thread_id: str) -> list:
    state = get_agent().get_state({"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])


def load_thread_summary(thread_id: str) -> str:
    state = get_agent().get_state({"configurable": {"thread_id": thread_id}})
    return state.values.get("summary", "")


if "threads" not in st.session_state:
    st.session_state.threads = {}
if "current_thread" not in st.session_state:
    st.session_state.current_thread = None


def new_chat() -> str:
    thread_id = f"chat-{uuid.uuid4().hex[:8]}"
    st.session_state.threads[thread_id] = f"Chat {len(st.session_state.threads) + 1}"
    st.session_state.current_thread = thread_id
    return thread_id


with st.sidebar:
    st.title("🛍️ ShopWise Agent")
    if st.button("➕ New Chat", use_container_width=True):
        new_chat()
        st.rerun()

    st.divider()
    st.subheader("Chats")
    if st.session_state.threads:
        for thread_id, title in list(st.session_state.threads.items()):
            if st.button(title, key=f"select-{thread_id}", use_container_width=True):
                st.session_state.current_thread = thread_id
                st.rerun()
    else:
        st.caption("No chats yet. Start a new one!")

thread_id = st.session_state.current_thread

if thread_id is None:
    st.info("👋 Start a **New Chat** from the sidebar to talk to the agent.")
    st.stop()

st.header("🛍️ ShopWise Agent")

summary = load_thread_summary(thread_id)
if summary:
    with st.expander("📝 Conversation summary", expanded=False):
        st.write(summary)

messages = load_thread_state(thread_id)

for message in messages:
    if message.type == "human":
        with st.chat_message("user"):
            st.markdown(message.content)
    elif message.type == "ai":
        if message.tool_calls:
            with st.chat_message("assistant"):
                st.caption(
                    "🔧 searched the product catalog: "
                    + ", ".join(tool["name"] for tool in message.tool_calls)
                )
        if message.content:
            with st.chat_message("assistant"):
                st.markdown(message.content)

prompt = st.chat_input("Ask about products…")

if prompt:
    if not st.session_state.threads.get(thread_id) or st.session_state.threads[thread_id].startswith("Chat "):
        st.session_state.threads[thread_id] = prompt[:40] + ("…" if len(prompt) > 40 else "")

    with st.chat_message("user"):
        st.markdown(prompt)
    with st.spinner("Thinking…"):
        answer = ask(prompt, thread_id=thread_id)
    with st.chat_message("assistant"):
        st.markdown(answer)
    st.rerun()
