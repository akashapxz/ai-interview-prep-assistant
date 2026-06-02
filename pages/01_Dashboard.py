"""
Page 01 — Dashboard
Shows KPIs, performance charts, recent activity, weak areas, and AI recommendations.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, timedelta
from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.database.supabase_client import (
    db_select, get_performance_history, get_supabase_client, db_insert
)
from src.components.ui_components import (
    inject_global_css, page_header, kpi_card, score_ring,
    render_sidebar_nav, render_ai_provider_selector, empty_state, glass_card
)
from src.components.charts import (
    radar_chart, performance_line_chart, pie_chart, readiness_gauge, weekly_progress_chart
)
from src.utils.helpers import score_to_emoji, readiness_label, time_ago, SKILL_DOMAINS

# ── Page config ───────────────────────────────────────────────────────────────
st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# Fetch data
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_dashboard_data(uid: str):
    interviews = db_select("interviews", {"user_id": uid, "status": "completed"}, order="created_at.desc", limit=50)
    coding = db_select("coding_sessions", {"user_id": uid}, order="created_at.desc", limit=50)
    performance = get_performance_history(uid, days=30)
    achievements = db_select("user_achievements", {"user_id": uid})
    recommendations = db_select("recommendations", {"user_id": uid, "is_active": True}, limit=1)
    bookmarks = db_select("responses", {"user_id": uid, "is_bookmarked": True}, limit=5)
    return interviews, coding, performance, achievements, recommendations, bookmarks

interviews, coding, performance, achievements, recommendations, bookmarks = load_dashboard_data(user_id)

# Compute aggregate stats
total_interviews = len(interviews)
avg_technical = round(sum(i.get("technical_score", 0) for i in interviews) / max(total_interviews, 1), 1)
avg_hr = round(sum(i.get("hr_score", 0) for i in interviews) / max(total_interviews, 1), 1)
avg_coding = round(sum(i.get("coding_score", 0) for i in interviews) / max(total_interviews, 1), 1)
avg_comm = round(sum(i.get("communication_score", 0) for i in interviews) / max(total_interviews, 1), 1)
avg_overall = round(sum(i.get("overall_score", 0) for i in interviews) / max(total_interviews, 1), 1)
problems_solved = sum(1 for c in coding if c.get("status") == "solved")
readiness = min(100, int((avg_overall * 0.5) + (total_interviews * 2) + (problems_solved * 0.5)))


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
name = profile.get("full_name", "there") if profile else "there"
greeting_hour = int(__import__("datetime").datetime.now().strftime("%H"))
greeting = "Good morning" if greeting_hour < 12 else "Good afternoon" if greeting_hour < 17 else "Good evening"

page_header(f"{greeting}, {name.split()[0]}! 👋", "Here's your interview preparation overview", "📊")

# Daily challenge banner
today_challenge = db_select("daily_challenges", {"challenge_date": str(date.today())}, limit=1)
if today_challenge:
    ch = today_challenge[0]
    already_solved = db_select(
        "user_daily_challenges",
        {"user_id": user_id, "challenge_id": ch["id"]},
        limit=1,
    )
    ch_col1, ch_col2 = st.columns([5, 1])
    with ch_col1:
        st.markdown(f"""
        <div style="
            background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(6,182,212,0.1));
            border:1px solid rgba(99,102,241,0.3);border-radius:14px;
            padding:1rem 1.5rem;
            animation:fadeInUp 0.5s ease;
        ">
            <span style="color:#818cf8;font-weight:700;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;">⚡ Daily Challenge · {ch.get('category','General').title()}</span>
            <p style="color:#f1f5f9;margin:0.4rem 0 0;font-size:0.95rem;line-height:1.6;">{ch['question'][:180]}{'...' if len(ch['question']) > 180 else ''}</p>
        </div>
        """, unsafe_allow_html=True)
    with ch_col2:
        st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
        if already_solved:
            score = already_solved[0].get("score", 0)
            st.markdown(f"""
            <div style="
                background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.3);
                border-radius:10px;padding:0.5rem;text-align:center;
            ">
                <div style="color:#22c55e;font-weight:700;font-size:0.82rem;text-transform:uppercase;">Completed</div>
                <div style="color:#f1f5f9;font-weight:800;font-size:1.05rem;margin-top:0.2rem;">{score:.0f}/100</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button("⚡ Attempt", key="daily_challenge_attempt", type="primary", use_container_width=True):
                st.session_state["daily_challenge"] = ch
                st.session_state["show_challenge_modal"] = True

    # Inline attempt modal
    if not already_solved and st.session_state.get("show_challenge_modal") and st.session_state.get("daily_challenge"):
        ch_data = st.session_state["daily_challenge"]
        with st.expander("✍️ Write your answer — Daily Challenge", expanded=True):
            st.markdown(f"<p style='color:#e2e8f0;font-size:0.95rem;line-height:1.6;margin-bottom:1rem;'><b>Q:</b> {ch_data['question']}</p>", unsafe_allow_html=True)
            ch_answer = st.text_area(
                "Your Answer",
                placeholder="Type your answer here… Take your time to structure your thoughts.",
                height=160,
                key="daily_challenge_answer",
            )
            cc1, cc2 = st.columns([3, 1])
            with cc1:
                if st.button("📤 Submit Answer", key="submit_daily_challenge", type="primary"):
                    if ch_answer.strip():
                        from src.ai.gemini_client import evaluate_technical_answer
                        with st.spinner("🤖 AI is evaluating your answer…"):
                            result = evaluate_technical_answer(
                                question=ch_data["question"],
                                answer=ch_answer,
                                domain=ch_data.get("category", "General"),
                                difficulty=ch_data.get("difficulty", "medium"),
                            )
                        if result:
                            score = result.get("overall_score", result.get("score", 0))
                            
                            # Save to user_daily_challenges table
                            db_insert("user_daily_challenges", {
                                "user_id": user_id,
                                "challenge_id": ch_data["id"],
                                "answer_text": ch_answer,
                                "score": float(score),
                            })
                            
                            color = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                            st.markdown(f"""
                            <div style="background:rgba(255,255,255,0.04);border-left:4px solid {color};
                                 border-radius:10px;padding:1rem;margin-top:0.75rem;">
                                <div style="color:{color};font-size:1.2rem;font-weight:800;">Score: {score:.0f}/100</div>
                                <div style="color:#e2e8f0;margin-top:0.5rem;line-height:1.6;">{result.get('feedback','')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            from src.database.supabase_client import award_xp
                            award_xp(user_id, max(5, int(score) // 10))
                            st.success(f"🎉 +{max(5, int(score) // 10)} XP awarded!")
                            st.session_state["show_challenge_modal"] = False
                            st.rerun()
                        else:
                            st.warning("Could not evaluate answer right now. Try again!")
                    else:
                        st.warning("Please write an answer before submitting.")
            with cc2:
                if st.button("✖ Close", key="close_daily_challenge"):
                    st.session_state["show_challenge_modal"] = False
                    st.rerun()


# ─────────────────────────────────────────────
# KPI Row
# ─────────────────────────────────────────────
st.markdown("### 📈 Quick Stats")
c1, c2, c3, c4, c5, c6 = st.columns(6)
kpis = [
    (c1, "🎯", "Interviews", str(total_interviews), "completed", "#6366f1"),
    (c2, "💻", "Technical", f"{avg_technical:.0f}", "avg score", "#06b6d4"),
    (c3, "🤝", "HR Score", f"{avg_hr:.0f}", "avg score", "#8b5cf6"),
    (c4, "👨‍💻", "Coding", f"{avg_coding:.0f}", "avg score", "#22c55e"),
    (c5, "🗣️", "Communication", f"{avg_comm:.0f}", "avg score", "#f59e0b"),
    (c6, "💡", "Problems", str(problems_solved), "solved", "#ef4444"),
]
for col, icon, title, val, sub, color in kpis:
    with col:
        st.markdown(kpi_card(icon, title, val, sub, color), unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Score Rings + Readiness
# ─────────────────────────────────────────────
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
st.markdown("### 🎯 Performance Scores")
cols = st.columns([2, 3])

with cols[0]:
    st.plotly_chart(readiness_gauge(readiness), use_container_width=True, config={"displayModeBar": False})
    st.markdown(f"""
    <div style="text-align:center;margin-top:-1rem;">
        <span style="
            background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
            border-radius:99px;padding:0.4rem 1.2rem;font-size:0.9rem;color:#818cf8;font-weight:600;
        ">{readiness_label(readiness)}</span>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    ring_html = ""
    rings = [
        (avg_overall, "Overall"), (avg_technical, "Technical"),
        (avg_hr, "HR"), (avg_coding, "Coding"), (avg_comm, "Communication"),
    ]
    for score, label in rings:
        ring_html += score_ring(score, label, 100)
    st.markdown(f'<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:1rem;padding:1rem;">{ring_html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Charts Row
# ─────────────────────────────────────────────
st.markdown("### 📉 Performance Trends")
ch1, ch2 = st.columns(2)

with ch1:
    if performance:
        st.plotly_chart(performance_line_chart(performance, "30-Day Score Trend"), use_container_width=True, config={"displayModeBar": False})
    else:
        empty_state("📉", "No data yet", "Complete interviews to see your trend.")

with ch2:
    if interviews:
        type_counts = {}
        for iv in interviews:
            t = iv.get("interview_type", "other").replace("_", " ").title()
            type_counts[t] = type_counts.get(t, 0) + 1
        st.plotly_chart(pie_chart(list(type_counts.keys()), list(type_counts.values()), "Interview Type Distribution"), use_container_width=True, config={"displayModeBar": False})
    else:
        empty_state("🥧", "No interviews yet", "Start a mock interview to see distribution.")


# Skill radar
if performance:
    skills_avg = {
        "Technical": avg_technical,
        "HR": avg_hr,
        "Coding": avg_coding,
        "Communication": avg_comm,
        "Confidence": round(sum(i.get("confidence_score", 0) for i in interviews) / max(total_interviews, 1), 1),
    }
    st.plotly_chart(radar_chart(skills_avg, "Skill Distribution Radar"), use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────
# Recent Activity + Weak Areas
# ─────────────────────────────────────────────
st.markdown("### 🕐 Recent Activity & Insights")
left, right = st.columns(2)

with left:
    st.markdown("**Recent Interviews**")
    if interviews:
        for iv in interviews[:5]:
            score = iv.get("overall_score", 0)
            emoji = score_to_emoji(score)
            iv_type = iv.get("interview_type", "").replace("_", " ").title()
            created = iv.get("created_at", "")
            st.markdown(f"""
            <div style="
                background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                border-radius:12px;padding:0.75rem 1rem;margin-bottom:0.5rem;
                display:flex;align-items:center;justify-content:space-between;
            ">
                <div>
                    <span style="color:#f1f5f9;font-weight:600;font-size:0.9rem;">{iv_type}</span>
                    <div style="color:#64748b;font-size:0.78rem;">{time_ago(created)}</div>
                </div>
                <span style="font-size:1.1rem;">{emoji}</span>
                <span style="color:#6366f1;font-weight:700;">{score:.0f}<span style="color:#64748b;font-weight:400;">/100</span></span>
            </div>
            """, unsafe_allow_html=True)
    else:
        empty_state("🎯", "No interviews yet", "Start your first mock interview!", "Go to Mock Interview →")

with right:
    st.markdown("**Weak Areas to Focus**")
    # Identify weak areas from scores
    domain_scores = {}
    for iv in interviews:
        domain = iv.get("domain")
        if domain:
            if domain not in domain_scores:
                domain_scores[domain] = []
            domain_scores[domain].append(iv.get("overall_score", 0))

    weak_areas = [(d, round(sum(s)/len(s), 1)) for d, s in domain_scores.items() if sum(s)/len(s) < 70]
    weak_areas.sort(key=lambda x: x[1])

    if weak_areas:
        for domain, score in weak_areas[:5]:
            color = "#ef4444" if score < 50 else "#f59e0b"
            st.markdown(f"""
            <div style="
                background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                border-radius:10px;padding:0.6rem 1rem;margin-bottom:0.4rem;
                display:flex;align-items:center;justify-content:space-between;
            ">
                <span style="color:#f1f5f9;font-size:0.9rem;">📚 {domain}</span>
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    <div style="width:80px;height:6px;background:rgba(255,255,255,0.08);border-radius:99px;overflow:hidden;">
                        <div style="width:{score}%;height:100%;background:{color};border-radius:99px;"></div>
                    </div>
                    <span style="color:{color};font-weight:700;font-size:0.85rem;">{score:.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        empty_state("🎉", "Great job!", "No critical weak areas found. Keep practicing to maintain your scores!")

    # Bookmarked questions
    if bookmarks:
        st.markdown("**📌 Bookmarked Questions**")
        for bm in bookmarks[:3]:
            q_rows = db_select("interview_questions", {"id": bm.get("question_id", "")})
            if q_rows:
                q = q_rows[0].get("question_text", "")[:80]
                st.markdown(f'<div style="color:#94a3b8;font-size:0.85rem;padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.05);">📌 {q}...</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Achievements
# ─────────────────────────────────────────────
st.markdown("### 🏅 Achievements")
if achievements:
    ach_details = db_select("achievements", {})
    ach_map = {a["id"]: a for a in ach_details}
    earned_ids = {ua["achievement_id"] for ua in achievements}
    cols_ach = st.columns(6)
    for i, a in enumerate(ach_details[:12]):
        earned = a["id"] in earned_ids
        with cols_ach[i % 6]:
            st.markdown(f"""
            <div style="
                text-align:center;padding:0.75rem 0.5rem;
                background:{'rgba(99,102,241,0.12)' if earned else 'rgba(255,255,255,0.02)'};
                border:1px solid {'rgba(99,102,241,0.35)' if earned else 'rgba(255,255,255,0.06)'};
                border-radius:12px;margin-bottom:0.5rem;
                opacity:{'1' if earned else '0.4'};
            ">
                <div style="font-size:1.6rem;">{a.get('icon','🏆')}</div>
                <div style="color:{'#818cf8' if earned else '#64748b'};font-size:0.7rem;font-weight:600;margin-top:0.2rem;">{a['name']}</div>
                <div style="color:#6366f1;font-size:0.65rem;">+{a['xp_reward']} XP</div>
            </div>
            """, unsafe_allow_html=True)
else:
    empty_state("🏅", "No achievements yet", "Complete interviews to earn badges and XP!", "Start practicing →")


# ─────────────────────────────────────────────
# Learning Roadmap Preview
# ─────────────────────────────────────────────
if recommendations:
    rec = recommendations[0]
    roadmap = rec.get("roadmap", [])
    if roadmap:
        st.markdown("### 🗺️ Your Learning Roadmap")
        rm_cols = st.columns(min(len(roadmap), 4))
        for i, week in enumerate(roadmap[:4]):
            with rm_cols[i]:
                st.markdown(f"""
                <div style="
                    background:rgba(99,102,241,0.08);
                    border:1px solid rgba(99,102,241,0.2);
                    border-radius:12px;padding:1rem;text-align:center;
                ">
                    <div style="color:#6366f1;font-weight:700;font-size:0.8rem;margin-bottom:0.4rem;">Week {week.get('week',i+1)}</div>
                    <div style="color:#f1f5f9;font-weight:600;font-size:0.9rem;">{week.get('focus_topic','')}</div>
                    <div style="color:#64748b;font-size:0.75rem;margin-top:0.3rem;">{week.get('expected_improvement','')[:60]}</div>
                </div>
                """, unsafe_allow_html=True)
