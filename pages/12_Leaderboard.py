"""
Page 12 — Leaderboard & Gamification
Weekly challenges, streaks, achievement rewards, and user ranking.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, kpi_card,
    render_sidebar_nav, render_ai_provider_selector, empty_state
)
from src.components.charts import leaderboard_chart
from src.database.supabase_client import db_select, db_insert, get_supabase_client, award_xp

# st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user    = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header(
    "Leaderboard & Gamification",
    "Compete with peers, complete daily challenges, and earn XP badges",
    "emoji_events",
)

# ── Current User Stats ────────────────────────────────────────────────────────
user_xp     = profile.get("xp_points",  0) if profile else 0
user_streak = profile.get("streak_days", 0) if profile else 0
completed_challenges = len(db_select("user_daily_challenges", {"user_id": user_id}))

st.markdown("### ⚡ Your Stats")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(kpi_card("bolt", "Your Total XP",   f"{user_xp:,} XP",           "rank points",   "#6366f1"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("local_fire_department", "Practice Streak", f"{user_streak} Days",        "active streak", "#f59e0b"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi_card("gps_fixed", "Challenges Done",  str(completed_challenges),    "completed",     "#22c55e"), unsafe_allow_html=True)

st.markdown("---")

# ── Daily Challenge ───────────────────────────────────────────────────────────
st.markdown("### 📅 Today's Daily Challenge")
today = str(date.today())

challenge_row = db_select("daily_challenges", {"challenge_date": today}, limit=1)
if not challenge_row:
    try:
        from src.database.supabase_client import get_supabase_admin
        admin_client = get_supabase_admin()
        admin_client.table("daily_challenges").insert({
            "challenge_date":  today,
            "challenge_type":  "technical",
            "question":        "Explain the difference between SQL and NoSQL databases. When would you choose one over the other?",
            "domain":          "DBMS",
            "difficulty":      "medium",
        }).execute()
    except Exception as e:
        pass
    challenge_row = db_select("daily_challenges", {"challenge_date": today}, limit=1)

if challenge_row:
    ch = challenge_row[0]
    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid rgba(99,102,241,0.25);
         border-radius:14px;padding:1.25rem;margin-bottom:1.5rem;">
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
            {badge("Daily Challenge", "#6366f1")}
            {badge(ch.get("domain","General"), "#06b6d4")}
            {badge(ch.get("difficulty","medium").capitalize(), "#f59e0b")}
        </div>
        <div style="color:var(--text-primary);font-weight:600;font-size:1rem;line-height:1.6;">
            {ch["question"]}
        </div>
    </div>
    """, unsafe_allow_html=True)

    already_solved = db_select(
        "user_daily_challenges",
        {"user_id": user_id, "challenge_id": ch["id"]},
        limit=1,
    )
    if already_solved:
        st.success("🎉 You already completed today's challenge! Come back tomorrow.")
    else:
        ans = st.text_area("Your Answer", key="daily_ans", placeholder="Type your answer here...", height=120)
        if st.button("🚀 Submit Answer", type="primary", key="submit_challenge"):
            if ans.strip():
                from src.ai.gemini_client import evaluate_technical_answer
                with st.spinner("🤖 AI is evaluating your answer..."):
                    result = evaluate_technical_answer(
                        question=ch["question"],
                        answer=ans,
                        domain=ch.get("domain", "General"),
                        difficulty=ch.get("difficulty", "medium"),
                    )
                if result:
                    score = result.get("overall_score", result.get("score", 85.0))
                    db_insert("user_daily_challenges", {
                        "user_id":      user_id,
                        "challenge_id": ch["id"],
                        "answer_text":  ans,
                        "score":        float(score),
                    })
                    xp_awarded = max(5, int(score) // 10)
                    award_xp(user_id, xp_awarded)
                    st.success(f"🎉 Answer submitted! Score: {score:.0f}/100. You earned **+{xp_awarded} XP**!")
                    st.info(f"🤖 AI Feedback: {result.get('feedback', '')}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Could not evaluate answer right now. Try again!")
            else:
                st.warning("Please write an answer before submitting.")

st.markdown("---")

# ── Global Weekly Leaderboard ─────────────────────────────────────────────────
st.markdown("### 🏆 Global Weekly Rankings")

client       = get_supabase_client()
profiles_res = (
    client.table("profiles")
    .select("id, full_name, xp_points")
    .order("xp_points", desc=True)
    .limit(10)
    .execute()
)
profiles_list = profiles_res.data or []

if profiles_list:
    # Build chart-compatible list: leaderboard_chart expects
    # [{"profiles": {"full_name": ...}, "xp_gained": ...}, ...]
    chart_data = [
        {"profiles": {"full_name": p.get("full_name", "User")}, "xp_gained": p.get("xp_points", 0)}
        for p in profiles_list
    ]
    st.plotly_chart(
        leaderboard_chart(chart_data),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # Rank table
    st.markdown("#### Rankings Table")
    medals = ["🥇", "🥈", "🥉"]
    for i, p in enumerate(profiles_list, 1):
        medal = medals[i - 1] if i <= 3 else f"#{i}"
        is_me = p["id"] == user_id
        bg    = "rgba(99,102,241,0.12)" if is_me else "rgba(255,255,255,0.03)"
        border= "rgba(99,102,241,0.4)"  if is_me else "rgba(255,255,255,0.06)"
        st.markdown(f"""
        <div style="background:{bg};border:1px solid {border};border-radius:10px;
             padding:0.65rem 1rem;margin-bottom:0.35rem;
             display:flex;justify-content:space-between;align-items:center;">
            <div style="display:flex;align-items:center;gap:0.75rem;">
                <span style="font-size:1.2rem;width:2rem;text-align:center;">{medal}</span>
                <span style="color:var(--text-primary);font-weight:{'700' if is_me else '500'};">
                    {p.get('full_name','Anonymous')}
                    {'&nbsp;<span style="color:#818cf8;font-size:0.75rem;">(You)</span>' if is_me else ''}
                </span>
            </div>
            <span style="color:#6366f1;font-weight:700;">⚡ {p.get('xp_points',0):,} XP</span>
        </div>
        """, unsafe_allow_html=True)
else:
    empty_state(
        "emoji_events", "No Rankings Yet",
        "Rankings appear here once users complete interviews and earn XP.",
    )

# ── Achievements Showcase ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🎖️ Achievement Badges")

all_achievements = db_select("achievements")
user_achievements = {
    ua["achievement_id"]
    for ua in db_select("user_achievements", {"user_id": user_id})
}

if all_achievements:
    cols = st.columns(4)
    for i, ach in enumerate(all_achievements):
        earned = ach["id"] in user_achievements
        opacity = "1" if earned else "0.35"
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid {'rgba(99,102,241,0.4)' if earned else 'rgba(255,255,255,0.06)'};
                 border-radius:14px;padding:1rem;text-align:center;opacity:{opacity};
                 transition:all 0.3s ease;margin-bottom:0.75rem;">
                <div style="font-size:2rem;margin-bottom:0.4rem;">{ach.get('icon','emoji_events')}</div>
                <div style="color:var(--text-primary);font-weight:700;font-size:0.85rem;margin-bottom:0.3rem;">{ach['name']}</div>
                <div style="color:var(--text-muted);font-size:0.75rem;line-height:1.4;">{ach['description']}</div>
                <div style="color:#6366f1;font-size:0.75rem;font-weight:700;margin-top:0.5rem;">
                    {'✅ Earned' if earned else f'⚡ {ach.get("xp_reward",50)} XP'}
                </div>
            </div>
            """, unsafe_allow_html=True)
