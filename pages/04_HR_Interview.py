"""
Page 04 — HR Interview Preparation
Behavioral questions with STAR method coaching and communication scoring.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, render_sidebar_nav,
    render_ai_provider_selector, empty_state, feedback_card
)
from src.ai.gemini_client import generate_hr_questions, evaluate_hr_answer
from src.database.supabase_client import award_xp
from src.utils.helpers import score_to_emoji

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("HR Interview Prep", "Master behavioral questions with STAR method coaching and AI feedback", "🤝")

# STAR Method info banner
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(139,92,246,0.08));
     border:1px solid rgba(99,102,241,0.25);border-radius:14px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;">
    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
        <span style="font-size:1.2rem;">⭐</span>
        <span style="color:#818cf8;font-weight:700;">STAR Method Guide</span>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">
        <div><span style="color:#6366f1;font-weight:700;">S</span><span style="color:#e2e8f0;"> — Situation</span><br><span style="color:#64748b;font-size:0.8rem;">Set the scene and context</span></div>
        <div><span style="color:#8b5cf6;font-weight:700;">T</span><span style="color:#e2e8f0;"> — Task</span><br><span style="color:#64748b;font-size:0.8rem;">Describe your responsibility</span></div>
        <div><span style="color:#06b6d4;font-weight:700;">A</span><span style="color:#e2e8f0;"> — Action</span><br><span style="color:#64748b;font-size:0.8rem;">Explain steps you took</span></div>
        <div><span style="color:#22c55e;font-weight:700;">R</span><span style="color:#e2e8f0;"> — Result</span><br><span style="color:#64748b;font-size:0.8rem;">Share the outcome/impact</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Configuration ─────────────────────────────────────────────────────────────
cfg1, cfg2, cfg3 = st.columns(3)
with cfg1:
    target_role = st.text_input("Target Role", placeholder="Software Engineer", key="hr_role")
with cfg2:
    focus_area = st.multiselect(
        "Focus Areas",
        ["Leadership", "Teamwork", "Conflict Resolution", "Achievement", "Growth", "Communication", "Problem Solving"],
        default=["Leadership", "Teamwork"],
        key="hr_focus"
    )
with cfg3:
    q_count = st.slider("Number of Questions", 3, 10, 5, key="hr_count")

gen_btn = st.button("🚀 Generate HR Questions", type="primary", key="gen_hr_btn")

if gen_btn:
    name = profile.get("full_name", "Student") if profile else "Student"
    college = profile.get("college", "") if profile else ""
    branch = profile.get("branch", "") if profile else ""
    focus_str = ", ".join(focus_area) if focus_area else "General"

    with st.spinner("🤖 Generating personalized behavioral questions..."):
        result = generate_hr_questions(name, college, branch, target_role or "Software Engineer", focus_str, q_count)

    if result and result.get("questions"):
        st.session_state["hr_questions"] = result["questions"]
        st.session_state["hr_evaluations"] = {}
        st.success(f"✅ Generated {len(result['questions'])} behavioral questions!")
    else:
        st.error("Failed to generate questions. Please try again.")

# ── Questions ─────────────────────────────────────────────────────────────────
questions = st.session_state.get("hr_questions", [])
evaluations = st.session_state.get("hr_evaluations", {})

if questions:
    st.markdown(f"---\n### 📋 {len(questions)} Behavioral Interview Questions")

    for i, q in enumerate(questions):
        q_text = q.get("question", "")
        category = q.get("category", "")
        star_tip = q.get("star_guidance", "")
        looks_for = q.get("what_interviewer_looks_for", "")

        # Question card
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
             border-radius:14px;padding:1.25rem;margin-bottom:0.5rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
                <span style="background:#8b5cf6;color:#fff;border-radius:8px;padding:0.2rem 0.6rem;font-size:0.75rem;font-weight:700;">Q{i+1}</span>
                {badge(category.title(), '#8b5cf6') if category else ''}
            </div>
            <div style="color:#f1f5f9;font-size:0.95rem;line-height:1.65;margin-bottom:0.75rem;">{q_text}</div>
            {f'<div style="color:#64748b;font-size:0.82rem;margin-top:0.4rem;">💡 <em>{star_tip}</em></div>' if star_tip else ''}
            {f'<div style="color:#06b6d4;font-size:0.8rem;margin-top:0.3rem;">🎯 Interviewer looks for: {looks_for}</div>' if looks_for else ''}
        </div>
        """, unsafe_allow_html=True)

        # STAR template helper
        with st.expander(f"📝 STAR Framework Template for Q{i+1}"):
            c1, c2 = st.columns(2)
            with c1:
                st.text_area("Situation", placeholder="Describe the context...", key=f"star_s_{i}", height=80)
                st.text_area("Action", placeholder="Steps you took...", key=f"star_a_{i}", height=80)
            with c2:
                st.text_area("Task", placeholder="Your responsibility...", key=f"star_t_{i}", height=80)
                st.text_area("Result", placeholder="Outcome and impact...", key=f"star_r_{i}", height=80)

        # Full answer
        answer = st.text_area(
            f"Full Answer for Q{i+1}",
            placeholder="Write your complete structured answer using the STAR method above...",
            key=f"hr_ans_{i}",
            height=140,
            label_visibility="collapsed",
        )

        if st.button(f"🤖 Evaluate HR Answer", key=f"eval_hr_{i}") and answer.strip():
            with st.spinner("AI evaluating communication and structure..."):
                ev = evaluate_hr_answer(q_text, answer)
            if ev:
                st.session_state["hr_evaluations"][i] = ev
                award_xp(user_id, 15)
            else:
                st.error("Evaluation failed.")

        # Show evaluation
        if i in evaluations:
            ev = evaluations[i]
            score = ev.get("overall_score", 0)
            feedback_card(score, ev.get("feedback", ""), ev.get("improved_answer_example", ""))

            sub_cols = st.columns(5)
            metrics = [
                ("Communication", ev.get("communication_score", 0)),
                ("Confidence", ev.get("confidence_score", 0)),
                ("Professionalism", ev.get("professionalism_score", 0)),
                ("Structure", ev.get("structure_score", 0)),
                ("Relevance", ev.get("relevance_score", 0)),
            ]
            for col, (label, val) in zip(sub_cols, metrics):
                col.metric(label, f"{val:.0f}/100")

            # STAR Analysis
            star_analysis = ev.get("star_analysis", {})
            if star_analysis:
                st.markdown("**⭐ STAR Method Analysis:**")
                star_cols = st.columns(4)
                for col, (part, status) in zip(star_cols, star_analysis.items()):
                    color = "#22c55e" if status == "present" else "#f59e0b" if status == "partial" else "#ef4444"
                    icon = "✅" if status == "present" else "⚠️" if status == "partial" else "❌"
                    col.markdown(f'<div style="text-align:center;"><div style="font-weight:700;color:{color};">{icon} {part.upper()}</div><div style="color:{color};font-size:0.8rem;">{status}</div></div>', unsafe_allow_html=True)

            # Emotion indicators
            emotion = ev.get("emotion_indicators", {})
            if emotion:
                confidence_level = emotion.get("confidence_level", "medium")
                conf_color = "#22c55e" if confidence_level == "high" else "#f59e0b" if confidence_level == "medium" else "#ef4444"
                fillers = emotion.get("filler_patterns", [])
                st.markdown(f'<div style="color:#94a3b8;font-size:0.85rem;margin-top:0.5rem;">Confidence: <span style="color:{conf_color};">{confidence_level.upper()}</span> · Filler words detected: <span style="color:#ef4444;">{", ".join(fillers) if fillers else "None"}</span></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    if evaluations:
        avg = sum(e.get("overall_score", 0) for e in evaluations.values()) / len(evaluations)
        emoji = score_to_emoji(avg)
        st.markdown(f"""
        <div style="background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.3);
             border-radius:14px;padding:1.5rem;text-align:center;margin-top:1rem;">
            <div style="font-size:2rem;">{emoji}</div>
            <div style="font-size:2rem;font-weight:800;color:#8b5cf6;">{avg:.1f}<span style="font-size:1rem;color:#94a3b8;">/100</span></div>
            <div style="color:#94a3b8;">HR Interview Session Score</div>
        </div>
        """, unsafe_allow_html=True)

else:
    if not gen_btn:
        empty_state("🤝", "Ready for HR Practice", "Configure your session and generate behavioral questions to begin!", "← Set your target role and focus areas")
