"""
Page 03 — Technical Interview Preparation
AI-generated questions across domains, difficulty levels, and types with evaluation.
"""

import streamlit as st
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, difficulty_badge,
    render_sidebar_nav, render_ai_provider_selector, empty_state, feedback_card
)
from src.database.supabase_client import db_insert, db_select, db_update
from src.ai.gemini_client import generate_technical_questions, evaluate_technical_answer
from src.utils.helpers import SKILL_DOMAINS, score_to_emoji, calculate_xp_for_interview
from src.database.supabase_client import award_xp

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("Technical Interview Prep", "Practice domain-specific technical questions with AI evaluation", "💻")

# ── Settings ──────────────────────────────────────────────────────────────────
st.markdown("### ⚙️ Configure Practice Session")
cfg1, cfg2, cfg3, cfg4 = st.columns(4)
with cfg1:
    domain = st.selectbox("Domain", SKILL_DOMAINS, key="tech_domain")
with cfg2:
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1, key="tech_diff")
with cfg3:
    q_type = st.selectbox("Question Type", ["Conceptual", "Scenario Based", "Problem Solving"], key="tech_type")
with cfg4:
    q_count = st.slider("Questions", 3, 10, 5, key="tech_count")

# Skills from latest resume
latest_resume = db_select("resumes", {"user_id": user_id}, order="created_at.desc", limit=1)
skills_str = ""
if latest_resume and latest_resume[0].get("skills"):
    skills_str = ", ".join(latest_resume[0]["skills"][:10])
    st.markdown(f'<div style="color:#64748b;font-size:0.85rem;">📄 Using skills from your resume: <span style="color:#818cf8;">{skills_str[:80]}...</span></div>', unsafe_allow_html=True)

gen_btn = st.button("🚀 Generate Questions", type="primary", use_container_width=False, key="gen_tech_btn")

if gen_btn:
    with st.spinner(f"🤖 Generating {q_count} {difficulty} {domain} questions..."):
        result = generate_technical_questions(domain, difficulty.lower(), q_type.lower().replace(" ", "_"), skills_str, q_count)

    if result and result.get("questions"):
        st.session_state["tech_questions"] = result["questions"]
        st.session_state["tech_answers"] = {}
        st.session_state["tech_evaluations"] = {}
        st.session_state["tech_domain_val"] = domain
        st.session_state["tech_difficulty_val"] = difficulty
        st.success(f"✅ Generated {len(result['questions'])} questions!")
    else:
        st.error("Failed to generate questions. Please try again.")

# ── Questions Display ─────────────────────────────────────────────────────────
questions = st.session_state.get("tech_questions", [])
evaluations = st.session_state.get("tech_evaluations", {})

if questions:
    st.markdown(f"---\n### 📝 {len(questions)} Questions — {st.session_state.get('tech_domain_val', domain)} | {st.session_state.get('tech_difficulty_val', difficulty)}")

    for i, q in enumerate(questions):
        q_text = q.get("question", "")
        hints = q.get("hints", [])

        st.markdown(f"""
        <div style="
            background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
            border-radius:14px;padding:1.25rem 1.5rem;margin-bottom:0.5rem;
        ">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
                <span style="background:#6366f1;color:#fff;border-radius:8px;padding:0.2rem 0.6rem;font-size:0.75rem;font-weight:700;">Q{i+1}</span>
                {difficulty_badge(q.get('difficulty', difficulty))}
                {badge(q.get('domain', domain), '#06b6d4')}
            </div>
            <div style="color:#f1f5f9;font-size:0.95rem;line-height:1.65;">{q_text}</div>
        </div>
        """, unsafe_allow_html=True)

        # Hints expander
        if hints:
            with st.expander(f"💡 Hints for Q{i+1}"):
                for h in hints:
                    st.markdown(f"• {h}")

        # Answer input
        answer_key = f"tech_ans_{i}"
        answer = st.text_area(
            f"Your Answer for Q{i+1}",
            placeholder="Type your answer here. Be detailed and structured.",
            key=answer_key,
            height=120,
            label_visibility="collapsed",
        )
        st.session_state.setdefault("tech_answers", {})[i] = answer

        # Evaluate button
        eval_col, book_col = st.columns([3, 1])
        with eval_col:
            if st.button(f"🤖 Evaluate Answer", key=f"eval_tech_{i}") and answer.strip():
                with st.spinner("AI evaluating..."):
                    eval_result = evaluate_technical_answer(q_text, answer, domain, difficulty.lower())
                if eval_result:
                    st.session_state["tech_evaluations"][i] = eval_result
                    # Save to DB (create minimal interview record if needed)
                    award_xp(user_id, 10)
                else:
                    st.error("Evaluation failed. Try again.")

        # Show evaluation
        if i in evaluations:
            ev = evaluations[i]
            score = ev.get("overall_score", 0)
            feedback_card(score, ev.get("feedback", ""), ev.get("model_answer", ""))

            # Sub-scores
            sub_cols = st.columns(4)
            sub_metrics = [("Accuracy", ev.get("accuracy_score", 0)), ("Depth", ev.get("depth_score", 0)),
                           ("Clarity", ev.get("clarity_score", 0)), ("Completeness", ev.get("completeness_score", 0))]
            for col, (label, val) in zip(sub_cols, sub_metrics):
                col.metric(label, f"{val:.0f}/100")

            if ev.get("key_points_missed"):
                with st.expander("📌 Key Points Missed"):
                    for pt in ev["key_points_missed"]:
                        st.markdown(f"• {pt}")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Session summary
    if evaluations:
        st.markdown("---")
        st.markdown("### 📊 Session Summary")
        avg = sum(e.get("overall_score", 0) for e in evaluations.values()) / len(evaluations)
        emoji = score_to_emoji(avg)
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
             border-radius:14px;padding:1.5rem;text-align:center;">
            <div style="font-size:2.5rem;">{emoji}</div>
            <div style="font-size:2rem;font-weight:800;color:#6366f1;">{avg:.1f}<span style="font-size:1rem;color:#94a3b8;">/100</span></div>
            <div style="color:#94a3b8;">Average Score across {len(evaluations)} evaluated questions</div>
        </div>
        """, unsafe_allow_html=True)

else:
    if not gen_btn:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        empty_state("💻", "Ready to Practice", "Configure your session above and click Generate Questions to start!", "← Set your domain, difficulty, and question type")

# ── History Tab ───────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("📚 View Past Technical Practice Sessions"):
    past_responses = db_select("responses", {"user_id": user_id}, order="created_at.desc", limit=20)
    if past_responses:
        for r in past_responses[:10]:
            q_rows = db_select("interview_questions", {"id": r.get("question_id","")})
            if q_rows:
                q_text = q_rows[0].get("question_text","")[:80]
                score = r.get("score", 0)
                color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:0.6rem;margin-bottom:0.3rem;
                     display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:#e2e8f0;font-size:0.85rem;">{q_text}...</span>
                    <span style="color:{color};font-weight:700;">{score:.0f}/100</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No past sessions yet.")
