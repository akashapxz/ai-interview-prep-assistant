"""
UI Components — Reusable Streamlit components with custom CSS.
Implements glassmorphism, animations, and premium design.
Supports both light and dark Streamlit themes via JS-based detection.
Uses Material Symbols Outlined icons instead of emojis for a professional look.
"""

import streamlit as st
from typing import Optional, List, Dict, Any


# ─────────────────────────────────────────────
# Material icon helper
# ─────────────────────────────────────────────

def mi(name: str, size: str = "1.25rem", color: str = "") -> str:
    """Return an inline Material Symbols Outlined icon span."""
    style = f"font-size:{size};vertical-align:middle;line-height:1;"
    if color:
        style += f"color:{color};"
    return f'<span class="material-symbols-outlined" style="{style}">{name}</span>'


# ─────────────────────────────────────────────
# Master CSS injection
# ─────────────────────────────────────────────

def inject_global_css():
    st.html("""
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet" />
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    :root {
        --primary: var(--primary-color, #6366f1);
        --primary-dark: var(--primary-color, #4f46e5);
        --primary-light: color-mix(in srgb, var(--primary) 75%, var(--text-color, #f1f5f9));
        --secondary: #8b5cf6;
        --accent: #06b6d4;
        --accent2: #a78bfa;
        
        /* Theme adaptive colors using color-mix and Streamlit variables */
        --bg-base: var(--background-color, #0a0a0f);
        --bg-card: var(--secondary-background-color, rgba(255,255,255,0.04));
        --bg-card-hover: color-mix(in srgb, var(--text-color, #ffffff) 4%, var(--secondary-background-color, rgba(255,255,255,0.04)));
        --bg-glass: rgba(99,102,241,0.08);
        --border: color-mix(in srgb, var(--text-color, #ffffff) 8%, transparent);
        --border-accent: rgba(99,102,241,0.4);
        
        --text-primary: var(--text-color, #f1f5f9);
        --text-secondary: color-mix(in srgb, var(--text-color, #f1f5f9) 70%, transparent);
        --text-muted: color-mix(in srgb, var(--text-color, #f1f5f9) 50%, transparent);
        --text-heading: var(--text-color, #f1f5f9);
        
        --success: #22c55e;
        --warning: #f59e0b;
        --danger: #ef4444;
        --radius: 16px;
        --radius-sm: 10px;
        --shadow: 0 8px 32px rgba(0,0,0,0.15);
        --shadow-accent: 0 0 30px rgba(99,102,241,0.2);
        --transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        --code-bg: color-mix(in srgb, var(--text-color, #ffffff) 5%, transparent);
        --sidebar-bg: var(--secondary-background-color, rgba(10,10,20,0.95));
        --divider: color-mix(in srgb, var(--text-color, #ffffff) 10%, transparent);
        --score-track: color-mix(in srgb, var(--text-color, #ffffff) 6%, transparent);
    }
    * { box-sizing: border-box; }
    html, body, [data-testid="stAppViewContainer"] {
        background: var(--bg-base) !important;
        font-family: 'Inter', sans-serif !important;
        color: var(--text-primary) !important;
    }
    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined' !important;
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
    [data-testid="stDecoration"] { display: none; }
    .viewerBadge_container__1QSob { display: none !important; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 99px; }
    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border) !important;
        backdrop-filter: blur(20px);
    }
    [data-testid="stSidebar"] > div { padding-top: 1rem; }
    .main .block-container {
        padding: 1.5rem 2rem 3rem !important;
        max-width: 1280px;
    }
    .stButton > button {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 1.4rem !important;
        transition: var(--transition) !important;
        box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99,102,241,0.5) !important;
        filter: brightness(1.1) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }
    .stButton > button[kind="secondary"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        box-shadow: none !important;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        transition: var(--transition) !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
        gap: 4px !important;
        padding: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        transition: var(--transition) !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: #fff !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
        border-radius: 99px !important;
    }
    .stSuccess { border-left: 4px solid var(--success) !important; background: rgba(34,197,94,0.1) !important; }
    .stError   { border-left: 4px solid var(--danger)  !important; background: rgba(239,68,68,0.1)  !important; }
    .stWarning { border-left: 4px solid var(--warning) !important; background: rgba(245,158,11,0.1) !important; }
    .stInfo    { border-left: 4px solid var(--accent)  !important; background: rgba(6,182,212,0.1)  !important; }
    .stSpinner > div { border-top-color: var(--primary) !important; }
    [data-testid="stFileUploader"] > div {
        background: var(--bg-glass) !important;
        border: 2px dashed var(--border-accent) !important;
        border-radius: var(--radius) !important;
        transition: var(--transition) !important;
    }
    [data-testid="stFileUploader"] > div:hover {
        border-color: var(--primary) !important;
        background: rgba(99,102,241,0.1) !important;
    }
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
        background: var(--code-bg) !important;
        border-radius: 8px !important;
    }
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1rem !important;
        transition: var(--transition) !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: var(--border-accent) !important;
        background: var(--bg-card-hover) !important;
    }
    [data-testid="stMetricValue"] { color: var(--primary-light) !important; font-weight: 700 !important; }
    [data-testid="stMetricDelta"] { font-size: 0.8rem !important; }
    [data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }
    @keyframes fadeInUp {
        from { opacity:0; transform:translateY(20px); }
        to   { opacity:1; transform:translateY(0); }
    }
    @keyframes pulse-glow {
        0%,100% { box-shadow: 0 0 15px rgba(99,102,241,0.3); }
        50%      { box-shadow: 0 0 35px rgba(99,102,241,0.6); }
    }
    @keyframes shimmer {
        0%   { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    @keyframes spin-slow { to { transform: rotate(360deg); } }
    .animate-fade-in { animation: fadeInUp 0.5s ease forwards; }
    .animate-pulse-glow { animation: pulse-glow 2s infinite; }
    </style>
    <script>
    (function(){
        function detectTheme(){
            var el = document.querySelector('[data-testid="stAppViewContainer"]');
            if(!el) return;
            var bg = getComputedStyle(el).backgroundColor;
            var m = bg.match(/(\\d+)/g);
            if(m && m.length >= 3){
                var lum = (parseInt(m[0])*299 + parseInt(m[1])*587 + parseInt(m[2])*114)/1000;
                document.documentElement.setAttribute('data-theme', lum > 128 ? 'light' : 'dark');
            }
        }
        new MutationObserver(detectTheme).observe(document.body, {attributes:true,childList:true,subtree:true});
        setTimeout(detectTheme, 200);
        setTimeout(detectTheme, 1000);
    })();
    </script>
    """)


