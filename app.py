# app.py
import os
from PIL import Image
import streamlit as st
from openai import OpenAI

# --- Branding ---
LOGO_PATH_GREEN = "assets\TMCC - 583 - STACKED.png"   # put your logo file here

LOGO_PATH_BLACK = "assets\TMCC - BLACK - STACKED.png"   # put your logo file here

# Must be first Streamlit call
st.set_page_config(
    page_title="TMCC Policy Manual Assistant",
    page_icon=LOGO_PATH_BLACK,
    layout="wide",
)

# Fonts + a little CSS
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
/* Apply Inter to typical text containers only — don't clobber icon fonts */
body, .stMarkdown, .stTextInput input, .stButton button, .stChatMessage {
  font-family: 'Inter', sans-serif;
}
</style>
""", unsafe_allow_html=True)

st.title("TMCC Policy Manual Assistant")
st.caption("By Will Garibaldo")

# --- Load configuration ---
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = (
    st.secrets.get("VECTOR_STORE_ID")
    or os.getenv("VECTOR_STORE_ID")
    or (open("vector_store_id.txt", "r", encoding="utf-8").read().strip()
        if os.path.exists("vector_store_id.txt") else None)
)

if st.secrets.get("APP_PASSWORD"):
    PASS = os.getenv("APP_PASSWORD") or st.secrets["APP_PASSWORD"]
    if "authed" not in st.session_state:
        st.session_state.authed = False
    if not st.session_state.authed:
        pw = st.text_input("Enter access password", type="password")
        if st.button("Enter"):
            st.session_state.authed = (pw == PASS)
        st.stop()

if not OPENAI_API_KEY or not VECTOR_STORE_ID:
    with st.sidebar:
        st.image(LOGO_PATH_GREEN, use_container_width=True)
        st.markdown("---")
        if not OPENAI_API_KEY:
            st.error("Missing OPENAI_API_KEY environment variable.")
        if not VECTOR_STORE_ID:
            st.error("Missing VECTOR_STORE_ID (set env var or add vector_store_id.txt).")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a helpful assistant for Truckee Meadows Community College policies.
Use ONLY information retrieved via File Search from the provided knowledge base.
If the answer isn't in the provided context, say you don't know.
When possible, provide the TMCC policy number.
Include a short "Sources:" list with URLs when applicable.
Do not make up information or provide personal opinions.
""".strip()

# Sidebar
with st.sidebar:
    st.image(LOGO_PATH_GREEN, use_container_width=True)
    st.markdown("---")
    st.subheader("Settings")
    st.caption(f"Key loaded: {'✅' if bool(OPENAI_API_KEY) else '❌'}")
    st.caption(f"Vector store: {VECTOR_STORE_ID[:6]+'…' if VECTOR_STORE_ID else '❌'}")
    if st.button("Clear chat"):
        st.session_state["messages"] = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

# --- Chat state ---
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": SYSTEM_PROMPT}]

for m in st.session_state["messages"]:
    if m["role"] == "user":
        with st.chat_message("user"): st.markdown(m["content"])
    elif m["role"] == "assistant":
        with st.chat_message("assistant"): st.markdown(m["content"])

# --- Input + response ---
user = st.chat_input("Ask about TMCC policies…")
if user:
    st.session_state["messages"].append({"role": "user", "content": user})
    with st.chat_message("user"): st.markdown(user)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                resp = client.responses.create(
                    model="gpt-4o-mini",
                    input=st.session_state["messages"],
                    tools=[{"type": "file_search", "vector_store_ids": [VECTOR_STORE_ID]}],
                    # temperature=0.2,  # optional
                )
                answer = resp.output_text or "No response text."
            except Exception as e:
                answer = f"**Error:** {e}"
        st.markdown(answer)

    st.session_state["messages"].append({"role": "assistant", "content": answer})
