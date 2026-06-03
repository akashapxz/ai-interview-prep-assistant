"""
Page 05 — Coding Interview Preparation
LeetCode-style problems with code editor, AI evaluation, hints, and complexity analysis.
"""

import streamlit as st
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, difficulty_badge,
    render_sidebar_nav, render_ai_provider_selector, empty_state
)
from src.database.supabase_client import db_insert, db_select, award_xp
from src.ai.gemini_client import generate_coding_problem, evaluate_code
from src.utils.helpers import CODING_TOPICS, score_to_emoji, format_duration

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("Coding Interview Prep", "Practice LeetCode-style problems with AI evaluation, hints, and optimal solutions", "code")

tabs = st.tabs(["💻 Practice", "📊 History", "🏆 Problem Bank"])

# ── TAB 1: Practice ───────────────────────────────────────────────────────────
with tabs[0]:
    cfg1, cfg2, cfg3 = st.columns(3)
    with cfg1:
        topic = st.selectbox("Topic", CODING_TOPICS, key="code_topic")
    with cfg2:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], index=1, key="code_diff")
    with cfg3:
        language = st.selectbox("Language", ["python", "java", "cpp", "javascript"], key="code_lang",
                                format_func=lambda x: {"python": "🐍 Python", "java": "☕ Java", "cpp": "⚡ C++", "javascript": "🟨 JavaScript"}[x])

    gen_btn = st.button("🎲 Generate Problem", type="primary", key="gen_code_btn")

    if gen_btn:
        with st.spinner(f"🤖 Generating a {difficulty} {topic} problem..."):
            problem = generate_coding_problem(topic, difficulty.lower(), language)
        if problem:
            st.session_state["current_problem"] = problem
            st.session_state["code_start_time"] = time.time()
            st.session_state["code_evaluation"] = None
            st.session_state["hints_shown"] = 0
            st.success(f"✅ Problem generated: {problem.get('title', '')}")
        else:
            st.error("Failed to generate problem. Please try again.")

    problem = st.session_state.get("current_problem")

    if problem:
        st.markdown("---")
        col_prob, col_code = st.columns([1, 1])

        with col_prob:
            # Problem statement
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);
                 border-radius:14px;padding:1.5rem;height:100%;">
                <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
                    <h3 style="color:var(--text-primary);margin:0;">{problem.get('title','Problem')}</h3>
                    {difficulty_badge(difficulty)}
                    {badge(topic, '#06b6d4')}
                </div>
                <div style="color:var(--text-primary);line-height:1.7;margin-bottom:1rem;">{problem.get('description','')}</div>
            """, unsafe_allow_html=True)

            # Examples
            for ex in problem.get("examples", []):
                st.markdown(f"""
                <div style="background:rgba(0,0,0,0.3);border-radius:8px;padding:0.75rem;margin-bottom:0.5rem;font-family:JetBrains Mono,monospace;font-size:0.85rem;">
                    <div style="color:#06b6d4;"><strong>Input:</strong> {ex.get('input','')}</div>
                    <div style="color:#22c55e;"><strong>Output:</strong> {ex.get('output','')}</div>
                    {f'<div style="color:var(--text-secondary);"><strong>Explanation:</strong> {ex.get("explanation","")}</div>' if ex.get('explanation') else ''}
                </div>
                """, unsafe_allow_html=True)

            # Constraints
            if problem.get("constraints"):
                st.markdown("**Constraints:**")
                for c in problem["constraints"]:
                    st.markdown(f'<div style="color:var(--text-secondary);font-size:0.85rem;">• {c}</div>', unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Hints
            hints = problem.get("hints", [])
            hints_shown = st.session_state.get("hints_shown", 0)
            if hints and hints_shown < len(hints):
                if st.button(f"💡 Reveal Hint {hints_shown + 1}/{len(hints)}", key="show_hint"):
                    st.session_state["hints_shown"] = hints_shown + 1
            for h_idx in range(hints_shown):
                st.markdown(f'<div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:8px;padding:0.6rem;margin-top:0.4rem;color:#fbbf24;">💡 Hint {h_idx+1}: {hints[h_idx]}</div>', unsafe_allow_html=True)

        with col_code:
            st.markdown("**✍️ Your Solution**")

            # Starter templates
            starters = {
                "python": f"def solution():\n    # Your code here\n    pass\n\n# Time Complexity: O(?)\n# Space Complexity: O(?)",
                "java": f"class Solution {{\n    public void solution() {{\n        // Your code here\n    }}\n}}",
                "cpp": f"class Solution {{\npublic:\n    void solution() {{\n        // Your code here\n    }}\n}};",
                "javascript": f"function solution() {{\n    // Your code here\n    return null;\n}}",
            }

            user_code = st.text_area(
                "Code Editor",
                value=st.session_state.get("user_code", starters.get(language, "")),
                height=350,
                key="code_editor",
                help="Write your solution here",
                label_visibility="collapsed",
            )
            st.session_state["user_code"] = user_code

            # Timer display
            if st.session_state.get("code_start_time"):
                elapsed = int(time.time() - st.session_state["code_start_time"])
                st.markdown(f'<div style="color:var(--text-muted);font-size:0.8rem;text-align:right;">⏱️ Time: {format_duration(elapsed)}</div>', unsafe_allow_html=True)

            sub_col1, sub_col2 = st.columns(2)
            with sub_col1:
                submit_btn = st.button("🚀 Submit Solution", type="primary", use_container_width=True, key="submit_code")
            with sub_col2:
                reveal_btn = st.button("👁️ Show Optimal Solution", use_container_width=True, key="reveal_solution")

            if reveal_btn and problem.get("optimal_solution"):
                with st.expander("✨ Optimal Solution", expanded=True):
                    st.code(problem["optimal_solution"], language=language)
                    st.markdown(f"""
                    <div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);border-radius:8px;padding:0.75rem;margin-top:0.5rem;">
                        <div style="color:#4ade80;">⏱️ <strong>Time:</strong> {problem.get('time_complexity','O(?)')}</div>
                        <div style="color:#4ade80;">💾 <strong>Space:</strong> {problem.get('space_complexity','O(?)')}</div>
                        <div style="color:var(--text-primary);margin-top:0.5rem;font-size:0.9rem;">{problem.get('approach_explanation','')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            if submit_btn and user_code.strip():
                elapsed = int(time.time() - st.session_state.get("code_start_time", time.time()))
                with st.spinner("🤖 AI evaluating your solution..."):
                    ev = evaluate_code(problem.get("description", ""), user_code, language)

                if ev:
                    st.session_state["code_evaluation"] = ev

                    # Save to DB
                    db_insert("coding_sessions", {
                        "user_id": user_id,
                        "problem_title": problem.get("title", ""),
                        "problem_description": problem.get("description", "")[:500],
                        "topic": topic,
                        "difficulty": difficulty.lower(),
                        "language": language,
                        "user_code": user_code,
                        "ai_solution": problem.get("optimal_solution", ""),
                        "correctness_score": ev.get("correctness_score", 0),
                        "time_complexity": ev.get("time_complexity", ""),
                        "space_complexity": ev.get("space_complexity", ""),
                        "best_practices_score": ev.get("best_practices_score", 0),
                        "overall_score": ev.get("overall_score", 0),
                        "ai_feedback": ev.get("feedback", ""),
                        "hints_used": hints_shown,
                        "time_taken_seconds": elapsed,
                        "status": "solved" if ev.get("overall_score", 0) >= 70 else "attempted",
                    })
                    award_xp(user_id, 25 if ev.get("overall_score", 0) >= 70 else 10)
                else:
                    st.error("Evaluation failed. Please try again.")

            # Show evaluation results
            ev = st.session_state.get("code_evaluation")
            if ev:
                st.markdown("---\n**📊 Evaluation Results**")
                overall = ev.get("overall_score", 0)
                color = "#22c55e" if overall >= 80 else "#f59e0b" if overall >= 60 else "#ef4444"

                met1, met2, met3, met4 = st.columns(4)
                met1.metric("Overall", f"{overall:.0f}/100")
                met2.metric("Correctness", f"{ev.get('correctness_score', 0):.0f}/100")
                met3.metric("Time Complexity", ev.get("time_complexity", "?"))
                met4.metric("Space Complexity", ev.get("space_complexity", "?"))

                if ev.get("feedback"):
                    st.markdown(f"""
                    <div style="background:var(--bg-card);border:1px solid {color}44;border-left:4px solid {color};
                         border-radius:12px;padding:1rem;margin:0.5rem 0;">
                        <div style="color:{color};font-weight:700;margin-bottom:0.4rem;">AI Feedback</div>
                        <div style="color:var(--text-primary);line-height:1.65;">{ev.get("feedback","")}</div>
                    </div>
                    """, unsafe_allow_html=True)

                if ev.get("improvements"):
                    with st.expander("💡 Suggested Improvements"):
                        for imp in ev["improvements"]:
                            st.markdown(f"• {imp}")

    else:
        if not gen_btn:
            empty_state("code", "Ready to Code", "Generate a problem to start your coding practice session!", "← Choose topic, difficulty, and language")

# ── TAB 2: History ────────────────────────────────────────────────────────────
with tabs[1]:
    history = db_select("coding_sessions", {"user_id": user_id}, order="created_at.desc", limit=30)
    if history:
        for sess in history:
            score = sess.get("overall_score", 0)
            status = sess.get("status", "attempted")
            status_color = "#22c55e" if status == "solved" else "#f59e0b" if status == "attempted" else "#ef4444"
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);
                 border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.5rem;
                 display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
                <div>
                    <span style="color:var(--text-primary);font-weight:600;">{sess.get('problem_title','Problem')}</span>
                    <div style="color:var(--text-muted);font-size:0.78rem;">{sess.get('topic','')} · {sess.get('difficulty','').title()} · {sess.get('language','')}</div>
                </div>
                <div style="display:flex;align-items:center;gap:1rem;">
                    {difficulty_badge(sess.get('difficulty','medium'))}
                    <span style="color:{status_color};font-weight:700;text-transform:capitalize;">{status}</span>
                    <span style="color:#6366f1;font-weight:700;">{score:.0f}/100</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        empty_state("dashboard", "No coding sessions yet", "Practice a problem to see your history here!")