# ─────────────────────────────────────────────
# Card components
# ─────────────────────────────────────────────

def glass_card(content: str, padding: str = "1.5rem", border_accent: bool = False) -> None:
    border = "border: 1px solid var(--border-accent);" if border_accent else "border: 1px solid var(--border);"
    st.markdown(f"""
    <div style="
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 16px;
        {border}
        padding: {padding};
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        animation: fadeInUp 0.5s ease;
    ">{content}</div>
    """, unsafe_allow_html=True)


def kpi_card(icon: str, title: str, value: str, subtitle: str = "", color: str = "#6366f1") -> str:
    """Render a KPI stat card. `icon` should be a Material Symbols icon name."""
    return f"""
    <div style="
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    ">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,{color},{color}88);"></div>
        <div style="margin-bottom:0.4rem;">{mi(icon, "2rem", color)}</div>
        <div style="font-size:1.8rem;font-weight:800;color:{color};line-height:1;">{value}</div>
        <div style="font-size:0.85rem;color:var(--text-secondary);margin-top:0.3rem;font-weight:500;">{title}</div>
        {f'<div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.2rem;">{subtitle}</div>' if subtitle else ''}
    </div>
    """


def score_ring(score: float, label: str, size: int = 120) -> str:
    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
    pct = score / 100
    circumference = 2 * 3.14159 * 45
    offset = circumference * (1 - pct)
    return f'<div style="text-align:center;display:inline-block;"><svg width="{size}" height="{size}" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="none" stroke="var(--score-track)" stroke-width="8"/><circle cx="50" cy="50" r="45" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}" transform="rotate(-90 50 50)" style="transition:stroke-dashoffset 1s ease;"/><text x="50" y="46" text-anchor="middle" fill="{color}" font-size="18" font-weight="bold" font-family="Inter">{score:.0f}</text><text x="50" y="62" text-anchor="middle" fill="var(--text-secondary)" font-size="9" font-family="Inter">/ 100</text></svg><div style="color:var(--text-secondary);font-size:0.8rem;margin-top:0.25rem;font-weight:500;">{label}</div></div>'


