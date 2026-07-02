import os
from pathlib import Path

import streamlit as st
import google.generativeai as genai


SYSTEM_PROMPT = """You are Vijay's Chatbot, a professional AI assistant designed for business, support, writing, analysis, and productivity tasks. Respond clearly, concisely, and helpfully. Keep your tone polished, trustworthy, and professional."""


def load_env_file(env_path: Path | None = None) -> None:
    path = env_path or Path(__file__).resolve().parent / ".env"
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env_file()


def get_client() -> object:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "No Gemini API key found. Add GEMINI_API_KEY to your environment or .env file before using the chatbot."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        system_instruction=SYSTEM_PROMPT,
    )
    return model


def generate_reply(messages: list[dict]) -> str:
    model = get_client()
    history = []
    for message in messages[-8:]:
        role = message["role"]
        content = message["content"]
        if role == "user":
            history.append({"role": "user", "parts": [content]})
        elif role == "assistant":
            history.append({"role": "model", "parts": [content]})

    chat = model.start_chat(history=history[:-1])
    prompt = history[-1]["parts"][0] if history else "Hello"
    response = chat.send_message(prompt)
    return response.text


st.set_page_config(page_title="Vijay's Chatbot", page_icon="🤖", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: #f8fafc;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    [data-testid="stSidebar"] {
        background-color: #111827;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Vijay's Chatbot")
st.caption("Professional AI assistant for business, support, drafting, research, and everyday productivity.")

with st.sidebar:
    st.header("About")
    st.write("Vijay's Chatbot is designed for professional conversations with a polished and dependable experience.")
    st.divider()
    st.subheader("Quick actions")
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.session_state["welcome_shown"] = False
        st.rerun()

    st.divider()
    st.write("Tip: add your API key to the .env file or your environment before chatting.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

if not st.session_state.welcome_shown and not st.session_state.messages:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I’m Vijay's Chatbot. I can help with professional writing, summaries, planning, brainstorming, and clear explanations.",
        }
    ]
    st.session_state.welcome_shown = True

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask Vijay's Chatbot anything...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        conversation = [{"role": "system", "content": SYSTEM_PROMPT}]
        conversation.extend(message for message in st.session_state.messages[-10:])
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = generate_reply(conversation)
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
    except Exception as exc:
        error_message = f"I’m unable to respond right now. {exc}"
        with st.chat_message("assistant"):
            st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