# ── TAB 3: Problem Bank ───────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("### 📚 Quick Generate by Topic")
    topic_cols = st.columns(4)
    topics_with_icons = [
        ("Arrays", "📦"), ("Strings", "🔤"), ("Linked Lists", "🔗"), ("Trees", "🌳"),
        ("Graphs", "🕸️"), ("Dynamic Programming", "🧮"), ("Sorting", "dashboard"), ("Hashing", "key"),
    ]
    for i, (t, icon) in enumerate(topics_with_icons):
        with topic_cols[i % 4]:
            if st.button(f"{icon} {t}", use_container_width=True, key=f"quick_{t}"):
                st.session_state["_quick_topic"] = t
                st.rerun()

    st.markdown("---")
    # Stats per topic
    if history:
        topic_stats = {}
        for h in history:
            t = h.get("topic", "Other")
            if t not in topic_stats:
                topic_stats[t] = {"solved": 0, "total": 0}
            topic_stats[t]["total"] += 1
            if h.get("status") == "solved":
                topic_stats[t]["solved"] += 1

        st.markdown("**Your Topic Progress:**")
        for t, stats in sorted(topic_stats.items()):
            pct = stats["solved"] / max(stats["total"], 1) * 100
            color = "#22c55e" if pct >= 80 else "#f59e0b" if pct >= 50 else "#ef4444"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.4rem;">
                <div style="width:140px;color:var(--text-primary);font-size:0.9rem;">{t}</div>
                <div style="flex:1;height:8px;background:rgba(255,255,255,0.08);border-radius:99px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;background:{color};border-radius:99px;"></div>
                </div>
                <div style="color:{color};font-weight:600;font-size:0.85rem;width:80px;text-align:right;">{stats['solved']}/{stats['total']}</div>
            </div>
            """, unsafe_allow_html=True)