def badge(text: str, color: str = "#6366f1", bg_opacity: float = 0.15) -> str:
    return f"""<span style="
        background: {color}{int(bg_opacity*255):02x};
        color: {color};
        border: 1px solid {color}44;
        border-radius: 99px;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        font-family: Inter, sans-serif;
        margin: 2px;
        display: inline-block;
    ">{text}</span>"""


def difficulty_badge(difficulty: str) -> str:
    colors = {"easy": "#22c55e", "medium": "#f59e0b", "hard": "#ef4444"}
    icons = {"easy": "check_circle", "medium": "warning", "hard": "error"}
    c = colors.get(difficulty.lower(), "#94a3b8")
    i = icons.get(difficulty.lower(), "help")
    return badge(f'{mi(i, "0.85rem", c)} {difficulty.capitalize()}', c)


def page_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a page header. `icon` should be a Material Symbols icon name."""
    icon_html = f'{mi(icon, "2rem", "var(--primary-light)")}' if icon else ''
    st.markdown(f"""
    <div style="margin-bottom:2rem;animation:fadeInUp 0.6s ease;">
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.4rem;">
            {icon_html}
            <h1 style="
                font-size:clamp(1.6rem,3vw,2.2rem);
                font-weight:800;
                background:linear-gradient(135deg, var(--text-heading), var(--primary));
                -webkit-background-clip:text;
                -webkit-text-fill-color:transparent;
                margin:0;line-height:1.2;
            ">{title}</h1>
        </div>
        {f'<p style="color:var(--text-secondary);font-size:1rem;margin:0;">{subtitle}</p>' if subtitle else ''}
        <div style="height:2px;background:linear-gradient(90deg,#6366f1,#8b5cf6,transparent);margin-top:0.75rem;border-radius:99px;"></div>
    </div>
    """, unsafe_allow_html=True)


def loading_skeleton(lines: int = 3):
    for _ in range(lines):
        st.markdown("""
        <div style="
            height:20px;border-radius:8px;margin-bottom:8px;
            background:linear-gradient(90deg, var(--bg-card) 25%, var(--bg-card-hover) 50%, var(--bg-card) 75%);
            background-size:200% 100%;
            animation:shimmer 1.5s infinite;
        "></div>""", unsafe_allow_html=True)


def empty_state(icon: str, title: str, description: str, action: str = ""):
    """Render an empty state placeholder. `icon` should be a Material Symbols icon name."""
    st.markdown(f"""
    <div style="text-align:center;padding:3rem 2rem;animation:fadeInUp 0.5s ease;">
        <div style="margin-bottom:1rem;">{mi(icon, "4rem", "var(--text-muted)")}</div>
        <h3 style="color:var(--text-primary);font-weight:700;margin-bottom:0.5rem;">{title}</h3>
        <p style="color:var(--text-secondary);max-width:400px;margin:0 auto;">{description}</p>
        {f'<p style="color:var(--primary);margin-top:1rem;font-weight:600;">{action}</p>' if action else ''}
    </div>
    """, unsafe_allow_html=True)


