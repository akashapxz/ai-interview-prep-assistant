"""
Page 15 — User Settings & Profile
Edit personal details, preferences, and account settings.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import (
    is_authenticated, get_current_user, get_current_profile,
    sign_out, update_profile
)
from src.components.ui_components import (
    inject_global_css, page_header, kpi_card,
    render_sidebar_nav, render_ai_provider_selector, success_banner
)
from src.database.supabase_client import get_supabase_client, award_xp

# st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user    = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("Settings & Profile", "Manage your account details and preferences", "settings")

tab_profile, tab_goals, tab_account = st.tabs([
    "👤 Profile Details",
    "🎯 Goals & Preferences",
    "🔐 Account Security",
])

# ── TAB 1: Profile Details ────────────────────────────────────────────────────
with tab_profile:
    st.markdown("### Personal Information")

    c1, c2 = st.columns(2)
    with c1:
        full_name = st.text_input(
            "Full Name",
            value=profile.get("full_name", "") if profile else "",
            placeholder="John Doe",
            key="s_name",
        )
        college = st.text_input(
            "College / University",
            value=profile.get("college", "") if profile else "",
            placeholder="MIT",
            key="s_college",
        )
        linkedin = st.text_input(
            "LinkedIn URL",
            value=profile.get("linkedin_url", "") if profile else "",
            placeholder="https://linkedin.com/in/yourname",
            key="s_linkedin",
        )
    with c2:
        branch = st.text_input(
            "Branch / Major",
            value=profile.get("branch", "") if profile else "",
            placeholder="Computer Science",
            key="s_branch",
        )
        grad_year = st.number_input(
            "Graduation Year",
            min_value=2020, max_value=2030,
            value=int(profile.get("graduation_year", 2025)) if profile and profile.get("graduation_year") else 2025,
            key="s_year",
        )
        github = st.text_input(
            "GitHub URL",
            value=profile.get("github_url", "") if profile else "",
            placeholder="https://github.com/yourname",
            key="s_github",
        )

    phone = st.text_input(
        "Phone Number (optional)",
        value=profile.get("phone", "") if profile else "",
        placeholder="+91 9876543210",
        key="s_phone",
    )

    if st.button("💾 Save Profile", type="primary", key="save_profile"):
        updates = {
            "full_name":      full_name,
            "college":        college,
            "branch":         branch,
            "graduation_year": grad_year,
            "linkedin_url":   linkedin,
            "github_url":     github,
            "phone":          phone,
        }
        ok, msg = update_profile(user_id, updates)
        if ok:
            success_banner("Profile updated successfully!")
        else:
            st.error(msg)

# ── TAB 2: Goals & Preferences ────────────────────────────────────────────────
with tab_goals:
    st.markdown("### Interview Goals")

    # Load existing preferences from company_preparation table
    from src.database.supabase_client import db_select, db_upsert
    pref_rows = db_select("company_preparation", {"user_id": user_id, "company_name": "__user_preferences__"})
    saved_prefs = pref_rows[0].get("metadata", {}) if pref_rows else {}

    target_companies = st.multiselect(
        "Target Companies",
        ["Google", "Amazon", "Microsoft", "Meta", "Apple",
         "Netflix", "Infosys", "TCS", "Wipro", "Accenture",
         "Flipkart", "Razorpay", "Zomato"],
        default=saved_prefs.get("target_companies", []),
        key="s_companies",
    )
    target_role = st.text_input(
        "Target Role",
        value=saved_prefs.get("target_role", ""),
        placeholder="e.g. Software Engineer, Data Scientist",
        key="s_role",
    )

    c1, c2 = st.columns(2)
    with c1:
        durations = ["1 week", "2 weeks", "1 month", "2 months", "3 months"]
        saved_dur = saved_prefs.get("prep_duration", "1 month")
        dur_idx = durations.index(saved_dur) if saved_dur in durations else 2
        prep_duration = st.selectbox(
            "Preparation Duration",
            durations,
            index=dur_idx,
            key="s_duration",
        )
    with c2:
        daily_goal = st.slider(
            "Daily Practice Goal (minutes)",
            min_value=15, max_value=180, 
            value=int(saved_prefs.get("daily_goal_min", 60)), 
            step=15,
            key="s_daily_goal",
        )

    focus_areas = st.multiselect(
        "Focus Areas",
        ["DSA", "DBMS", "OOP", "OS", "Computer Networks",
         "Machine Learning", "System Design", "Web Development",
         "Cloud Computing", "Behavioral / HR"],
        default=saved_prefs.get("focus_areas", []),
        key="s_focus",
    )

    if st.button("💾 Save Goals", type="primary", key="save_goals"):
        prefs = {
            "target_companies": target_companies,
            "target_role":      target_role,
            "prep_duration":    prep_duration,
            "daily_goal_min":   daily_goal,
            "focus_areas":      focus_areas,
        }
        res = db_upsert("company_preparation", {
            "user_id": user_id,
            "company_name": "__user_preferences__",
            "metadata": prefs
        })
        if res:
            success_banner("Goals saved!")
        else:
            st.error("Failed to save goals. Please try again.")

# ── TAB 3: Account Security ───────────────────────────────────────────────────
with tab_account:
    st.markdown("### Account Information")

    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border);
         border-radius:14px;padding:1.25rem;margin-bottom:1.5rem;">
        <div style="color:var(--text-secondary);font-size:0.8rem;margin-bottom:0.25rem;">Logged In As</div>
        <div style="color:var(--text-primary);font-weight:600;font-size:1rem;">{user.get('email','')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Change Password")
    st.info("To change your password, use the **Reset** tab on the login screen after signing out.")

    st.markdown("---")
    st.markdown("### Danger Zone")
    st.warning("Deleting your account is permanent and cannot be undone.")
    if st.button("🗑️ Delete My Account", type="secondary", key="delete_account"):
        st.error("Account deletion is disabled in this demo. Contact your admin to remove the account.")

    st.markdown("---")
    st.markdown("### XP & Achievements")
    xp = profile.get("xp_points", 0) if profile else 0
    streak = profile.get("streak_days", 0) if profile else 0
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(kpi_card("bolt", "Total XP Points", f"{xp:,}", "earned through practice", "#6366f1"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("local_fire_department", "Current Streak", f"{streak} Days", "consecutive active days", "#f59e0b"), unsafe_allow_html=True)
