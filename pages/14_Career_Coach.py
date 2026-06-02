"""
Page 14 — AI Career Coach Chat
Real-time advice, LinkedIn tips, resume hints, and career guidance.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, render_sidebar_nav,
    render_ai_provider_selector, empty_state
)
from src.database.supabase_client import db_insert, db_select
from src.ai.gemini_client import chat_career_coach
from src.utils.helpers import generate_session_id

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("AI Career Coach", "Real-time advice, placement roadmap tips, and career guidance", "💬")

# Initialize Chat Session
if "coach_session_id" not in st.session_state:
    st.session_state["coach_session_id"] = generate_session_id()
if "coach_chat_history" not in st.session_state:
    st.session_state["coach_chat_history"] = []

session_id = st.session_state["coach_session_id"]
chat_history = st.session_state["coach_chat_history"]

# Display conversation
for msg in chat_history:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    if role == "user":
        st.markdown(f"""
        <div style="display:flex;justify-content:flex-end;margin-bottom:0.75rem;">
            <div style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.25);
                 border-radius:16px 16px 4px 16px;padding:0.75rem 1rem;max-width:70%;">
                <div style="color:#f1f5f9;line-height:1.6;">{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex;gap:0.75rem;margin-bottom:0.75rem;">
            <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#8b5cf6,#06b6d4);
                 display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0;">💬</div>
            <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                 border-radius:4px 16px 16px 16px;padding:0.75rem 1rem;flex:1;">
                <div style="color:#a78bfa;font-size:0.72rem;font-weight:600;margin-bottom:0.3rem;">CAREER COACH</div>
                <div style="color:#e2e8f0;line-height:1.65;">{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Coach Input ───────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask about LinkedIn optimization, resumes, placements...")

if user_input:
    chat_history.append({"role": "user", "content": user_input})
    # Save user message to DB
    db_insert("chat_history", {
        "user_id": user_id,
        "session_id": session_id,
        "chat_type": "career_coach",
        "role": "user",
        "content": user_input,
    })

    # Prepare performance summary context
    perf = db_select("interviews", {"user_id": user_id}, order="created_at.desc", limit=5)
    perf_str = "No completed sessions yet."
    if perf:
        perf_str = ", ".join([f"{p.get('interview_type','').replace('_',' ').title()} score: {p.get('overall_score',0)}" for p in perf])

    # AI Response
    with st.spinner("🤖 Thinking..."):
        # Format chat history context
        hist_context = "\n".join([f"{'Candidate' if h['role']=='user' else 'Coach'}: {h['content']}" for h in chat_history[-5:]])
        
        reply = chat_career_coach(
            name=profile.get("full_name", "Student") if profile else "Student",
            branch=profile.get("branch", "Computer Science") if profile else "Computer Science",
            college=profile.get("college", "University") if profile else "University",
            target_role="Software Engineer",
            performance=perf_str,
            message=user_input,
            history=hist_context,
        )

    chat_history.append({"role": "assistant", "content": reply})
    # Save assistant message to DB
    db_insert("chat_history", {
        "user_id": user_id,
        "session_id": session_id,
        "chat_type": "career_coach",
        "role": "assistant",
        "content": reply,
    })
    
    st.session_state["coach_chat_history"] = chat_history
    st.rerun()

# Control buttons
if chat_history:
    if st.button("🗑️ Clear Chat History", key="clear_coach"):
        st.session_state["coach_chat_history"] = []
        st.session_state["coach_session_id"] = generate_session_id()
        st.rerun()
