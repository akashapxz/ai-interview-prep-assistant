"""
Page 08 — Company-Specific Interview Preparation
Google, Amazon, Microsoft, Meta, and more — company-tailored questions with readiness scores.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, kpi_card,
    render_sidebar_nav, render_ai_provider_selector, empty_state
)
from src.database.supabase_client import db_insert, db_select, db_upsert, award_xp
from src.ai.gemini_client import generate_company_questions, evaluate_technical_answer
from src.utils.helpers import COMPANIES

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("Company-Specific Prep", "Targeted interview preparation for top tech companies", "domain")

# Company logos/colors
COMPANY_META = {
    "Google": {"color": "#4285F4", "icon": "radio_button_checked", "culture": "Innovation, scale, data-driven"},
    "Amazon": {"color": "#FF9900", "icon": "radio_button_checked", "culture": "Leadership Principles, customer obsession"},
    "Microsoft": {"color": "#00A4EF", "icon": "🪟", "culture": "Growth mindset, cloud-first"},
    "Meta": {"color": "#1877F2", "icon": "🔷", "culture": "Move fast, build social impact"},
    "Apple": {"color": "#555555", "icon": "🍎", "culture": "Design excellence, privacy focus"},
    "Netflix": {"color": "#E50914", "icon": "🎬", "culture": "Freedom and responsibility"},
    "Infosys": {"color": "#007CC3", "icon": "🏗️", "culture": "Learning agility, collaboration"},
    "TCS": {"color": "#1B3A6B", "icon": "🏛️", "culture": "Customer satisfaction, integrity"},
    "Wipro": {"color": "#341C75", "icon": "work", "culture": "Innovation, inclusion"},
    "Accenture": {"color": "#A100FF", "icon": "🔮", "culture": "Technology-led transformation"},
}

# Company selection grid
st.markdown("### 🏢 Select Your Target Company")
company_cols = st.columns(5)
selected_company = st.session_state.get("selected_company", "Google")

for i, company in enumerate(COMPANIES[:10]):
    meta = COMPANY_META.get(company, {"color": "#6366f1", "icon": "domain", "culture": ""})
    with company_cols[i % 5]:
        is_selected = selected_company == company
        if st.button(
            f"{meta['icon']} {company}",
            use_container_width=True,
            key=f"company_btn_{company}",
            type="primary" if is_selected else "secondary"
        ):
            st.session_state["selected_company"] = company
            st.session_state.pop("company_questions", None)
            st.rerun()

# Company overview
selected_company = st.session_state.get("selected_company", "Google")
meta = COMPANY_META.get(selected_company, {"color": "#6366f1", "icon": "domain", "culture": ""})

st.markdown(f"""
<div style="background:var(--bg-card);border:1px solid {meta['color']}33;
     border-left:4px solid {meta['color']};border-radius:14px;
     padding:1.25rem;margin:1rem 0;">
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem;">
        <span style="font-size:2rem;">{meta['icon']}</span>
        <span style="color:var(--text-primary);font-size:1.2rem;font-weight:700;">{selected_company}</span>
    </div>
    <div style="color:var(--text-secondary);font-size:0.9rem;">Culture: {meta['culture']}</div>
</div>
""", unsafe_allow_html=True)

# Readiness for this company
company_prep = db_select("company_preparation", {"user_id": user_id, "company_name": selected_company}, limit=1)
readiness = company_prep[0].get("readiness_score", 0) if company_prep else 0
sessions = company_prep[0].get("sessions_completed", 0) if company_prep else 0

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(kpi_card("gps_fixed", f"{selected_company} Readiness", f"{readiness}%", "overall score", meta["color"]), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("📚", "Sessions Done", str(sessions), "practice sessions", "#06b6d4"), unsafe_allow_html=True)
with c3:
    remaining = max(0, 80 - readiness)
    st.markdown(kpi_card("trending_up", "To Interview Ready", f"{remaining}%", "to 80% readiness", "#22c55e"), unsafe_allow_html=True)

# Readiness progress bar
st.markdown(f"""
<div style="margin:0.5rem 0 1.5rem;">
    <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
        <span style="color:var(--text-secondary);font-size:0.85rem;">{selected_company} Readiness</span>
        <span style="color:{meta['color']};font-weight:700;">{readiness}%</span>
    </div>
    <div style="height:10px;background:rgba(255,255,255,0.08);border-radius:99px;overflow:hidden;">
        <div style="width:{readiness}%;height:100%;background:{meta['color']};border-radius:99px;transition:width 1s ease;"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Configuration
st.markdown("### ⚙️ Generate Company Questions")
cfg1, cfg2, cfg3 = st.columns(3)
with cfg1:
    categories = st.multiselect(
        "Question Categories",
        ["Technical", "System Design", "Leadership Principle", "HR", "Behavioral"],
        default=["Technical", "HR"],
        key="company_cats"
    )
with cfg2:
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard", "Mixed"], index=2, key="company_diff")
with cfg3:
    role_type = st.selectbox("Role Type", ["Software Engineer", "Data Engineer", "ML Engineer", "Product Manager", "Data Analyst"], key="company_role")

q_count = st.slider("Number of Questions", 5, 15, 8, key="company_q_count")

