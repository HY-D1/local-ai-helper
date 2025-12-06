"""
Streamlit UI - Claude-inspired with real-time streaming
"""
import streamlit as st
import requests
import os
import uuid
import json

API_URL = os.getenv('API_URL', 'http://localhost:8000')

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
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'agent_mode' not in st.session_state:
    st.session_state.agent_mode = 'general'
if 'model' not in st.session_state:
    st.session_state.model = 'phi3:mini'
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.7
if 'max_tokens' not in st.session_state:
    st.session_state.max_tokens = 128
if 'api_healthy' not in st.session_state:
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        st.session_state.api_healthy = r.status_code == 200
    except:
        st.session_state.api_healthy = False

def load_models():
    try:
        r = requests.get(f"{API_URL}/api/v1/models/list", timeout=10)
        return r.json()['models'], r.json()['default'] if r.status_code == 200 else ([], 'phi3:mini')
    except:
        return [], 'phi3:mini'

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

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 AI Assistant")
    
    models, default = load_models()
    installed = [m for m in models if m.get('installed')]
    
    if not installed:
        st.warning("⚠️ Download a model first")
    
    st.markdown("**Mode**")
    modes = {'general': '💬 General', 'math': '🔢 Math', 'code': '💻 Code', 'writing': '✍️ Writing', 'design': '🎨 Design'}
    st.session_state.agent_mode = st.selectbox("", list(modes.keys()), format_func=lambda x: modes[x], label_visibility="collapsed")
    
    st.markdown("**Model**")
    model_opts = [m['name'] for m in models if m.get('installed')] or [default]
    st.session_state.model = st.selectbox("", model_opts, label_visibility="collapsed")
    
    use_memory = st.checkbox("💾 Memory", True)
    
    with st.expander("⚙️ Settings"):
        st.caption("**Temperature** - Higher = more creative")
        st.session_state.temperature = st.slider("", 0.0, 1.0, 0.7, 0.1, label_visibility="collapsed")
        st.caption("**Max Tokens** - Lower = faster")
        st.session_state.max_tokens = st.select_slider("", [64, 128, 256, 512], 128, label_visibility="collapsed")
    
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
                sessions = r.json()['sessions']
                if not sessions:
                    st.caption("No previous chats")
                else:
                    for s in sessions[:10]:
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            if st.button(f"{s['preview'][:20]}...", key=f"s{s['session_id']}", use_container_width=True):
                                st.session_state.session_id = s['session_id']
                                try:
                                    hr = requests.get(f"{API_URL}/api/v1/chat/sessions/{s['session_id']}/history", timeout=10)
                                    convos = hr.json()['conversations']
                                    msgs = []
                                    for c in reversed(convos):
                                        msgs.append({"role": "user", "content": c['user_message']})
                                        msgs.append({"role": "assistant", "content": c['assistant_message']})
                                    st.session_state.messages = msgs
                                except:
                                    st.session_state.messages = []
                                st.rerun()
                        with col2:
                            if st.button("🗑", key=f"d{s['session_id']}"):
                                try:
                                    requests.delete(f"{API_URL}/api/v1/memory/sessions/{s['session_id']}", timeout=10)
                                except:
                                    pass
                                st.rerun()
            else:
                st.caption("Unable to load history")
        except:
            st.caption("History unavailable")
    
    # Models
    with st.expander("📦 Models"):
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
                            except:
                                st.error("Failed")
                        st.rerun()
            else:
                if st.button("⬇️ Download", key=f"dl{m['name']}", use_container_width=True):
                    with st.spinner("Downloading... (5-10 min)"):
                        try:
                            requests.post(f"{API_URL}/api/v1/models/pull", json={"model_name": m['name']}, timeout=900)
                            st.success("Done!")
                        except:
                            st.error("Failed")
                    st.rerun()
            st.divider()

# Main
st.title("Local AI Helper")
st.caption(f"{modes[st.session_state.agent_mode]} • {st.session_state.model}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message..."):
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