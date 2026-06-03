"""
Page 11 — Performance Analytics
Detailed tracking of mock interview performance with complex Plotly charts and report export.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, kpi_card, render_sidebar_nav,
    render_ai_provider_selector, empty_state
)
from src.components.charts import (
    radar_chart, performance_line_chart, score_bar_chart, pie_chart, activity_heatmap
)
from src.database.supabase_client import db_select, get_performance_history

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("Performance Analytics", "Detailed tracking and trend analysis of your preparation stats", "trending_up")

# ── Data Fetching ─────────────────────────────────────────────────────────────
interviews = db_select("interviews", {"user_id": user_id, "status": "completed"}, order="created_at.desc")
coding_sessions = db_select("coding_sessions", {"user_id": user_id}, order="created_at.desc")
performance_history = get_performance_history(user_id, days=60)

if interviews or coding_sessions:
    # Aggregates
    total_ivs = len(interviews)
    avg_score = sum(i.get("overall_score", 0) for i in interviews) / max(total_ivs, 1)
    avg_tech = sum(i.get("technical_score", 0) for i in interviews) / max(total_ivs, 1)
    avg_hr = sum(i.get("hr_score", 0) for i in interviews) / max(total_ivs, 1)
    avg_comm = sum(i.get("communication_score", 0) for i in interviews) / max(total_ivs, 1)
    
    solved_coding = sum(1 for c in coding_sessions if c.get("status") == "solved")
    
    st.markdown("### 📊 Performance Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("gps_fixed", "Overall Average", f"{avg_score:.1f}%", f"across {total_ivs} interviews", "#6366f1"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("terminal", "Technical Average", f"{avg_tech:.1f}%", "domain specific", "#06b6d4"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("handshake", "HR Average", f"{avg_hr:.1f}%", "behavioral fit", "#8b5cf6"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("lightbulb", "Coding Problems", f"{solved_coding}", f"out of {len(coding_sessions)} attempted", "#22c55e"), unsafe_allow_html=True)
    
    # ── Charts ────────────────────────────────────────────────────────────────
    st.markdown("### 📉 Analysis Charts")
    
    ch_col1, ch_col2 = st.columns(2)
    with ch_col1:
        # Score distribution
        scores_breakdown = {
            "Overall": avg_score,
            "Technical": avg_tech,
            "HR": avg_hr,
            "Communication": avg_comm,
            "Coding": sum(c.get("overall_score", 0) for c in coding_sessions) / max(len(coding_sessions), 1),
        }
        st.plotly_chart(score_bar_chart(scores_breakdown, "Average Scores by Category"), use_container_width=True, config={"displayModeBar": False})
        
    with ch_col2:
        # Radar chart
        st.plotly_chart(radar_chart(scores_breakdown, "Core Interview Competencies"), use_container_width=True, config={"displayModeBar": False})
        
    # Line trend chart
    if len(performance_history) > 1:
        st.plotly_chart(performance_line_chart(performance_history, "Performance Score Trend Over Time"), use_container_width=True, config={"displayModeBar": False})
    
    # Heatmap & Type distribution
    st.markdown("### 📅 Activity & Breakdown")
    ch_col3, ch_col4 = st.columns([2, 1])
    with ch_col3:
        if performance_history:
            st.plotly_chart(activity_heatmap(performance_history, "Daily Interview Completion Activity"), use_container_width=True, config={"displayModeBar": False})
    with ch_col4:
        # Pie chart of interview types
        type_counts = {}
        for iv in interviews:
            itype = iv.get("interview_type", "other").replace("_", " ").title()
            type_counts[itype] = type_counts.get(itype, 0) + 1
        
        if type_counts:
            st.plotly_chart(pie_chart(list(type_counts.keys()), list(type_counts.values()), "Completed Interview Types"), use_container_width=True, config={"displayModeBar": False})
            
    # Export csv
    st.markdown("---")
    st.markdown("### 📥 Export Preparation Data")
    if interviews:
        df_ivs = pd.DataFrame(interviews)
        csv_data = df_ivs.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export Completed Interviews (CSV)",
            data=csv_data,
            file_name="interview_history.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    empty_state("trending_up", "No Performance Data", "Complete a mock interview or coding session to populate analytics!", "Go to Mock Interview →")
