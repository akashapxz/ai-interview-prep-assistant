"""
Login / Welcome Page — AI Interview Prep Assistant.
Premium split-panel design: branded left panel + clean auth form on the right.
Uses clean_html to strip all indentation from HTML lines, preventing Markdown code block escaping.
Uses pure CSS to style the columns and tabs card to avoid breaking the DOM tree.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import sign_in, sign_up, reset_password, get_google_oauth_url
from src.components.ui_components import inject_global_css

# Inject global styles
inject_global_css()

# Temporary Developer Debugger for OAuth/Session troubleshooting
if st.checkbox("🛠️ Auth Debugger (Developer Mode)", value=True, key="auth_dev_debugger"):
    st.json({
        "authenticated": st.session_state.get("authenticated"),
        "user": st.session_state.get("user"),
        "query_params": dict(st.query_params),
        "cookies": dict(st.context.cookies)
    })
    st.write("**Auth Flow Progress Logs:**")
    logs = st.session_state.get("auth_debug_logs", [])
    if not logs:
        st.write("*No flow logs recorded yet. Click 'Continue with Google' to start.*")
    for log_msg in logs:
        st.write(f"- {log_msg}")


def clean_html(html_str: str) -> str:
    """Strip all leading/trailing whitespace from each line to prevent Markdown code-block escaping."""
    return "\n".join(line.strip() for line in html_str.splitlines())


# ── Extra premium login-page CSS ──────────────────────────────────────────────
st.markdown(clean_html("""
<style>
/* Full-page hero gradient background */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 50% 15%, rgba(99,102,241,0.15) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 80%, rgba(6,182,212,0.06) 0%, transparent 50%),
                #0a0a0f !important;
}

/* Hide sidebar on login page */
[data-testid="stSidebar"] { display: none !important; }

/* Center and pad the main block container */
.main .block-container {
    padding: 3rem 1.5rem !important;
    max-width: 850px !important;
    margin: 0 auto !important;
}

/* Centered styling container */
.login-header-container {
    text-align: center;
    margin: 0 auto 2.5rem;
    max-width: 650px;
    animation: fadeInUp 0.5s ease;
}

/* Style the tabs container as the premium card */
.stTabs {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 24px !important;
    padding: 2.5rem !important;
    width: 100% !important;
    max-width: 500px !important;
    margin: 0 auto !important;
    box-shadow: 0 25px 60px rgba(0,0,0,0.5) !important;
    backdrop-filter: blur(20px) !important;
    animation: fadeInUp 0.7s ease;
}

/* Tab labels adjustment to be slightly bigger */
.stTabs [data-baseweb="tab"] {
    font-size: 1rem !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
}

