"""
Streamlit UI - Claude-inspired with real-time streaming
"""
import json
import os
import uuid

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
FALLBACK_MODEL = "llama3.2:8b"

st.set_page_config(page_title="Local AI Helper", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    * {font-family: 'Inter', sans-serif;}
    
    .main {background: #ffffff;}
    [data-testid="stSidebar"] {background: #f7f7f8;}
    
    /* Chat messages */
    [data-testid="stChatMessage"] {
        padding: 1.25rem;
        border-radius: 0.5rem;
        margin: 0.75rem 0;
    }
    
    [data-testid="stChatMessage"][data-testid*="user"] {
        background: #f4f4f5;
        border-left: 3px solid #ab68ff;
    }
    
    [data-testid="stChatMessage"][data-testid*="assistant"] {
        background: #ffffff;
        border-left: 3px solid #10a37f;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% {opacity: 1;}
        50% {opacity: 0.5;}
    }
    
    .loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 0.5rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# State
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = "general"
if "model" not in st.session_state:
    st.session_state.model = FALLBACK_MODEL
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 128
if "api_status" not in st.session_state:
    st.session_state.api_status = {"ok": False, "details": {}}


def check_api_health():
    """Lightweight API health probe with friendly error handling."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        if response.status_code != 200:
            return {"ok": False, "details": {"status": response.status_code}}
        payload = response.json()
        return {"ok": payload.get("status") == "healthy", "details": payload}
    except Exception as exc:  # pragma: no cover - defensive UI guard
        return {"ok": False, "details": {"error": str(exc)}}

def load_models():
    """Fetch configured models and the recommended default from the API."""
    try:
        response = requests.get(f"{API_URL}/api/v1/models/list", timeout=10)
        if response.status_code != 200:
            return [], FALLBACK_MODEL, FALLBACK_MODEL

        payload = response.json()
        return (
            payload.get("models", []),
            payload.get("default", FALLBACK_MODEL),
            payload.get("recommended", payload.get("default", FALLBACK_MODEL)),
        )
    except Exception:
        return [], FALLBACK_MODEL, FALLBACK_MODEL

def stream_response(message, agent_mode, model, use_memory, temp, tokens):
    try:
        r = requests.post(
            f"{API_URL}/api/v1/chat/stream",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "agent_mode": agent_mode,
                "model": model,
                "use_memory": use_memory,
                "temperature": temp,
                "max_tokens": tokens
            },
            stream=True,
            timeout=300
        )
        
        for line in r.iter_lines():
            if line:
                text = line.decode('utf-8')
                if text.startswith('data: '):
                    data = json.loads(text[6:])
                    if not data.get('done'):
                        yield data.get('text', '')
    except Exception as e:
        yield f"Error: {str(e)}"

st.session_state.api_status = check_api_health()
models, _default_model, recommended_model = load_models()
installed = [m for m in models if m.get('installed')]
model_choices = [m['name'] for m in installed] or [recommended_model]
if st.session_state.model not in model_choices:
    st.session_state.model = recommended_model

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 AI Assistant")

    api_status = st.session_state.api_status
    if api_status['ok']:
        st.success("API connected")
    else:
        st.error("API unavailable. Check that the backend is running.")

    st.markdown("**Mode**")
    modes = {'general': '💬 General', 'math': '🔢 Math', 'code': '💻 Code', 'writing': '✍️ Writing', 'design': '🎨 Design'}
    st.session_state.agent_mode = st.selectbox("", list(modes.keys()), format_func=lambda x: modes[x], label_visibility="collapsed")

    st.markdown("**Model**")
    st.session_state.model = st.selectbox("", model_choices, label_visibility="collapsed", help="Pick an installed model. Download one below if the list is empty.")

    use_memory = st.checkbox("💾 Memory", True)

    with st.expander("⚙️ Settings"):
        st.caption("**Temperature** - Higher = more creative")
        st.session_state.temperature = st.slider("", 0.0, 1.0, st.session_state.temperature, 0.1, label_visibility="collapsed")
        st.caption("**Max Tokens** - Lower = faster")
        st.session_state.max_tokens = st.select_slider("", [64, 128, 256, 512], st.session_state.max_tokens, label_visibility="collapsed")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # History
    with st.expander("📋 History"):
        try:
            r = requests.get(f"{API_URL}/api/v1/memory/sessions", timeout=10)
            if r.status_code == 200:
                sessions = r.json().get('sessions', [])
                if not sessions:
                    st.caption("No previous chats")
                else:
                    for s in sessions[:10]:
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            label = s.get('preview') or "New chat"
                            if st.button(f"{label[:30]}...", key=f"s{s['session_id']}", use_container_width=True, help="Load this session"):
                                st.session_state.session_id = s['session_id']
                                try:
                                    hr = requests.get(f"{API_URL}/api/v1/chat/sessions/{s['session_id']}/history", timeout=10)
                                    convos = hr.json().get('conversations', [])
                                    msgs = []
                                    for c in reversed(convos):
                                        msgs.append({"role": "user", "content": c['user_message']})
                                        msgs.append({"role": "assistant", "content": c['assistant_message']})
                                    st.session_state.messages = msgs
                                except Exception:
                                    st.session_state.messages = []
                                st.rerun()
                        with col2:
                            if st.button("🗑", key=f"d{s['session_id']}"):
                                try:
                                    requests.delete(f"{API_URL}/api/v1/memory/sessions/{s['session_id']}", timeout=10)
                                except Exception:
                                    pass
                                st.rerun()
            else:
                st.caption("Unable to load history")
        except Exception:
            st.caption("History unavailable")

    # Models
    with st.expander("📦 Models"):
        if not installed:
            st.info("Download a model to start chatting.")
        for m in models:
            st.markdown(f"**{m['display_name']}** • {m['size']}")

            if m.get('installed'):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.success("✓ Installed")
                with col2:
                    if st.button("🗑️", key=f"del{m['name']}", help="Delete model"):
                        with st.spinner("Deleting..."):
                            try:
                                requests.delete(f"{API_URL}/api/v1/models/delete/{m['name']}")
                                st.success("Deleted!")
                            except Exception:
                                st.error("Failed")
                        st.rerun()
            else:
                if st.button("⬇️ Download", key=f"dl{m['name']}", use_container_width=True):
                    with st.spinner("Downloading... (5-10 min)"):
                        try:
                            requests.post(f"{API_URL}/api/v1/models/pull", json={"model_name": m['name']}, timeout=900)
                            st.success("Done!")
                        except Exception:
                            st.error("Failed")
                    st.rerun()
            st.divider()

# Main
st.title("Local AI Helper")

if not st.session_state.api_status['ok']:
    st.error("Connect to the API to start chatting. Ensure `uvicorn src.api.main:app` is running.")
    st.stop()

summary_col1, summary_col2, summary_col3 = st.columns(3)
summary_col1.metric("Connection", "Online", delta_color="inverse")
summary_col2.metric("Installed models", len(installed))
summary_col3.metric("Recommended", recommended_model)

st.caption("Friendly multi-mode assistant. Start with a question below or download a model from the sidebar.")

if not installed:
    st.warning("No models installed. Download one from the sidebar to begin chatting.")

st.caption(f"{modes[st.session_state.agent_mode]} • {st.session_state.model}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if installed and (prompt := st.chat_input("Message...")):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        try:
            for chunk in stream_response(
                prompt,
                st.session_state.agent_mode,
                st.session_state.model,
                use_memory,
                st.session_state.temperature,
                st.session_state.max_tokens
            ):
                if chunk.startswith("Error:"):
                    placeholder.error(chunk)
                    break
                full_response += chunk
                placeholder.markdown(full_response + "▌")

            if full_response:
                placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            placeholder.error(f"❌ {str(e)}")

st.caption("🚀 Powered by Open Source LLMs")
