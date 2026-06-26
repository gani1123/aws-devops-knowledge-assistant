"""
AWS DevOps Knowledge Assistant — Streamlit Frontend.

A professional chat interface that communicates with the FastAPI backend
to answer AWS DevOps questions using Amazon Bedrock Knowledge Bases.

Design choices:
  - AWS dark navy (#0D1B2A) sidebar with orange (#FF9900) accents
  - JetBrains Mono for code blocks, Inter for UI copy
  - Native st.chat_message() for a modern, familiar chat experience
  - Compact hero strip instead of a full-height splash to keep the chat
    viewport as tall as possible
"""

import time
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

API_BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
REQUEST_TIMEOUT = 60  # seconds

SUGGESTED_QUESTIONS: list[str] = [
    "What is AWS IAM and how does it work?",
    "How do I set up a CI/CD pipeline using AWS CodePipeline?",
    "What is the difference between ECS and EKS?",
    "How does AWS Auto Scaling work?",
    "What is Infrastructure as Code and how does Terraform fit in?",
    "How do I secure an S3 bucket in AWS?",
    "What is the AWS Shared Responsibility Model?",
    "How do I monitor AWS resources using CloudWatch?",
    "What is the difference between AWS CodeDeploy and CodePipeline?",
    "How do I configure VPC networking in AWS?",
]

APP_TITLE = "AWS DevOps Knowledge Assistant"
APP_ICON = "☁️"

