"""
AI Interview Preparation Assistant — Main Entry Point
Handles authentication flow, dynamic page navigation routing, and premium unified sidebar.
"""

import streamlit as st
from dotenv import load_dotenv
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import inject_global_css, render_sidebar_nav, render_ai_provider_selector

# ── Main Page Config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Interview Prep Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "AI Interview Preparation Assistant — Powered by Gemini 2.5 Flash",
    },
)

# Inject global CSS style rules
inject_global_css()

# Custom premium sidebar styles
st.markdown("""
<style>
    /* Hide native Streamlit Navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Style custom page links */
    div[data-testid="stPageLink"] {
        padding: 0.08rem 0.25rem !important;
    }
    div[data-testid="stPageLink"] a {
        background: transparent !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 0.45rem 0.75rem !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        color: var(--text-secondary) !important;
        transition: var(--transition) !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.6rem !important;
        text-decoration: none !important;
        width: 100% !important;
    }
    div[data-testid="stPageLink"] a:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: var(--text-primary) !important;
        padding-left: 0.9rem !important; /* Slide-in micro-animation */
    }
    /* Active menu item styling */
    div[data-testid="stPageLink"] a[aria-current="page"] {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25) !important;
    }
</style>
""", unsafe_allow_html=True)



# ── Dynamic Route Handling ────────────────────────────────────────────────────
if is_authenticated():
    # Fetch profile details for sidebar header card
    profile = get_current_profile()

    # Core Page Navigation Definitions
    pages = {
        "Dashboard": [
            st.Page("pages/01_Dashboard.py", title="Dashboard", icon="📊", default=True),
            st.Page("pages/11_Performance_Analytics.py", title="Performance Analytics", icon="📈"),
            st.Page("pages/12_Leaderboard.py", title="Leaderboard & XP", icon="🏆"),
        ],
        "AI Coaching": [
            st.Page("pages/06_Mock_Interview.py", title="Mock Interview", icon="🤖"),
            st.Page("pages/03_Technical_Interview.py", title="Technical Interview", icon="💻"),
            st.Page("pages/04_HR_Interview.py", title="HR Interview", icon="🤝"),
            st.Page("pages/05_Coding_Interview.py", title="Coding Interview", icon="👨‍💻"),
            st.Page("pages/07_Voice_Interview.py", title="Voice Interview", icon="🎙️"),
            st.Page("pages/08_Company_Prep.py", title="Company Prep", icon="🏢"),
        ],
        "Resources": [
            st.Page("pages/02_Resume_Analyzer.py", title="Resume Analyzer", icon="📄"),
            st.Page("pages/09_RAG_Assistant.py", title="RAG Assistant", icon="🧠"),
            st.Page("pages/10_Personalized_Roadmap.py", title="Personalized Roadmap", icon="🗺️"),
            st.Page("pages/14_Career_Coach.py", title="Career Coach", icon="💬"),
        ],
        "System": [
            st.Page("pages/15_Settings.py", title="Settings", icon="⚙️"),
        ]
    }

    # Admin Dashboard: only injected into nav if the logged-in user has role="admin" or email starts with "admin@"
    user = get_current_user()
    user_email = user.get("email", "") if user else ""
    is_admin = False
    if profile:
        is_admin = profile.get("role") == "admin"
    if not is_admin and user_email.startswith("admin@"):
        is_admin = True

    if is_admin:
        pages["System"].append(
            st.Page("pages/13_Admin_Dashboard.py", title="Admin Dashboard", icon="🛡️")
        )

    # Render Custom Sidebar structure
    with st.sidebar:
        # 1. Profile badge (at absolute top)
        if profile:
            render_sidebar_nav(profile)
        
        # 2. LLM selector (below profile badge, still at the top)
        render_ai_provider_selector()
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # 3. Custom navigation links grouped by category
        for category, page_list in pages.items():
            st.markdown(f"""
            <div style="
                color: var(--primary-light) !important;
                font-size: 0.72rem !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.1em !important;
                margin-top: 1rem !important;
                margin-bottom: 0.25rem !important;
                padding-left: 0.5rem !important;
                opacity: 0.8;
            ">{category}</div>
            """, unsafe_allow_html=True)
            for p in page_list:
                st.page_link(p, label=p.title, icon=p.icon)

        # 4. Sign-out at the bottom
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True, key="app_signout"):
            sign_out()
            st.rerun()

    # Render Streamlit Navigation
    pg = st.navigation(pages, position="hidden")
    if st.session_state.pop("redirect_to_admin", False):
        st.switch_page("pages/13_Admin_Dashboard.py")
    pg.run()
else:
    # Logged out state - only allow access to Login screen
    pg = st.navigation([st.Page("pages/login.py", title="Welcome", icon="🔐")], position="hidden")
    pg.run()