/* Auth tab strip */
.auth-tab-strip [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    padding: 4px !important;
    gap: 4px !important;
}
.auth-tab-strip [aria-selected="true"] {
    background: linear-gradient(135deg,#6366f1,#8b5cf6) !important;
    color: #fff !important;
}

/* Input label colour */
label { color: #94a3b8 !important; font-size: 0.85rem !important; font-weight: 500 !important; }

/* Remove red borders from required inputs */
.stTextInput > div > div > input { border-color: rgba(255,255,255,0.1) !important; }
</style>
"""), unsafe_allow_html=True)


# ── Centered Branding & Features ─────────────────────────────────────────────
st.markdown(clean_html("""
    <div class="login-header-container">
        <!-- Logo pill -->
        <div style="
            display:inline-flex;align-items:center;gap:0.6rem;
            background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.3);
            border-radius:99px;padding:0.55rem 1.4rem;margin-bottom:2rem;
            font-size:0.92rem;color:#818cf8;font-weight:600;width:fit-content;
            backdrop-filter: blur(10px);
        ">
            🎯 &nbsp;AI Interview Prep
        </div>

        <!-- Hero heading -->
        <h1 style="
            font-size:clamp(2.2rem, 5vw, 3.4rem);font-weight:900;
            line-height:1.15;margin:0 auto 1.2rem;text-align:center;
            background:linear-gradient(135deg,#f1f5f9 0%,#a5b4fc 55%,#38bdf8 100%);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        ">
            Ace Every Interview with AI
        </h1>

        <p style="color:#94a3b8;font-size:1.1rem;line-height:1.65;margin:0 auto 2.5rem;max-width:560px;text-align:center;">
            The most advanced AI platform for interview preparation — mock interviews, resume analysis, coding practice, and personalised learning.
        </p>

        <!-- Feature pills grid -->
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
            text-align: left;
            width: 100%;
        ">
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:0.85rem 1rem;display:flex;align-items:center;gap:0.75rem;">
                <div style="width:34px;height:34px;border-radius:8px;background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🤖</div>
                <div>
                    <div style="color:#f1f5f9;font-size:0.88rem;font-weight:600;">AI Mock Interviews</div>
                    <div style="color:#64748b;font-size:0.75rem;">Realistic FAANG, HR & tech sessions</div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:0.85rem 1rem;display:flex;align-items:center;gap:0.75rem;">
                <div style="width:34px;height:34px;border-radius:8px;background:rgba(6,182,212,0.12);border:1px solid rgba(6,182,212,0.25);display:flex;align-items:center;justify-content:center;font-size:1.1rem;">📄</div>
                <div>
                    <div style="color:#f1f5f9;font-size:0.88rem;font-weight:600;">Resume Analyzer</div>
                    <div style="color:#64748b;font-size:0.75rem;">ATS scoring & feedback tips</div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:0.85rem 1rem;display:flex;align-items:center;gap:0.75rem;">
                <div style="width:34px;height:34px;border-radius:8px;background:rgba(139,92,246,0.12);border:1px solid rgba(139,92,246,0.25);display:flex;align-items:center;justify-content:center;font-size:1.1rem;">💻</div>
                <div>
                    <div style="color:#f1f5f9;font-size:0.88rem;font-weight:600;">Coding Practice</div>
                    <div style="color:#64748b;font-size:0.75rem;">LeetCode challenges with AI grading</div>
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:0.85rem 1rem;display:flex;align-items:center;gap:0.75rem;">
                <div style="width:34px;height:34px;border-radius:8px;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.25);display:flex;align-items:center;justify-content:center;font-size:1.1rem;">🎙️</div>
                <div>
                    <div style="color:#f1f5f9;font-size:0.88rem;font-weight:600;">Voice Interviews</div>
                    <div style="color:#64748b;font-size:0.75rem;">Speech analysis & filler-word detection</div>
                </div>
            </div>
        </div>
    </div>
"""), unsafe_allow_html=True)


# ── Auth Form Card ───────────────────────────────────────────────────────────
# Header above the card
st.markdown(clean_html("""
    <div style="text-align:center;margin-bottom:1.5rem;width:100%;">
        <div style="font-size:2.5rem;margin-bottom:0.4rem;">🔐</div>
        <div style="color:#f1f5f9;font-size:1.35rem;font-weight:700;">Welcome back</div>
        <div style="color:#64748b;font-size:0.88rem;margin-top:0.2rem;">Sign in to continue your prep journey</div>
    </div>
"""), unsafe_allow_html=True)

# Tabs (styled directly as the card using CSS .stTabs rule)
tab_login, tab_signup, tab_reset = st.tabs(["🔐 Login", "✨ Sign Up", "🔑 Reset"])

# ── LOGIN ──────────────────────────────────────────────────────────────────
with tab_login:
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    email = st.text_input("Email address", placeholder="you@example.com", key="login_email")
    password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")

    col_rem, col_forgot = st.columns(2)
    with col_rem:
        remember = st.checkbox("Remember me", key="login_remember")

    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    if st.button("🚀 Sign In", use_container_width=True, key="btn_login", type="primary"):
        if not email or not password:
            st.error("Please fill in both fields.")
        else:
            with st.spinner("Authenticating…"):
                success, msg = sign_in(email, password, remember)
            if success:
                st.success(msg)
                if email.strip().lower() == "admin@gmail.com":
                    st.session_state["redirect_to_admin"] = True
                st.rerun()
            else:
                st.error(msg)

    st.markdown("<div style='text-align:center;color:#475569;font-size:0.8rem;margin:0.9rem 0;'>— or continue with —</div>", unsafe_allow_html=True)
    # Pre-generate the URL and PKCE code verifier on page load
    url, code_verifier = get_google_oauth_url()
    
    if url:
        # Set the cookie immediately on load so it's ready when the button is clicked
        if code_verifier:
            import time
            st.markdown(f'<img src="cookie-set-{time.time()}" onerror="document.cookie=\'pkce_code_verifier={code_verifier}; path=/; max-age=300; SameSite=Lax\';" style="display:none;"/>', unsafe_allow_html=True)

        if st.button("🔵 Continue with Google", use_container_width=True, key="google_login_btn"):
            st.session_state["oauth_redirect_url"] = url
            st.rerun()
            
        if "oauth_redirect_url" in st.session_state:
            redirect_url = st.session_state.pop("oauth_redirect_url")
            st.components.v1.html(f"""
                <script type="text/javascript">
                    window.top.location.href = "{redirect_url}";
                </script>
            """, height=0)
            st.info("🔄 Redirecting to Google...")
    else:
        st.warning("Google OAuth not configured. Add GOOGLE_CLIENT_ID to .env")

# ── SIGNUP ─────────────────────────────────────────────────────────────────
with tab_signup:
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    full_name = st.text_input("Full Name", placeholder="John Doe", key="su_name")
    su_email = st.text_input("Email", placeholder="you@example.com", key="su_email")

    pc1, pc2 = st.columns(2)
    with pc1:
        su_pass = st.text_input("Password", type="password", placeholder="Min 8 chars", key="su_pass")
    with pc2:
        su_pass2 = st.text_input("Confirm", type="password", placeholder="Repeat", key="su_pass2")

    dc1, dc2 = st.columns(2)
    with dc1:
        college = st.text_input("College / University", placeholder="MIT", key="su_college")
    with dc2:
        branch = st.text_input("Branch / Major", placeholder="Computer Science", key="su_branch")

    grad_year = st.number_input("Graduation Year", min_value=2020, max_value=2032, value=2025, key="su_year")

    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
    if st.button("🎯 Create Account", use_container_width=True, key="btn_signup", type="primary"):
        if not all([full_name, su_email, su_pass, college, branch]):
            st.error("Please fill in all required fields.")
        elif su_pass != su_pass2:
            st.error("Passwords do not match.")
        elif len(su_pass) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            with st.spinner("Creating your account…"):
                success, msg = sign_up(su_email, su_pass, full_name, college, branch, grad_year)
            if success:
                st.success(msg)
                st.info("📧 Check your email to verify your account, then log in.")
            else:
                st.error(msg)

# ── PASSWORD RESET ─────────────────────────────────────────────────────────
with tab_reset:
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;font-size:0.85rem;margin-bottom:1rem;'>Enter your email and we'll send a link to reset your password.</p>", unsafe_allow_html=True)
    reset_email = st.text_input("Email address", placeholder="your@email.com", key="reset_email")
    if st.button("📧 Send Reset Link", use_container_width=True, key="btn_reset", type="primary"):
        if not reset_email:
            st.error("Please enter your email address.")
        else:
            with st.spinner("Sending reset email…"):
                success, msg = reset_password(reset_email)
            if success:
                st.success(msg)
            else:
                st.error(msg)

# Footer note below the card
st.markdown(clean_html("""
    <div style="text-align:center;margin-top:1.5rem;color:#334155;font-size:0.75rem;width:100%;">
        By signing up you agree to our Terms of Service &amp; Privacy Policy
    </div>
"""), unsafe_allow_html=True)
