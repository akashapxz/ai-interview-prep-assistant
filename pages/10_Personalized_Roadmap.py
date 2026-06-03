"""
Page 10 — Personalized Learning Roadmap
Analyzes performance history, weak areas, and generates weekly study guides/roadmaps.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, timedelta
from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, kpi_card,
    render_sidebar_nav, render_ai_provider_selector, empty_state, glass_card
)
from src.database.supabase_client import db_insert, db_select, db_upsert, get_performance_history, award_xp
from src.ai.gemini_client import generate_learning_roadmap
from src.utils.helpers import COMPANIES

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("Personalized Learning Engine", "AI-generated weekly roadmap and daily challenges to target your weak areas", "map")

# ── Fetch Past Data to Feed AI Roadmap ──────────────────────────────────────────
performance = get_performance_history(user_id, days=30)
interviews = db_select("interviews", {"user_id": user_id, "status": "completed"})
coding = db_select("coding_sessions", {"user_id": user_id})

# Aggregate info
total_interviews = len(interviews)
avg_technical = round(sum(i.get("technical_score", 0) for i in interviews) / max(total_interviews, 1), 1)
avg_hr = round(sum(i.get("hr_score", 0) for i in interviews) / max(total_interviews, 1), 1)

# Group domain scores to find weak/strong areas
domain_scores = {}
for iv in interviews:
    domain = iv.get("domain")
    if domain:
        domain_scores.setdefault(domain, []).append(iv.get("overall_score", 0))

weak_list = [d for d, s in domain_scores.items() if sum(s)/len(s) < 70]
strong_list = [d for d, s in domain_scores.items() if sum(s)/len(s) >= 70]

# Add fallback if no practice data yet
if not weak_list and not strong_list:
    weak_list = ["DBMS", "DSA"]
    strong_list = ["OOP"]

weak_areas = ", ".join(weak_list)
strong_areas = ", ".join(strong_list)

# ── Roadmap Generator Configuration ───────────────────────────────────────────
st.markdown("### 🛠️ Configure Your Learning Roadmap")
cfg1, cfg2, cfg3 = st.columns(3)
with cfg1:
    # Load user target companies from preferences if set
    pref_rows = db_select("company_preparation", {"user_id": user_id, "company_name": "__user_preferences__"})
    saved_prefs = pref_rows[0].get("metadata", {}) if pref_rows else {}
    default_companies = saved_prefs.get("target_companies", ["Google", "Amazon"])
    # filter to make sure default companies exist in COMPANIES list
    default_companies = [c for c in default_companies if c in COMPANIES]
    if not default_companies:
        default_companies = ["Google", "Amazon"]
    target_companies = st.multiselect("Target Companies", COMPANIES, default=default_companies, key="rm_companies")
with cfg2:
    weeks = st.slider("Duration (Weeks)", 2, 12, 4, key="rm_weeks")
with cfg3:
    habit_count = st.slider("Daily Habits Count", 2, 5, 3, key="rm_habits")

if st.button("🗺️ Generate Personalized Roadmap", type="primary", use_container_width=True, key="btn_gen_roadmap"):
    comp_str = ", ".join(target_companies) if target_companies else "General Tech"
    history_summary = f"Completed {total_interviews} mock interviews and solved {len(coding)} coding problems."
    
    with st.spinner("🤖 AI is analyzing your performance and building a tailored roadmap..."):
        roadmap_data = generate_learning_roadmap(
            name=profile.get("full_name", "Student") if profile else "Student",
            branch=profile.get("branch", "Computer Science") if profile else "Computer Science",
            weak_areas=weak_areas,
            strong_areas=strong_areas,
            tech_score=avg_technical,
            hr_score=avg_hr,
            companies=comp_str,
            weeks=weeks,
            history_summary=history_summary,
        )
    
    if roadmap_data:
        st.session_state["learning_roadmap"] = roadmap_data
        # Save to DB
        db_insert("recommendations", {
            "user_id": user_id,
            "roadmap": roadmap_data.get("weekly_plan", []),
            "weak_areas": weak_list,
            "focus_topics": roadmap_data.get("priority_areas", []),
            "weekly_goals": roadmap_data.get("daily_habits", []),
            "readiness_score": roadmap_data.get("readiness_score", 0),
            "is_active": True,
        })
        award_xp(user_id, 50)
        st.success("✅ Roadmap generated successfully!")
    else:
        st.error("Failed to generate learning roadmap. Please check configuration and try again.")

# ── Roadmap Display ───────────────────────────────────────────────────────────
roadmap_state = db_select("recommendations", {"user_id": user_id, "is_active": True}, order="generated_at.desc", limit=1)
roadmap_data = roadmap_state[0] if roadmap_state else st.session_state.get("learning_roadmap")

if roadmap_data:
    st.markdown("---")
    
    # Overview
    r_score = roadmap_data.get("readiness_score", 0)
    color = "#22c55e" if r_score >= 80 else "#f59e0b" if r_score >= 60 else "#ef4444"
    
    col_ov1, col_ov2 = st.columns([1, 2])
    with col_ov1:
        st.markdown(kpi_card("gps_fixed", "Estimated Readiness Index", f"{r_score}%", "based on roadmap", color), unsafe_allow_html=True)
    with col_ov2:
        st.markdown("**Priority Focus Areas:**")
        p_areas = roadmap_data.get("focus_topics", [])
        if not p_areas and isinstance(roadmap_data.get("roadmap"), list):
            p_areas = [w.get("focus_topic", "") for w in roadmap_data.get("roadmap")]
        
        areas_html = " ".join(badge(area, "#6366f1") for area in p_areas if area)
        st.markdown(f'<div style="padding:0.5rem 0;">{areas_html}</div>', unsafe_allow_html=True)

    # Weekly Details
    st.markdown("### 📅 Weekly Plan")
    plan = roadmap_data.get("roadmap") or roadmap_data.get("weekly_plan") or []
    if plan:
        for idx, week in enumerate(plan):
            with st.expander(f"📅 Week {week.get('week', idx+1)}: {week.get('focus_topic', 'Topic')}", expanded=(idx==0)):
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.02);border-radius:12px;padding:1rem;margin-bottom:0.5rem;">
                    <div style="color:#818cf8;font-weight:700;font-size:0.9rem;margin-bottom:0.5rem;">⚡ Objective & Weekly Goals</div>
                    <div style="color:var(--text-primary);font-size:0.9rem;line-height:1.6;margin-bottom:0.8rem;">{week.get('expected_improvement', '')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c_sub, c_daily = st.columns(2)
                with c_sub:
                    st.markdown("**Subtopics to cover:**")
                    for sub in week.get("subtopics", []):
                        st.markdown(f"• {sub}")
                with c_daily:
                    st.markdown("**Daily Targets:**")
                    for target in week.get("daily_goals", []):
                        st.markdown(f"• {target}")
                
                # Resources
                res = week.get("resources", [])
                if res:
                    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
                    st.markdown("**Recommended Resources:**")
                    res_html = "  ·  ".join(f'<span style="color:#06b6d4;">{r}</span>' for r in res)
                    st.markdown(f'<div>{res_html}</div>', unsafe_allow_html=True)

    # Daily Habits
    habits = roadmap_data.get("weekly_goals") or roadmap_data.get("daily_habits") or []
    if habits:
        st.markdown("### 🏆 Recommended Practice Habits")
        for i, habit in enumerate(habits, 1):
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid rgba(255,255,255,0.06);
                 border-radius:10px;padding:0.75rem 1rem;margin-bottom:0.4rem;display:flex;align-items:center;gap:0.75rem;">
                <span style="color:#6366f1;font-weight:800;font-size:1.1rem;">0{i}</span>
                <span style="color:var(--text-primary);font-size:0.9rem;">{habit}</span>
            </div>
            """, unsafe_allow_html=True)
else:
    empty_state("map", "No Roadmap Active", "Click generate above to create your personalized weekly learning plan!", "← We will analyze your weaknesses and create an adaptive schedule")