if st.button(f"🚀 Generate {selected_company} Questions", type="primary", use_container_width=True, key="gen_company_btn"):
    cats_str = ", ".join(categories)
    with st.spinner(f"🤖 Generating {selected_company}-specific questions..."):
        result = generate_company_questions(
            company=selected_company,
            categories=cats_str,
            difficulty=difficulty.lower(),
            role_type=role_type,
            count=q_count,
        )
    if result and result.get("questions"):
        st.session_state["company_questions"] = result
        # Update company prep record
        new_readiness = min(100, readiness + 5)
        db_upsert("company_preparation", {
            "user_id": user_id,
            "company_name": selected_company,
            "readiness_score": new_readiness,
            "sessions_completed": sessions + 1,
            "last_practiced_at": "now()",
        })
        award_xp(user_id, 30)
        st.success(f"✅ Generated {len(result['questions'])} {selected_company}-specific questions!")
    else:
        st.error("Failed to generate questions. Please try again.")

# ── Questions Display ─────────────────────────────────────────────────────────
company_data = st.session_state.get("company_questions")

if company_data:
    questions = company_data.get("questions", [])
    interview_overview = company_data.get("interview_overview", "")
    company_values = company_data.get("company_values", [])
    interview_tips = company_data.get("interview_tips", [])

    if interview_overview:
        st.markdown(f"""
        <div style="background:var(--bg-card);border-radius:12px;padding:1rem;margin-bottom:1rem;">
            <div style="color:#818cf8;font-size:0.85rem;font-weight:600;margin-bottom:0.3rem;">INTERVIEW OVERVIEW</div>
            <div style="color:var(--text-primary);line-height:1.65;">{interview_overview}</div>
        </div>
        """, unsafe_allow_html=True)

    # Values and Tips
    col_vals, col_tips = st.columns(2)
    with col_vals:
        if company_values:
            st.markdown(f"**{selected_company} Core Values:**")
            for val in company_values:
                st.markdown(f'<span style="background:{meta["color"]}22;color:{meta["color"]};border:1px solid {meta["color"]}44;border-radius:99px;padding:0.2rem 0.75rem;font-size:0.8rem;margin:2px;display:inline-block;">{val}</span>', unsafe_allow_html=True)

    with col_tips:
        if interview_tips:
            with st.expander(f"💡 {selected_company} Interview Tips"):
                for tip in interview_tips:
                    st.markdown(f"• {tip}")

    st.markdown(f"---\n### 📋 {len(questions)} {selected_company} Interview Questions")
    evaluations = st.session_state.setdefault("company_evaluations", {})

    for i, q in enumerate(questions):
        category = q.get("category", "technical")
        cat_colors = {"technical": "#06b6d4", "hr": "#8b5cf6", "system_design": "#f59e0b",
                      "leadership_principle": "#22c55e", "behavioral": "#a78bfa"}
        cat_color = cat_colors.get(category.lower().replace(" ", "_"), "#6366f1")

        st.markdown(f"""
        <div style="background:var(--bg-card);border:1px solid var(--border);
             border-radius:14px;padding:1.25rem;margin-bottom:0.5rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
                <span style="background:{meta['color']};color:#fff;border-radius:8px;padding:0.2rem 0.6rem;font-size:0.75rem;font-weight:700;">{meta['icon']} Q{i+1}</span>
                <span style="background:{cat_color}22;color:{cat_color};border:1px solid {cat_color}44;border-radius:99px;padding:0.2rem 0.75rem;font-size:0.75rem;font-weight:600;">{category.replace('_',' ').title()}</span>
            </div>
            <div style="color:var(--text-primary);font-size:0.95rem;line-height:1.65;margin-bottom:0.5rem;">{q.get('question','')}</div>
            {f'<div style="color:var(--text-muted);font-size:0.8rem;border-top:1px solid rgba(255,255,255,0.06);padding-top:0.5rem;margin-top:0.5rem;">💡 {q.get("tips","")}</div>' if q.get('tips') else ''}
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"📝 Answer Q{i+1} & Get Feedback"):
            if q.get("company_context"):
                st.markdown(f'<div style="color:var(--text-muted);font-size:0.82rem;margin-bottom:0.5rem;">🏢 Why {selected_company} asks this: {q["company_context"]}</div>', unsafe_allow_html=True)
            if q.get("evaluation_criteria"):
                st.markdown(f'<div style="color:#818cf8;font-size:0.82rem;margin-bottom:0.75rem;">🎯 {selected_company} looks for: {q["evaluation_criteria"]}</div>', unsafe_allow_html=True)

            ans = st.text_area("Your Answer", key=f"comp_ans_{i}", height=120, placeholder="Structure your answer...")
            if st.button(f"🤖 Evaluate", key=f"eval_comp_{i}") and ans.strip():
                with st.spinner("Evaluating..."):
                    ev = evaluate_technical_answer(q.get("question", ""), ans, selected_company, difficulty.lower())
                if ev:
                    evaluations[i] = ev
                    score = ev.get("overall_score", 0)
                    color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                    st.markdown(f'<div style="color:{color};font-weight:700;">{score:.0f}/100 — {ev.get("feedback","")}</div>', unsafe_allow_html=True)
                    if ev.get("model_answer"):
                        st.info(f"💡 Model Answer: {ev['model_answer'][:300]}")
else:
    if not st.session_state.get("selected_company"):
        empty_state("domain", "Select a Company", "Click on any company above to start company-specific preparation!")
