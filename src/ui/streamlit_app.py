"""
Streamlit UI - Claude-inspired with real-time streaming
"""
import json
import os
import time
import uuid

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
FALLBACK_MODEL = "qwen2.5:7b"

st.set_page_config(page_title="Local AI Helper", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    * {font-family: 'Inter', sans-serif;}

    body {background: #0f172a;}
    .main {
        background: radial-gradient(circle at 20% 20%, rgba(88, 28, 135, 0.08), transparent 30%),
                    radial-gradient(circle at 80% 10%, rgba(16, 163, 127, 0.08), transparent 35%),
                    linear-gradient(145deg, #0b1220 0%, #0f172a 35%, #111827 100%);
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] {
        background: #0b1220;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    [data-testid="stSidebar"] .stButton>button,
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] .stSelectbox>div>div {
        background: #111827 !important;
        color: #e5e7eb !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
    }

    /* Hero + stat cards */
    .hero {
        padding: 1.5rem 1.25rem;
        background: linear-gradient(120deg, rgba(16, 163, 127, 0.08), rgba(88, 28, 135, 0.12));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        box-shadow: 0 20px 80px rgba(0, 0, 0, 0.25);
    }

    .hero h1 {
        color: #f8fafc;
        margin-bottom: 0.25rem;
        font-weight: 700;
    }

    .eyebrow { text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.75rem; color: #a5b4fc; }
    .subtitle { color: #cbd5f5; margin-top: 0.35rem; }

    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.9rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #e5e7eb;
        background: rgba(255, 255, 255, 0.04);
    }

    .pill.success { color: #34d399; border-color: rgba(52, 211, 153, 0.25); background: rgba(52, 211, 153, 0.08); }
    .pill.warn { color: #fbbf24; border-color: rgba(251, 191, 36, 0.25); background: rgba(251, 191, 36, 0.08); }

    .stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }

    .stat-card {
        padding: 1rem;
        background: #0b1220;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 0.9rem;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
    }

    .stat-label { color: #9ca3af; font-size: 0.9rem; margin-bottom: 0.25rem; }
    .stat-value { color: #f8fafc; font-size: 1.4rem; font-weight: 700; }
    .stat-meta { color: #a5b4fc; font-size: 0.9rem; margin-top: 0.15rem; }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        padding: 1.25rem;
        border-radius: 0.75rem;
        margin: 0.85rem 0;
        background: linear-gradient(145deg, rgba(23, 37, 84, 0.65), rgba(15, 118, 110, 0.18));
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 14px 50px rgba(0, 0, 0, 0.28);
    }

    [data-testid="stChatMessage"][data-testid*="user"] {
        border-left: 4px solid #a855f7;
    }

    [data-testid="stChatMessage"][data-testid*="assistant"] {
        border-left: 4px solid #22c55e;
    }

    /* Chat input tweaks */
    [data-testid="stChatInput"] > div {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8), rgba(34, 197, 94, 0.06));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 0.9rem !important;
        box-shadow: 0 18px 60px rgba(0, 0, 0, 0.32);
        padding: 0.35rem 0.4rem;
    }

    [data-testid="stChatInput"] textarea {
        color: #e5e7eb !important;
        background: transparent !important;
        border: none !important;
    }

    [data-testid="stChatInput"] label p {
        color: #cbd5f5 !important;
    }

    /* Loading animation */
    @keyframes pulse {
        0%, 100% {opacity: 1;}
        50% {opacity: 0.5;}
    }

    .loading { animation: pulse 1.5s ease-in-out infinite; }

    /* Buttons */
    .stButton>button {
        border-radius: 0.6rem;
        font-weight: 600;
        transition: all 0.2s;
        background: #111827;
        color: #e5e7eb;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        border-color: rgba(16, 163, 127, 0.5);
        box-shadow: 0 8px 30px rgba(16, 163, 127, 0.12);
    }

    [data-testid="stChatInput"] textarea {
        background: #0b1220;
        color: #e5e7eb;
        border-radius: 0.75rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
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
if "download_task" not in st.session_state:
    st.session_state.download_task = None


def check_api_health(timeout: float = 8.0):
    """Lightweight API health probe with friendly error handling."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=timeout)
        if response.status_code != 200:
            return {"ok": False, "details": {"status": response.status_code}}
        payload = response.json()
        return {"ok": payload.get("status") == "healthy", "details": payload}
    except Exception as exc:  # pragma: no cover - defensive UI guard
        return {"ok": False, "details": {"error": str(exc)}}


def wait_for_api(retries: int = 1, delay: float = 1.5):
    """Give the backend a moment to start before marking it unavailable."""

    status = check_api_health()
    if status.get("ok"):
        return status

    for _ in range(retries):
        time.sleep(delay)
        status = check_api_health()
        if status.get("ok"):
            return status

    return status

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


def poll_download_task(api_url: str, task: dict):
    """Poll a download task from the API and return status + UI-friendly fields."""

    try:
        task_resp = requests.get(
            f"{api_url}/api/v1/models/tasks/{task['task_id']}", timeout=10
        )
        if task_resp.status_code != 200:
            return {
                "status": "error",
                "detail": f"Unable to fetch progress ({task_resp.status_code})",
                "percent": task.get("percent", 0),
            }

        payload = task_resp.json()
        percent = payload.get("percent")
        status_text = payload.get("status", "in_progress")
        detail_text = payload.get("detail", status_text)

        return {
            "status": status_text,
            "detail": detail_text,
            "percent": percent if percent is not None else task.get("percent", 0),
        }
    except Exception as exc:  # pragma: no cover - UI guard
        return {
            "status": "error",
            "detail": f"Progress check failed: {exc}",
            "percent": task.get("percent", 0),
        }


def _quality_score(label: str) -> int:
    order = ["excellent", "very good", "good", "ok"]
    label = (label or "").lower()
    for idx, tag in enumerate(order[::-1]):
        if tag in label:
            return idx + 1
    return 0


def model_for_mode(mode: str, models: list[dict[str, str]], installed: list[str], recommended: str):
    """Pick the best installed model for a mode when available."""
    installed_set = set(installed)
    candidates = [m for m in models if mode in m.get("best_for", [])]
    candidates.sort(
        key=lambda m: (_quality_score(m.get("quality", "")), m.get("size", "")),
        reverse=True,
    )

    for candidate in candidates:
        if candidate["name"] in installed_set:
            return candidate["name"], candidate

    if recommended in installed_set:
        rec_model = next((m for m in models if m.get("name") == recommended), None)
        return recommended, rec_model

    if installed:
        fallback = installed[0]
        fallback_model = next((m for m in models if m.get("name") == fallback), None)
        return fallback, fallback_model

    return recommended, next((m for m in models if m.get("name") == recommended), None)

def stream_response(message, agent_mode, model, use_memory, temp, tokens):
    try:
        with requests.post(
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
        ) as r:
            if r.status_code != 200:
                try:
                    detail = r.json().get('detail', r.text)
                except Exception:
                    detail = r.text
                yield f"Error: API returned {r.status_code} - {detail}"
                return

            for line in r.iter_lines():
                if not line:
                    continue
                text = line.decode('utf-8')
                if not text.startswith('data: '):
                    continue
                data = json.loads(text[6:])
                if data.get('error'):
                    yield f"Error: {data.get('error')}"
                    return
                if not data.get('done'):
                    yield data.get('text', '')
    except Exception as e:
        yield f"Error: {str(e)}"

api_status = wait_for_api(retries=2)
st.session_state.api_status = api_status
models, _default_model, recommended_model = load_models()
installed = [m for m in models if m.get('installed')]
installed_names = [m['name'] for m in installed]
models_by_name = {m["name"]: m for m in models}

recommended_installed = (
    recommended_model
    if recommended_model in installed_names
    else (installed_names[0] if installed_names else recommended_model)
)

model_choices = installed_names or [recommended_installed]
if st.session_state.model not in model_choices:
    st.session_state.model = recommended_installed

preset_model_name, preset_model_meta = model_for_mode(
    st.session_state.agent_mode,
    models,
    installed_names,
    recommended_model,
)

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 AI Assistant")

    api_status = st.session_state.api_status
    detail = api_status.get("details", {})
    error_msg = detail.get("error") or detail.get("status") or "API unavailable"
    if api_status['ok']:
        st.success("API connected")
    else:
        st.warning(f"API warming up… {error_msg}")
        if st.button("Retry connection", use_container_width=True):
            st.session_state.api_status = wait_for_api(retries=2)
            st.experimental_rerun()

    st.markdown("**Mode**")
    modes = {'general': '💬 General', 'math': '🔢 Math', 'code': '💻 Code', 'writing': '✍️ Writing', 'design': '🎨 Design'}
    st.session_state.agent_mode = st.selectbox("", list(modes.keys()), format_func=lambda x: modes[x], label_visibility="collapsed")

    preset_model_name, preset_model_meta = model_for_mode(
        st.session_state.agent_mode,
        models,
        installed_names,
        recommended_model,
    )
    if preset_model_meta:
        st.caption(
            f"Suggested for {modes[st.session_state.agent_mode]}: "
            f"{preset_model_meta.get('display_name', preset_model_name)}"
        )
        if preset_model_name and preset_model_name != st.session_state.model:
            if st.button("Use mode preset", use_container_width=True):
                st.session_state.model = preset_model_name
                st.rerun()

    st.markdown("**Model**")
    st.session_state.model = st.selectbox("", model_choices, label_visibility="collapsed", help="Pick an installed model. Download one below if the list is empty.")

    if st.session_state.model not in installed_names and installed_names:
        st.warning("Previously selected model is missing. Using the closest installed option instead.")

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
        active_task = st.session_state.download_task

        if active_task:
            st.info(f"Downloading {active_task.get('model', '')}...")
            status_placeholder = st.empty()
            detail_placeholder = st.empty()
            progress_bar = st.progress(
                active_task.get("percent", 0), text="Checking download..."
            )

            elapsed = time.time() - active_task.get("started_at", time.time())
            if elapsed > 900:
                status_placeholder.error("Download timed out")
                st.session_state.download_task = None
            else:
                task_status = poll_download_task(API_URL, active_task)
                percent = task_status.get("percent") or 0
                status_text = task_status.get("status", "in_progress")
                detail_text = task_status.get("detail", status_text)

                detail_placeholder.caption(detail_text)
                progress_bar.progress(
                    min(max(percent, 0), 100),
                    text=f"{status_text} ({int(percent)}%)" if percent else status_text,
                )

                if status_text == "completed":
                    status_placeholder.success("Download completed")
                    st.session_state.download_task = None
                    st.experimental_rerun()
                elif status_text == "error":
                    status_placeholder.error(detail_text)
                    st.session_state.download_task = None
                else:
                    status_placeholder.info(status_text)
                    st.session_state.download_task.update(
                        {
                            "percent": percent,
                            "status": status_text,
                            "detail": detail_text,
                        }
                    )
                    time.sleep(1)
                    st.experimental_rerun()

        if not installed:
            st.info("Download a model to start chatting.")
        for m in models:
            badges = []
            if m['name'] == recommended_model:
                badges.append("recommended")
            if m['name'] == preset_model_name:
                badges.append("preset")

            badge_text = " • ".join(badges)
            st.markdown(
                f"**{m['display_name']}** • {m['size']} • {m.get('quality', '').title()}"
                + (f" • {badge_text}" if badge_text else "")
            )
            if m.get("strengths"):
                st.caption(m["strengths"])
            if m.get("best_for"):
                st.caption("Best for: " + ", ".join(m.get("best_for", [])))

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
                    status_placeholder = st.empty()
                    detail_placeholder = st.empty()
                    progress_bar = st.progress(0, text="Starting download...")

                    try:
                        resp = requests.post(
                            f"{API_URL}/api/v1/models/pull",
                            json={"model_name": m['name']},
                            timeout=30,
                        )
                        if resp.status_code != 200:
                            try:
                                detail = resp.json().get('detail', resp.text)
                            except Exception:
                                detail = resp.text
                            status_placeholder.error(detail or 'Failed to start download')
                        else:
                            task_id = resp.json().get("task_id")
                            if not task_id:
                                status_placeholder.error("Download task not created")
                            else:
                                st.session_state.download_task = {
                                    "task_id": task_id,
                                    "model": m["name"],
                                    "percent": 0,
                                    "started_at": time.time(),
                                }
                                status_placeholder.info(
                                    "Download started — tracking progress below."
                                )
                                st.experimental_rerun()
                    except Exception as exc:  # pragma: no cover - UI guard
                        status_placeholder.error(f"Failed to start download: {exc}")
                    st.experimental_rerun()
            st.divider()

# Main
connection_state = "Online" if st.session_state.api_status.get("ok") else "Offline"
connection_detail = st.session_state.api_status.get("details", {})
connection_delta = connection_detail.get("status") or connection_detail.get("error") or ""
status_pill_class = "success" if st.session_state.api_status.get("ok") else "warn"
status_text = "API connected" if st.session_state.api_status.get("ok") else "API unavailable"

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">Local-first AI workspace</div>
        <h1>Local AI Helper</h1>
        <p class="subtitle">Chat, code, design and explore your models with a calmer, higher contrast interface.</p>
        <div style="display:flex; gap:0.5rem; align-items:center; flex-wrap: wrap; margin-top: 0.6rem;">
            <span class="pill {status_pill_class}">• {status_text}</span>
            <span class="pill">Mode: {modes[st.session_state.agent_mode]}</span>
            <span class="pill">Model: {st.session_state.model}</span>
        </div>
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-label">Connection</div>
                <div class="stat-value">{connection_state}</div>
                <div class="stat-meta">{connection_delta}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Installed models</div>
                <div class="stat-value">{len(installed)}</div>
                <div class="stat-meta">Recommended: {recommended_model}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Session</div>
                <div class="stat-value">{st.session_state.session_id[:8]}...</div>
                <div class="stat-meta">Memory {"on" if use_memory else "off"}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.api_status['ok']:
    detail = st.session_state.api_status.get("details", {})
    detail_text = detail.get("error") or detail.get("status") or "backend not reachable"
    st.error(
        "Connect to the API to start chatting. Ensure `uvicorn src.api.main:app` is running."
    )
    st.caption(f"Latest check: {detail_text}")
    if st.button("Retry connection"):
        st.session_state.api_status = wait_for_api(retries=2)
        st.experimental_rerun()
    st.stop()

st.caption("Friendly multi-mode assistant. Start with a question below or download a model from the sidebar.")

if not installed:
    st.warning("No models installed. Download one from the sidebar to begin chatting.")

st.caption(f"{modes[st.session_state.agent_mode]} • {st.session_state.model}")

current_model_meta = models_by_name.get(st.session_state.model)
if current_model_meta and (current_model_meta.get("strengths") or current_model_meta.get("best_for")):
    best_for = ", ".join(current_model_meta.get("best_for", []))
    st.info(
        f"{current_model_meta.get('display_name', st.session_state.model)} is a strong fit for {best_for or 'general use'}. "
        f"{current_model_meta.get('strengths', '')}"
    )

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
