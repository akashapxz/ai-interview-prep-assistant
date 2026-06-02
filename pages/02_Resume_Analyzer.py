"""
Page 02 — Resume Analyzer
Upload PDF/DOCX, extract text, AI analysis, ATS score, improvement tips, PDF report download.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, kpi_card, badge, render_sidebar_nav,
    render_ai_provider_selector, empty_state, feedback_card, glass_card
)
from src.components.charts import score_bar_chart, pie_chart
from src.database.supabase_client import db_insert, db_select, upload_file_to_storage
from src.utils.pdf_processor import extract_text, validate_file
from src.utils.report_generator import generate_resume_report
from src.ai.gemini_client import analyze_resume
from src.utils.helpers import score_to_emoji

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]

page_header("Resume Analyzer", "AI-powered resume analysis with ATS scoring and interview question generation", "📄")

tabs = st.tabs(["📤 Upload & Analyze", "📋 Past Resumes", "🎯 Interview Questions"])

# ── TAB 1: Upload ─────────────────────────────────────────────────────────────
with tabs[0]:
    col_upload, col_settings = st.columns([2, 1])

    with col_upload:
        st.markdown("#### Upload Your Resume")
        uploaded_file = st.file_uploader(
            "Drop your resume here",
            type=["pdf", "docx", "txt"],
            help="Supported: PDF, DOCX, TXT (max 10MB)",
            key="resume_uploader"
        )

    with col_settings:
        st.markdown("#### Analysis Settings")
        target_role = st.text_input("Target Role (optional)", placeholder="e.g. Software Engineer at Google")
        include_questions = st.checkbox("Generate interview questions", value=True)
        analyze_btn = st.button("🚀 Analyze Resume", use_container_width=True, type="primary")

    if uploaded_file and analyze_btn:
        file_bytes = uploaded_file.read()
        valid, msg = validate_file(file_bytes, uploaded_file.name)
        if not valid:
            st.error(msg)
        else:
            with st.spinner("🔍 Extracting text from resume..."):
                text = extract_text(file_bytes, uploaded_file.name)

            if not text or len(text) < 50:
                st.error("Could not extract text. Please ensure the PDF/DOCX is not scanned/image-based.")
            else:
                with st.spinner("🤖 AI is analyzing your resume..."):
                    result = analyze_resume(text, target_role)

                if not result:
                    st.error("AI analysis failed. Please check your API key and try again.")
                else:
                    # Upload to Supabase Storage
                    with st.spinner("💾 Saving to cloud..."):
                        storage_path = f"{user_id}/{uploaded_file.name}"
                        file_url = upload_file_to_storage("resumes", storage_path, file_bytes, "application/pdf")
                        if not file_url:
                            file_url = ""

                        # Save to DB
                        resume_row = db_insert("resumes", {
                            "user_id": user_id,
                            "file_name": uploaded_file.name,
                            "file_url": file_url,
                            "file_size": len(file_bytes),
                            "parsed_text": text[:5000],
                            "skills": result.get("skills", []),
                            "education": result.get("education", []),
                            "experience": result.get("experience", []),
                            "projects": result.get("projects", []),
                            "certifications": result.get("certifications", []),
                            "summary": result.get("summary", ""),
                            "ats_score": result.get("ats_score", 0),
                            "readiness_score": result.get("readiness_score", 0),
                            "strengths": result.get("strengths", []),
                            "weaknesses": result.get("weaknesses", []),
                            "recommendations": result.get("recommendations", []),
                        })

                    st.session_state["last_resume_analysis"] = result
                    st.session_state["last_resume_text"] = text
                    st.success("✅ Resume analyzed successfully!")

                    # ── Results Display ──────────────────────────────────────
                    st.markdown("---")
                    st.markdown("### 📊 Analysis Results")

                    # Scores
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1:
                        ats = result.get("ats_score", 0)
                        color = "#22c55e" if ats >= 75 else "#f59e0b" if ats >= 50 else "#ef4444"
                        st.markdown(kpi_card("🤖", "ATS Score", f"{ats}", "Applicant Tracking System", color), unsafe_allow_html=True)
                    with sc2:
                        rdy = result.get("readiness_score", 0)
                        color2 = "#22c55e" if rdy >= 75 else "#f59e0b" if rdy >= 50 else "#ef4444"
                        st.markdown(kpi_card("🎯", "Readiness Score", f"{rdy}", "Interview Ready", color2), unsafe_allow_html=True)
                    with sc3:
                        skill_count = len(result.get("skills", []))
                        st.markdown(kpi_card("⚡", "Skills Found", str(skill_count), "detected skills", "#6366f1"), unsafe_allow_html=True)

                    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

                    # Summary
                    if result.get("summary"):
                        st.markdown("**📝 Professional Summary**")
                        st.markdown(f'<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:1rem;color:#e2e8f0;line-height:1.7;">{result["summary"]}</div>', unsafe_allow_html=True)
                        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

                    col_l, col_r = st.columns(2)
                    with col_l:
                        # Skills
                        st.markdown("**⚡ Identified Skills**")
                        skills_html = " ".join(badge(s, "#6366f1") for s in result.get("skills", [])[:20])
                        st.markdown(f'<div style="padding:0.5rem 0;">{skills_html}</div>', unsafe_allow_html=True)

                        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

                        # Strengths
                        st.markdown("**💪 Strengths**")
                        for s in result.get("strengths", [])[:5]:
                            st.markdown(f'<div style="color:#4ade80;padding:0.2rem 0;">✓ {s}</div>', unsafe_allow_html=True)

                    with col_r:
                        # Missing Skills
                        st.markdown("**⚠️ Missing / Recommended Skills**")
                        for s in result.get("missing_skills", [])[:8]:
                            st.markdown(f'<div style="color:#f87171;padding:0.2rem 0;">→ {s}</div>', unsafe_allow_html=True)

                        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

                        # Recommendations
                        st.markdown("**💡 Recommendations**")
                        for i, rec in enumerate(result.get("recommendations", [])[:5], 1):
                            st.markdown(f'<div style="color:#fbbf24;padding:0.2rem 0;">{i}. {rec}</div>', unsafe_allow_html=True)

                    # Education & Experience
                    with st.expander("🎓 Education & Experience Details"):
                        ed_col, exp_col = st.columns(2)
                        with ed_col:
                            st.markdown("**Education**")
                            for edu in result.get("education", []):
                                st.markdown(f"""
                                <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:0.6rem;margin-bottom:0.4rem;">
                                    <div style="color:#f1f5f9;font-weight:600;">{edu.get('degree','')}</div>
                                    <div style="color:#94a3b8;font-size:0.85rem;">{edu.get('institution','')} · {edu.get('year','')}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        with exp_col:
                            st.markdown("**Experience**")
                            for exp in result.get("experience", []):
                                st.markdown(f"""
                                <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:0.6rem;margin-bottom:0.4rem;">
                                    <div style="color:#f1f5f9;font-weight:600;">{exp.get('role','')}</div>
                                    <div style="color:#94a3b8;font-size:0.85rem;">{exp.get('company','')} · {exp.get('duration','')}</div>
                                </div>
                                """, unsafe_allow_html=True)

                    # Download PDF Report
                    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
                    pdf_bytes = generate_resume_report(result, profile.get("full_name", "Candidate") if profile else "Candidate")
                    st.download_button(
                        "📥 Download Full PDF Report",
                        data=pdf_bytes,
                        file_name=f"resume_analysis_{uploaded_file.name.split('.')[0]}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

    elif not uploaded_file:
        empty_state("📄", "Upload Your Resume", "Support for PDF, DOCX, and TXT files up to 10MB", "👆 Drag & drop or click to browse")

    # Show cached result if available
    elif uploaded_file and not analyze_btn:
        st.info("👆 Click **Analyze Resume** to start the AI analysis.")


# ── TAB 2: Past Resumes ───────────────────────────────────────────────────────
with tabs[1]:
    past = db_select("resumes", {"user_id": user_id}, order="created_at.desc", limit=10)
    if past:
        for r in past:
            with st.expander(f"📄 {r['file_name']} — ATS: {r['ats_score']}/100 | {r['created_at'][:10]}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("ATS Score", f"{r['ats_score']}/100")
                c2.metric("Readiness", f"{r['readiness_score']}/100")
                c3.metric("Skills Found", len(r.get("skills") or []))
                if r.get("summary"):
                    st.write(r["summary"])
                if r.get("skills"):
                    skills_html = " ".join(badge(s) for s in (r["skills"] or [])[:15])
                    st.markdown(skills_html, unsafe_allow_html=True)
    else:
        empty_state("📋", "No resumes yet", "Upload your first resume above to get started!")


# ── TAB 3: Interview Questions ────────────────────────────────────────────────
with tabs[2]:
    result_cached = st.session_state.get("last_resume_analysis")
    if result_cached and result_cached.get("interview_questions"):
        st.markdown("#### 🎯 AI-Generated Interview Questions (from your resume)")
        for i, q in enumerate(result_cached["interview_questions"], 1):
            st.markdown(f"""
            <div style="
                background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
                border-radius:12px;padding:1rem;margin-bottom:0.75rem;
            ">
                <div style="color:#818cf8;font-size:0.8rem;font-weight:600;margin-bottom:0.3rem;">QUESTION {i}</div>
                <div style="color:#f1f5f9;line-height:1.6;">{q}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        empty_state("💬", "No questions yet", "Analyze a resume first to generate personalized interview questions.")
