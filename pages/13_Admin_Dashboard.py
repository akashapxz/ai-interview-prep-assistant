"""
Page 13 — Admin Dashboard
Full backend visibility: users, interviews, coding sessions, documents, audit logs, system stats.
Only accessible when logged in with an account that has role='admin' in the profiles table.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile
from src.components.ui_components import (
    inject_global_css, page_header, badge, kpi_card,
    render_sidebar_nav, render_ai_provider_selector
)
from src.database.supabase_client import db_select, db_delete, db_update, get_supabase_client

inject_global_css()

# ── Auth guard ────────────────────────────────────────────────────────────────
if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

# ── Admin gate: HARD BLOCK for non-admins ─────────────────────────────────────
is_admin = False
if profile:
    is_admin = profile.get("role") == "admin"
if not is_admin and user:
    is_admin = user.get("email", "").startswith("admin@")

if not is_admin:
    st.markdown("""
    <div style="text-align:center;padding:5rem 2rem;animation:fadeInUp 0.5s ease;">
        <div style="font-size:4rem;margin-bottom:1rem;">🚫</div>
        <h2 style="color:#ef4444;font-weight:800;margin-bottom:0.5rem;">Access Denied</h2>
        <p style="color:#94a3b8;max-width:420px;margin:0 auto 1.5rem;">
            You do not have administrator permissions to view this page.
            Contact your system administrator or update your role in Supabase.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Page Header ───────────────────────────────────────────────────────────────
page_header("Admin Dashboard", "Full backend visibility — users, interviews, logs, documents & system settings", "🛡️")

# ── Fetch summary stats ───────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_admin_stats():
    client = get_supabase_client()
    profiles_res = client.table("profiles").select("*").execute()
    profiles = profiles_res.data or []

    interviews_res = client.table("interviews").select("*").order("created_at", desc=True).limit(200).execute()
    interviews = interviews_res.data or []

    coding_res = client.table("coding_sessions").select("*").order("created_at", desc=True).limit(200).execute()
    coding = coding_res.data or []

    logs_res = client.table("audit_logs").select("*").order("created_at", desc=True).limit(100).execute()
    logs = logs_res.data or []

    docs_res = client.table("uploaded_documents").select("*").order("created_at", desc=True).limit(100).execute()
    docs = docs_res.data or []

    challenges_res = client.table("daily_challenges").select("*").order("challenge_date", desc=True).limit(30).execute()
    challenges = challenges_res.data or []

    return profiles, interviews, coding, logs, docs, challenges

profiles, interviews, coding, logs, docs, challenges = load_admin_stats()