# ---------------------------------------------------------------------------
# Page configuration  (must be the first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
        /* ── Google Fonts ─────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ── Root tokens ──────────────────────────────────────────── */
        :root {
            --aws-orange:    #FF9900;
            --aws-navy:      #0D1B2A;
            --aws-navy-mid:  #1A2D42;
            --aws-navy-soft: #243447;
            --aws-white:     #FFFFFF;
            --text-primary:  #111827;
            --text-muted:    #6B7280;
            --border:        #E5E7EB;
            --bg-page:       #F8FAFC;
            --radius-md:     0.625rem;
            --radius-lg:     1rem;
        }

        /* ── Global resets ────────────────────────────────────────── */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 860px;
        }
        #MainMenu, footer, header { visibility: hidden; }

        /* ── Sidebar shell ────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background: var(--aws-navy) !important;
        }
        [data-testid="stSidebar"] * {
            color: #CBD5E1 !important;
        }
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] strong {
            color: var(--aws-white) !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: var(--aws-navy-soft) !important;
        }

        /* ── Sidebar buttons (suggested questions) ────────────────── */
        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            text-align: left;
            background: var(--aws-navy-mid);
            border: 1px solid var(--aws-navy-soft);
            border-radius: var(--radius-md);
            color: #CBD5E1 !important;
            font-size: 0.80rem;
            line-height: 1.4;
            padding: 0.55rem 0.75rem;
            margin-bottom: 0.35rem;
            transition: background 0.18s, border-color 0.18s, color 0.18s;
            white-space: normal;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: var(--aws-orange);
            border-color: var(--aws-orange);
            color: var(--aws-navy) !important;
            font-weight: 600;
        }

        /* ── Sidebar primary action buttons ──────────────────────── */
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: var(--aws-orange);
            border-color: var(--aws-orange);
            color: var(--aws-navy) !important;
            font-weight: 600;
        }

        /* ── Hero strip ───────────────────────────────────────────── */
        .hero-strip {
            background: linear-gradient(135deg, var(--aws-navy) 0%, var(--aws-navy-mid) 100%);
            border-radius: var(--radius-lg);
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .hero-icon {
            font-size: 2.6rem;
            line-height: 1;
        }
        .hero-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--aws-white);
            margin: 0;
            letter-spacing: -0.02em;
        }
        .hero-sub {
            font-size: 0.875rem;
            color: #94A3B8;
            margin: 0.2rem 0 0;
        }
        .hero-badge {
            margin-left: auto;
            background: rgba(255,153,0,0.15);
            border: 1px solid rgba(255,153,0,0.35);
            border-radius: 9999px;
            padding: 0.3rem 0.9rem;
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--aws-orange);
            white-space: nowrap;
        }

        /* ── Status pills ─────────────────────────────────────────── */
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.25rem 0.7rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .pill-online  { background:#D1FAE5; color:#065F46; }
        .pill-offline { background:#FEE2E2; color:#991B1B; }
        .pill-unknown { background:#F3F4F6; color:#6B7280; }

        /* ── Response-time caption ────────────────────────────────── */
        .resp-time {
            font-size: 0.72rem;
            color: var(--text-muted);
            text-align: right;
            margin-top: -0.25rem;
            margin-bottom: 0.5rem;
        }

        /* ── Empty state ──────────────────────────────────────────── */
        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--text-muted);
        }
        .empty-state .icon { font-size: 3rem; margin-bottom: 0.75rem; }
        .empty-state p     { font-size: 0.95rem; max-width: 440px; margin: 0 auto; }

        /* ── Chat input send button ───────────────────────────────── */
        [data-testid="stChatInputSubmitButton"] svg { color: var(--aws-orange); }

        /* ── Sidebar caption / small text ─────────────────────────── */
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] small {
            color: #64748B !important;
            font-size: 0.72rem !important;
        }

        /* ── Scrollable suggested-question area ───────────────────── */
        .sq-scroll {
            max-height: 340px;
            overflow-y: auto;
            padding-right: 2px;
        }

        /* ── Footer ───────────────────────────────────────────────── */
        .app-footer {
            text-align: center;
            font-size: 0.72rem;
            color: var(--text-muted);
            padding: 1.5rem 0 0;
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history: list[dict[str, str]] = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question: str = ""

if "backend_status" not in st.session_state:
    # "unknown" | "online" | "offline"
    st.session_state.backend_status: str = "unknown"

if "last_response_time" not in st.session_state:
    st.session_state.last_response_time: float | None = None

# ---------------------------------------------------------------------------
# Backend helpers
# ---------------------------------------------------------------------------


def check_backend_health() -> bool:
    """
    Ping the FastAPI ``GET /health`` endpoint.

    Returns:
        ``True`` if the backend is reachable and returns HTTP 200.
    """
    try:
        resp = requests.get(HEALTH_ENDPOINT, timeout=5)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False


def ask_question(question: str) -> str:
    """
    POST a user question to the FastAPI ``POST /chat`` endpoint.

    Args:
        question: The user's natural-language question.

    Returns:
        The assistant answer string, or a user-friendly error message.
    """
    try:
        resp = requests.post(
            CHAT_ENDPOINT,
            json={"question": question},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("answer", "No answer returned.")

    except requests.exceptions.ConnectionError:
        return (
            "⚠️ **Cannot connect to the backend.**  \n"
            "Make sure the FastAPI server is running on `localhost:8000`."
        )
    except requests.exceptions.Timeout:
        return (
            "⚠️ **Request timed out.**  \n"
            "The Knowledge Base is taking longer than expected — please try again."
        )
    except requests.exceptions.HTTPError as exc:
        code = exc.response.status_code if exc.response else "unknown"
        return f"⚠️ **Backend error (HTTP {code}).** Please try again."
    except Exception as exc:  # noqa: BLE001
        return f"⚠️ **Unexpected error:** {exc}"


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def _status_pill(status: str) -> str:
    """Return an HTML status pill for the given status string."""
    icons = {"online": "●", "offline": "●", "unknown": "○"}
    labels = {"online": "Online", "offline": "Offline", "unknown": "Not checked"}
    css = {"online": "pill-online", "offline": "pill-offline", "unknown": "pill-unknown"}
    icon = icons.get(status, "○")
    label = labels.get(status, status.capitalize())
    cls = css.get(status, "pill-unknown")
    return f'<span class="pill {cls}">{icon} {label}</span>'


def render_chat_history() -> None:
    """Render every message stored in ``st.session_state.chat_history``."""
    for message in st.session_state.chat_history:
        role = message["role"]
        with st.chat_message(role, avatar="🧑" if role == "user" else "☁️"):
            st.markdown(message["content"])


def handle_question(question: str) -> None:
    """
    Append the user question, call the API, store the answer, and track timing.

    Args:
        question: Validated, non-empty question string.
    """
    # Persist the user turn immediately so it renders on rerun
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.chat_message("assistant", avatar="☁️"):
        with st.spinner("Querying AWS DevOps Knowledge Base…"):
            t0 = time.monotonic()
            answer = ask_question(question)
            elapsed = time.monotonic() - t0

        st.markdown(answer)
        st.session_state.last_response_time = elapsed

    st.session_state.chat_history.append({"role": "assistant", "content": answer})


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## ☁️ AWS DevOps\nAssistant")
    st.markdown("---")

    # ── Backend status ─────────────────────────────────────────────────
    st.markdown("### 🔌 Backend Status")
    if st.button("Check connection", use_container_width=True, type="primary"):
        alive = check_backend_health()
        st.session_state.backend_status = "online" if alive else "offline"

    st.markdown(
        _status_pill(st.session_state.backend_status),
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Suggested questions ────────────────────────────────────────────
    st.markdown("### 💡 Suggested Questions")
    st.caption("Click to ask instantly.")

    st.markdown('<div class="sq-scroll">', unsafe_allow_html=True)
    for q in SUGGESTED_QUESTIONS:
        if st.button(q, key=f"sq_{q[:40]}"):
            st.session_state.pending_question = q
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ── Session controls ───────────────────────────────────────────────
    st.markdown("### 🗑️ Session")
    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pending_question = ""
        st.session_state.last_response_time = None
        st.rerun()

    st.markdown("---")
    st.caption(
        "Powered by **Amazon Bedrock** Knowledge Bases  \n"
        "Built with **FastAPI** & **Streamlit**"
    )

# ---------------------------------------------------------------------------
# Hero strip
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="hero-strip">
        <div class="hero-icon">☁️</div>
        <div>
            <p class="hero-title">AWS DevOps Knowledge Assistant</p>
            <p class="hero-sub">Instant answers from Amazon Bedrock Knowledge Bases</p>
        </div>
        <div class="hero-badge">Bedrock · RAG</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Chat history — render all previous turns
# ---------------------------------------------------------------------------

if st.session_state.chat_history:
    render_chat_history()
    if st.session_state.last_response_time is not None:
        st.markdown(
            f'<p class="resp-time">⏱ Last response: '
            f'{st.session_state.last_response_time:.1f}s</p>',
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">🛠️</div>
            <p>Type an AWS DevOps question below, or pick one from
               <strong>Suggested Questions</strong> in the sidebar to get started.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Chat input  (native Streamlit component — renders at bottom of viewport)
# ---------------------------------------------------------------------------

# Consume a pending suggested question if the user clicked one
prefill = st.session_state.pending_question
st.session_state.pending_question = ""

user_input: str | None = st.chat_input(
    placeholder="e.g. How do I configure IAM roles for EC2?",
    key="chat_input",
)

# Prioritise typed input; fall back to a suggested-question click
question_to_process = (user_input or "").strip() or prefill.strip()

if question_to_process:
    if len(question_to_process) < 3:
        st.warning("Question is too short — please be more specific.", icon="⚠️")
    elif len(question_to_process) > 1000:
        st.warning("Question exceeds the 1,000-character limit.", icon="⚠️")
    else:
        # Render the user bubble immediately, then answer
        with st.chat_message("user", avatar="🧑"):
            st.markdown(question_to_process)
        handle_question(question_to_process)
        st.rerun()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="app-footer">
        AWS DevOps Knowledge Assistant &nbsp;·&nbsp;
        Amazon Bedrock &nbsp;·&nbsp; FastAPI &nbsp;·&nbsp; Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)