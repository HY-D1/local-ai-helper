"""
Streamlit UI for Local AI Helper - Enhanced Version
"""
import streamlit as st
import requests
import os
import uuid
from datetime import datetime
import time

API_URL = os.getenv('API_URL', 'http://localhost:8000')

st.set_page_config(
    page_title="Local AI Helper",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with animations and modern design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: #f5f7fa;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* Chat container */
    .stChatMessage {
        animation: slideIn 0.3s ease-out;
        margin-bottom: 1rem;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* User message */
    .stChatMessage[data-testid*="user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-radius: 18px !important;
    }
    
    .stChatMessage[data-testid*="user"] p,
    .stChatMessage[data-testid*="user"] div {
        color: white !important;
    }
    
    /* Assistant message */
    .stChatMessage[data-testid*="assistant"] {
        background: white !important;
        border-radius: 18px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .stChatMessage[data-testid*="assistant"] p,
    .stChatMessage[data-testid*="assistant"] div {
        color: #1a1a2e !important;
    }
    
    /* Model cards */
    .model-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .model-card:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .model-name {
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
        color: #fff;
    }
    
    .model-specs {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 0.5rem;
    }
    
    /* Status badges */
    .status-ready {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .status-available {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Section headers */
    .section-header {
        font-size: 0.75rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        letter-spacing: 1px;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    
    /* Chat input */
    .stChatInputContainer {
        border-radius: 25px;
        background: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Title area */
    h1 {
        color: #1a1a2e !important;
        font-weight: 800;
    }
    
    /* Captions */
    .stCaption {
        color: #666 !important;
    }
    
    /* Selectbox */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Hide branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Slider - scoped to sidebar */
    [data-testid="stSidebar"] .stSlider > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Chat input styling */
    .stChatInputContainer {
        background: white;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'agent_mode' not in st.session_state:
    st.session_state.agent_mode = 'general'
if 'model' not in st.session_state:
    st.session_state.model = 'llama3.2:3b'
if 'temperature' not in st.session_state:
    st.session_state.temperature = 0.7
if 'max_tokens' not in st.session_state:
    st.session_state.max_tokens = 512

def load_models():
    try:
        response = requests.get(f"{API_URL}/api/v1/models/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data['models'], data['default']
        return [], 'llama3.2:3b'
    except:
        return [], 'llama3.2:3b'

def load_session_history():
    try:
        response = requests.get(f"{API_URL}/api/v1/memory/sessions", timeout=5)
        if response.status_code == 200:
            return response.json()['sessions']
        return []
    except:
        return []

def load_session_messages(session_id):
    try:
        response = requests.get(f"{API_URL}/api/v1/chat/sessions/{session_id}/history", timeout=5)
        if response.status_code == 200:
            convos = response.json()['conversations']
            messages = []
            for c in convos:
                messages.append({"role": "user", "content": c['user_message']})
                messages.append({"role": "assistant", "content": c['assistant_message']})
            return messages[::-1]
        return []
    except:
        return []

def send_message(message, agent_mode, model, use_memory=True, temperature=0.7, max_tokens=512):
    try:
        response = requests.post(
            f"{API_URL}/api/v1/chat/completion",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "agent_mode": agent_mode,
                "model": model,
                "use_memory": use_memory,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# Sidebar
with st.sidebar:
    st.markdown("# 🤖 AI Assistant")
    
    models, default_model = load_models()
    installed_models = [m for m in models if m.get('installed', False)]
    
    if not installed_models:
        st.error("⚠️ No models installed")
        st.info("👇 Download a model below")
    
    # Agent mode
    st.markdown('<div class="section-header">Mode</div>', unsafe_allow_html=True)
    agent_modes = {
        'general': '💬 General',
        'math': '🔢 Math',
        'code': '💻 Code',
        'writing': '✍️ Writing',
        'design': '🎨 Design'
    }
    
    selected_mode = st.selectbox(
        "mode",
        options=list(agent_modes.keys()),
        format_func=lambda x: agent_modes[x],
        index=list(agent_modes.keys()).index(st.session_state.agent_mode),
        label_visibility="collapsed"
    )
    st.session_state.agent_mode = selected_mode
    
    # Model selection
    st.markdown('<div class="section-header">Model</div>', unsafe_allow_html=True)
    model_options = [m['name'] for m in models if m.get('installed', False)]
    if not model_options:
        model_options = [default_model]
    
    selected_model = st.selectbox(
        "model",
        options=model_options,
        index=model_options.index(st.session_state.model) if st.session_state.model in model_options else 0,
        label_visibility="collapsed"
    )
    st.session_state.model = selected_model
    
    # Settings
    st.markdown('<div class="section-header">Settings</div>', unsafe_allow_html=True)
    use_memory = st.checkbox("💾 Memory", value=True)
    
    with st.expander("⚙️ Advanced"):
        temperature = st.slider("🌡️ Temperature", 0.0, 1.0, 0.7, 0.1)
        max_tokens = st.select_slider(
            "📏 Length",
            options=[128, 256, 512, 1024, 2048],
            value=512
        )
        st.session_state.temperature = temperature
        st.session_state.max_tokens = max_tokens
    
    # Session controls
    st.markdown('<div class="section-header">Chat</div>', unsafe_allow_html=True)
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
    with st.expander("📋 History", expanded=False):
        sessions = load_session_history()
        if not sessions:
            st.caption("No previous chats")
        else:
            for sess in sessions[:10]:
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(
                        f"{sess['preview'][:20]}...",
                        key=f"sess_{sess['session_id']}",
                        use_container_width=True
                    ):
                        st.session_state.session_id = sess['session_id']
                        st.session_state.messages = load_session_messages(sess['session_id'])
                        st.rerun()
                with col2:
                    if st.button("🗑", key=f"del_{sess['session_id']}"):
                        try:
                            resp = requests.delete(f"{API_URL}/api/v1/memory/sessions/{sess['session_id']}")
                            if resp.status_code == 200:
                                st.rerun()
                        except:
                            pass
    
    # Model downloads
    expand_models = not installed_models
    with st.expander("📦 Download Models", expanded=expand_models):
        if not models:
            st.error("❌ API offline")
        else:
            for model in models:
                st.markdown(f"""
                <div class="model-card">
                    <div class="model-name">{model['display_name']}</div>
                    <div class="model-specs">📦 {model['size']} • ⚡ {model['speed']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if model.get('installed'):
                    st.markdown('<span class="status-ready">✓ Installed</span>', unsafe_allow_html=True)
                else:
                    if st.button(f"⬇️ Download", key=f"dl_{model['name']}", use_container_width=True):
                        with st.spinner(f"Downloading {model['display_name']}...\n⏱️ 5-10 min"):
                            try:
                                response = requests.post(
                                    f"{API_URL}/api/v1/models/pull",
                                    json={"model_name": model['name']},
                                    timeout=600
                                )
                                if response.status_code == 200:
                                    st.success("✅ Done!")
                                    st.balloons()
                                else:
                                    st.error(f"Failed: {response.status_code}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                        st.rerun()

# Main chat
st.title("🤖 Local AI Helper")
mode_emoji = {'general': '💬', 'math': '🔢', 'code': '💻', 'writing': '✍️', 'design': '🎨'}
st.caption(f"{mode_emoji[st.session_state.agent_mode]} {agent_modes[st.session_state.agent_mode]} • {st.session_state.model}")

# Chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        with st.spinner("🤔 Thinking..."):
            response = send_message(
                prompt,
                st.session_state.agent_mode,
                st.session_state.model,
                use_memory,
                st.session_state.temperature,
                st.session_state.max_tokens
            )
        
        if "error" in response:
            st.error(f"❌ {response['error']}")
        else:
            # Animated typing effect
            full_response = response['response']
            displayed = ""
            words = full_response.split()
            
            for i, word in enumerate(words):
                displayed += word + " "
                if i % 3 == 0:
                    message_placeholder.markdown(displayed + "▌")
                    time.sleep(0.03)
            
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response
            })

st.markdown("---")
st.caption("🚀 Powered by Open Source LLMs • Built with ❤️")