def success_banner(message: str, icon: str = "check_circle"):
    """Render a success banner. `icon` should be a Material Symbols icon name."""
    st.markdown(f"""
    <div style="
        background:linear-gradient(135deg,rgba(34,197,94,0.15),rgba(16,185,129,0.1));
        border:1px solid rgba(34,197,94,0.3);
        border-radius:12px;padding:1rem 1.25rem;
        display:flex;align-items:center;gap:0.75rem;
        animation:fadeInUp 0.4s ease;
    ">
        {mi(icon, "1.5rem", "#4ade80")}
        <span style="color:#4ade80;font-weight:600;">{message}</span>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_nav(profile: Dict):
    """Render the animated sidebar navigation."""
    name = profile.get("full_name", "User") if profile else "User"
    xp = profile.get("xp_points", 0) if profile else 0
    streak = profile.get("streak_days", 0) if profile else 0
    avatar_char = name[0].upper() if name else "U"

    st.sidebar.markdown(f"""
    <div style="padding:1rem;margin-bottom:1rem;">
        <div style="
            background:linear-gradient(135deg,rgba(99,102,241,0.2),rgba(139,92,246,0.2));
            border:1px solid rgba(99,102,241,0.3);
            border-radius:16px;padding:1rem;text-align:center;
        ">
            <div style="
                width:56px;height:56px;border-radius:50%;
                background:linear-gradient(135deg,#6366f1,#8b5cf6);
                display:flex;align-items:center;justify-content:center;
                font-size:1.4rem;font-weight:800;color:white;
                margin:0 auto 0.6rem;
                box-shadow:0 0 20px rgba(99,102,241,0.4);
            ">{avatar_char}</div>
            <div style="color:var(--text-primary);font-weight:700;font-size:0.95rem;">{name}</div>
            <div style="display:flex;justify-content:center;gap:1rem;margin-top:0.6rem;">
                <div style="text-align:center;">
                    <div style="color:#6366f1;font-weight:700;font-size:1rem;">{xp:,}</div>
                    <div style="color:var(--text-muted);font-size:0.7rem;">XP</div>
                </div>
                <div style="width:1px;background:var(--divider);"></div>
                <div style="text-align:center;">
                    <div style="color:#f59e0b;font-weight:700;font-size:1rem;">{mi("local_fire_department","1rem","#f59e0b")} {streak}</div>
                    <div style="color:var(--text-muted);font-size:0.7rem;">Streak</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_ai_provider_selector():
    """Sidebar widget to switch between AI providers."""
    st.sidebar.markdown(f"""
    <div style="padding:0 0.25rem 0.4rem;">
        <div style="
            background:var(--bg-glass);
            border:1px solid rgba(99,102,241,0.2);
            border-radius:12px;
            padding:0.6rem 0.85rem 0.5rem;
        ">
            <div style="color:var(--text-muted);font-size:0.68rem;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.35rem;">
                {mi("smart_toy","0.85rem","var(--text-muted)")} AI Engine
            </div>
    """, unsafe_allow_html=True)
    provider = st.sidebar.selectbox(
        "AI Model",
        ["gemini", "groq", "openai", "anthropic", "openrouter"],
        format_func=lambda x: {
            "gemini": "Gemini 2.5 Flash",
            "groq": "Groq · Llama 3.3",
            "openai": "OpenAI · GPT-4o Mini",
            "anthropic": "Claude 3.5 Sonnet",
            "openrouter": "OpenRouter · Llama 3.3"
        }.get(x, x),
        key="ai_provider",
        label_visibility="collapsed",
    )
    st.sidebar.markdown("</div></div>", unsafe_allow_html=True)
    return provider


def feedback_card(score: float, feedback: str, model_answer: Optional[str] = None):
    """Show AI evaluation feedback with styled card."""
    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
    grade_icon = "emoji_events" if score >= 90 else "star" if score >= 75 else "thumb_up" if score >= 60 else "trending_up"

    st.markdown(f"""
    <div style="
        background:var(--bg-card);
        border:1px solid {color}44;
        border-left:4px solid {color};
        border-radius:12px;
        padding:1.25rem;
        margin:1rem 0;
        animation:fadeInUp 0.5s ease;
    ">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
            <span style="color:{color};font-size:1.4rem;font-weight:800;">{mi(grade_icon,"1.4rem",color)} {score:.0f}/100</span>
            <span style="color:var(--text-secondary);font-size:0.8rem;">AI Evaluation</span>
        </div>
        <p style="color:var(--text-primary);margin:0;line-height:1.6;">{feedback}</p>
    </div>
    """, unsafe_allow_html=True)

    if model_answer:
        with st.expander("View Model Answer"):
            st.markdown(f'<div style="color:var(--text-primary);line-height:1.7;">{model_answer}</div>', unsafe_allow_html=True)