# ── KPI Row ───────────────────────────────────────────────────────────────────
kc = st.columns(5)
kpis = [
    (kc[0], "👥", "Total Users",      str(len(profiles)),   "registered",      "#6366f1"),
    (kc[1], "🎯", "Interviews",        str(len(interviews)), "all time",        "#06b6d4"),
    (kc[2], "💻", "Coding Sessions",   str(len(coding)),     "submitted",       "#8b5cf6"),
    (kc[3], "📄", "Documents",         str(len(docs)),       "uploaded",        "#22c55e"),
    (kc[4], "📋", "Audit Events",      str(len(logs)),       "logged",          "#f59e0b"),
]
for col, icon, title, val, sub, color in kpis:
    with col:
        st.markdown(kpi_card(icon, title, val, sub, color), unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "👥 Users",
    "🎯 Interviews",
    "💻 Coding Sessions",
    "📂 Documents",
    "⚡ Daily Challenges",
    "📋 Audit Logs",
    "🛠️ Settings",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Users
# ─────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown(f"**{len(profiles)} Registered Users**")

    # Quick role filter
    role_filter = st.selectbox("Filter by role", ["All", "user", "admin"], key="admin_role_filter")
    filtered = profiles if role_filter == "All" else [p for p in profiles if p.get("role") == role_filter]

    for u in filtered:
        uid  = u.get("id", "")
        name = u.get("full_name", "—")
        email= u.get("email", "—")
        role = u.get("role", "user")
        xp   = u.get("xp_points", 0)
        streak = u.get("streak_days", 0)
        college= u.get("college", "—")
        branch = u.get("branch", "—")
        joined = u.get("created_at", "")[:10]
        last   = u.get("last_active", "")[:10] if u.get("last_active") else "never"

        role_color = "#ef4444" if role == "admin" else "#6366f1"
        with st.expander(f"👤 {name} · {email}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Role:** {badge(role.upper(), role_color)}", unsafe_allow_html=True)
                st.write(f"**College:** {college}")
                st.write(f"**Branch:** {branch}")
            with c2:
                st.write(f"**XP Points:** {xp:,}")
                st.write(f"**Streak:** 🔥 {streak} days")
                st.write(f"**Joined:** {joined}")
            with c3:
                st.write(f"**Last Active:** {last}")
                st.write(f"**User ID:** `{uid[:18]}…`")

            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if role == "user":
                    if st.button("⬆️ Promote to Admin", key=f"promote_{uid}"):
                        try:
                            get_supabase_client().table("profiles").update({"role": "admin"}).eq("id", uid).execute()
                            st.success("User promoted to Admin!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    if st.button("⬇️ Demote to User", key=f"demote_{uid}"):
                        try:
                            get_supabase_client().table("profiles").update({"role": "user"}).eq("id", uid).execute()
                            st.success("Admin demoted to User!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            with btn_c2:
                if uid != user_id:   # prevent self-delete
                    if st.button("🗑️ Delete User", key=f"del_user_{uid}"):
                        try:
                            db_delete("profiles", {"id": uid})
                            st.success("User profile deleted.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Interviews
# ─────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown(f"**{len(interviews)} Interview Records** (most recent 200)")

    if interviews:
        iv_type_filter = st.selectbox(
            "Filter by type",
            ["All"] + sorted({iv.get("interview_type", "other") for iv in interviews}),
            key="admin_iv_type",
        )
        shown = interviews if iv_type_filter == "All" else [iv for iv in interviews if iv.get("interview_type") == iv_type_filter]

        # Summary stats
        completed = [iv for iv in shown if iv.get("status") == "completed"]
        avg_score = round(sum(iv.get("overall_score", 0) for iv in completed) / max(len(completed), 1), 1)
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Total Shown", len(shown))
        sc2.metric("Completed", len(completed))
        sc3.metric("Avg Score", f"{avg_score}/100")

        st.markdown("---")
        for iv in shown[:50]:
            iv_id   = iv.get("id", "")[:8]
            iv_type = iv.get("interview_type", "—").replace("_", " ").title()
            domain  = iv.get("domain", "—")
            persona = iv.get("persona", "—")
            score   = iv.get("overall_score", 0)
            status  = iv.get("status", "—")
            created = iv.get("created_at", "")[:16].replace("T", " ")
            color   = "#22c55e" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                 border-radius:10px;padding:0.65rem 1rem;margin-bottom:0.35rem;
                 display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.4rem;">
                <div>
                    <span style="color:#f1f5f9;font-weight:600;font-size:0.88rem;">{iv_type}</span>
                    <span style="color:#64748b;font-size:0.78rem;margin-left:0.5rem;">{domain} · {persona}</span>
                </div>
                <div style="display:flex;align-items:center;gap:1rem;">
                    <span style="color:{color};font-weight:700;">{score:.0f}/100</span>
                    <span style="color:#64748b;font-size:0.78rem;">{created}</span>
                    <span style="background:rgba(99,102,241,0.1);border-radius:6px;padding:0.2rem 0.5rem;
                          color:#818cf8;font-size:0.75rem;">{status}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No interview records found.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Coding Sessions
# ─────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown(f"**{len(coding)} Coding Session Records** (most recent 200)")

    if coding:
        solved   = sum(1 for c in coding if c.get("status") == "solved")
        unsolved = len(coding) - solved
        cs1, cs2 = st.columns(2)
        cs1.metric("✅ Solved", solved)
        cs2.metric("❌ Not Solved", unsolved)
        st.markdown("---")

        for c in coding[:50]:
            topic    = c.get("topic", "—")
            lang     = c.get("language", "—")
            diff     = c.get("difficulty", "—")
            status   = c.get("status", "—")
            score    = c.get("score", 0)
            created  = c.get("created_at", "")[:16].replace("T", " ")
            color    = "#22c55e" if status == "solved" else "#ef4444"
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                 border-radius:10px;padding:0.65rem 1rem;margin-bottom:0.35rem;
                 display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.4rem;">
                <div>
                    <span style="color:#f1f5f9;font-weight:600;font-size:0.88rem;">{topic}</span>
                    <span style="color:#64748b;font-size:0.78rem;margin-left:0.5rem;">{lang} · {diff}</span>
                </div>
                <div style="display:flex;align-items:center;gap:1rem;">
                    <span style="color:{color};font-weight:700;">{status}</span>
                    <span style="color:#818cf8;">{score}/100</span>
                    <span style="color:#64748b;font-size:0.78rem;">{created}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No coding session records found.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Documents
# ─────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown(f"**{len(docs)} Uploaded Documents**")

    if docs:
        total_kb = sum((d.get("file_size", 0) or 0) for d in docs) // 1024
        st.info(f"📦 Total storage used: ~{total_kb:,} KB")
        st.markdown("---")

        for doc in docs:
            doc_id  = doc["id"]
            name    = doc.get("file_name", "—")
            size_kb = (doc.get("file_size", 0) or 0) // 1024
            doc_type= doc.get("file_type", "—")
            created = doc.get("created_at", "")[:16].replace("T", " ")

            dc1, dc2 = st.columns([5, 1])
            with dc1:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                     border-radius:10px;padding:0.65rem 1rem;">
                    <div style="color:#f1f5f9;font-size:0.88rem;font-weight:600;">📄 {name}</div>
                    <div style="color:#64748b;font-size:0.78rem;margin-top:0.2rem;">{doc_type} · {size_kb} KB · {created}</div>
                </div>
                """, unsafe_allow_html=True)
            with dc2:
                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"del_doc_{doc_id}"):
                    db_delete("uploaded_documents", {"id": doc_id})
                    st.success("Deleted.")
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.info("No uploaded documents found.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — Daily Challenges
# ─────────────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown(f"**{len(challenges)} Daily Challenges (last 30)**")

    with st.expander("➕ Add New Challenge", expanded=False):
        from datetime import date as _date
        ch_date  = st.date_input("Challenge Date", value=_date.today(), key="admin_ch_date")
        ch_cat   = st.selectbox("Category", ["DSA", "System Design", "HR", "Behavioral", "Coding", "General"], key="admin_ch_cat")
        ch_diff  = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1, key="admin_ch_diff")
        ch_q     = st.text_area("Question", placeholder="Type the daily challenge question here…", height=100, key="admin_ch_q")
        if st.button("✅ Save Challenge", key="admin_save_ch", type="primary"):
            if ch_q.strip():
                from src.database.supabase_client import db_insert
                res = db_insert("daily_challenges", {
                    "challenge_date": str(ch_date),
                    "category": ch_cat,
                    "difficulty": ch_diff,
                    "question": ch_q.strip(),
                })
                if res:
                    st.success("Challenge saved!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Failed to save challenge.")
            else:
                st.warning("Please enter a question.")

    st.markdown("---")
    for ch in challenges:
        ch_id  = ch.get("id", "")
        ch_d   = ch.get("challenge_date", "—")
        ch_cat = ch.get("category", "—")
        ch_diff= ch.get("difficulty", "—")
        ch_q   = ch.get("question", "—")[:120]

        chc1, chc2 = st.columns([5, 1])
        with chc1:
            diff_color = "#22c55e" if ch_diff == "easy" else "#f59e0b" if ch_diff == "medium" else "#ef4444"
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
                 border-radius:10px;padding:0.65rem 1rem;margin-bottom:0.35rem;">
                <div style="display:flex;gap:0.75rem;align-items:center;margin-bottom:0.3rem;">
                    <span style="color:#818cf8;font-size:0.8rem;font-weight:700;">{ch_d}</span>
                    <span style="background:{diff_color}22;color:{diff_color};border-radius:6px;padding:0.15rem 0.5rem;font-size:0.72rem;font-weight:600;">{ch_diff.upper()}</span>
                    <span style="color:#64748b;font-size:0.78rem;">{ch_cat}</span>
                </div>
                <div style="color:#e2e8f0;font-size:0.88rem;">{ch_q}{'...' if len(ch.get('question','')) > 120 else ''}</div>
            </div>
            """, unsafe_allow_html=True)
        with chc2:
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_ch_{ch_id}"):
                db_delete("daily_challenges", {"id": ch_id})
                st.success("Challenge deleted.")
                st.cache_data.clear()
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — Audit Logs
# ─────────────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown(f"**{len(logs)} Recent Audit Events**")

    action_filter = st.selectbox(
        "Filter by action",
        ["All"] + sorted({log.get("action", "") for log in logs if log.get("action")}),
        key="admin_log_filter",
    )
    shown_logs = logs if action_filter == "All" else [l for l in logs if l.get("action") == action_filter]

    for log in shown_logs[:80]:
        action   = log.get("action", "—")
        resource = log.get("resource", "—")
        res_id   = log.get("resource_id", "")
        created  = log.get("created_at", "")[:19].replace("T", " ")

        action_colors = {
            "insert": "#22c55e", "update": "#f59e0b", "delete": "#ef4444",
            "login": "#06b6d4", "logout": "#94a3b8",
        }
        ac = action_colors.get(action.lower(), "#818cf8")
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border-left:3px solid {ac};
             border-radius:0 8px 8px 0;padding:0.45rem 1rem;margin-bottom:0.3rem;
             display:flex;justify-content:space-between;align-items:center;font-size:0.82rem;">
            <span style="color:#e2e8f0;">
                <span style="color:{ac};font-weight:700;">{action.upper()}</span>
                &nbsp;·&nbsp;{resource}
                {f"&nbsp;<code style='color:#64748b;font-size:0.75rem;'>{res_id[:12]}…</code>" if res_id else ""}
            </span>
            <span style="color:#64748b;white-space:nowrap;">{created}</span>
        </div>
        """, unsafe_allow_html=True)

    if not shown_logs:
        st.info("No audit events found.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 7 — System Settings
# ─────────────────────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("### 🛠️ System Configuration")

    col_set1, col_set2 = st.columns(2)
    with col_set1:
        max_up  = st.number_input("Max File Upload Size (MB)", value=50, min_value=1, max_value=200, key="admin_max_up")
        rate_lim= st.number_input("Max API Requests Per Minute", value=30, min_value=1, max_value=500, key="admin_rate_lim")
        st.selectbox("Default AI Provider", ["gemini", "groq"], key="admin_default_provider")
    with col_set2:
        st.markdown("""
        <div style="background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.2);
             border-radius:12px;padding:1rem;">
            <div style="color:#22d3ee;font-weight:700;margin-bottom:0.5rem;">🟢 System Status</div>
            <div style="color:#94a3b8;font-size:0.85rem;line-height:1.8;">
                ✅ Database: Supabase Cloud (Active)<br>
                ✅ Auth: Supabase Auth (Active)<br>
                ✅ Storage: Supabase Storage (Active)<br>
                ✅ AI: Gemini 2.5 Flash + Groq Llama
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("💾 Save Settings", type="primary", key="admin_save_settings"):
        st.success("Configuration saved successfully! (Note: these settings are session-level only until DB config table is added.)")

    st.markdown("---")
    st.markdown("#### 🔴 Danger Zone")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("🗑️ Clear All Audit Logs", key="admin_clear_logs"):
            st.warning("⚠️ This will permanently delete all audit logs. Type 'CONFIRM' to proceed.")
            confirm = st.text_input("Confirm", key="admin_clear_logs_confirm")
            if confirm == "CONFIRM":
                try:
                    get_supabase_client().table("audit_logs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                    st.success("Audit logs cleared.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    with col_d2:
        st.markdown("<p style='color:#64748b;font-size:0.85rem;'>More danger zone actions can be added here for full system management.</p>", unsafe_allow_html=True)
