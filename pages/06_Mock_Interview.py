"""
Page 06 — AI Mock Interview Engine (Flagship Feature)
Full conversational AI mock interview with personas, follow-up questions, and final report.
"""

import streamlit as st
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.auth.supabase_auth import is_authenticated, get_current_user, get_current_profile, sign_out
from src.components.ui_components import (
    inject_global_css, page_header, badge, render_sidebar_nav,
    render_ai_provider_selector, empty_state
)
from src.components.charts import score_bar_chart, radar_chart
from src.database.supabase_client import db_insert, db_update, award_xp
from src.ai.gemini_client import generate_mock_question, generate_mock_report
from src.ai.prompts import PERSONA_TRAITS
from src.utils.helpers import SKILL_DOMAINS, COMPANIES, score_to_emoji, calculate_xp_for_interview
from src.utils.report_generator import generate_interview_report
from src.utils.helpers import generate_session_id

st.markdown('<!-- ' + st.get_option('theme.primaryColor') + ' -->' if False else '') # st.set_page_config commented out for navigation
inject_global_css()

if not is_authenticated():
    st.switch_page("app.py")

user = get_current_user()
profile = get_current_profile()
user_id = user["id"]
candidate_name = profile.get("full_name", "Candidate") if profile else "Candidate"

page_header("AI Mock Interview", "Realistic AI-powered interviews with multiple personas and a comprehensive final report", "🤖")

# ── PHASE 1: Setup ────────────────────────────────────────────────────────────
if not st.session_state.get("mock_active") and not st.session_state.get("mock_complete"):
    st.markdown("### ⚙️ Configure Your Interview")

    c1, c2 = st.columns(2)
    with c1:
        interview_type = st.selectbox(
            "Interview Type",
            ["Technical", "HR", "Coding", "Mixed"],
            key="mock_type",
            help="Select the type of interview you want to practice"
        )
        persona = st.selectbox(
            "AI Interviewer Persona",
            list(PERSONA_TRAITS.keys()),
            key="mock_persona"
        )
        persona_desc = {
            "Friendly Recruiter": "Warm and encouraging, focuses on fit",
            "Strict Recruiter": "Demanding and detail-oriented",
            "FAANG Interviewer": "Highly technical, scalability focus",
            "Startup Founder": "Fast-paced, execution-oriented",
            "HR Manager": "Soft skills and STAR method focused",
        }
        st.markdown(f'<div style="color:#64748b;font-size:0.85rem;margin-top:-0.5rem;">{persona_desc.get(persona,"")}</div>', unsafe_allow_html=True)

    with c2:
        domain = st.selectbox("Technical Domain", SKILL_DOMAINS, key="mock_domain")
        company = st.selectbox("Target Company (Optional)", ["General"] + COMPANIES, key="mock_company")
        difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], index=1, key="mock_difficulty")
        total_questions = st.slider("Number of Questions", 3, 15, 8, key="mock_total_q")

    # Preview card
    st.markdown(f"""
    <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);
         border-radius:14px;padding:1.25rem;margin:1rem 0;">
        <div style="color:#818cf8;font-weight:700;margin-bottom:0.5rem;">Interview Preview</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;">
            <div><span style="color:#64748b;font-size:0.8rem;">Type</span><br><span style="color:#f1f5f9;font-weight:600;">{interview_type}</span></div>
            <div><span style="color:#64748b;font-size:0.8rem;">Persona</span><br><span style="color:#f1f5f9;font-weight:600;">{persona}</span></div>
            <div><span style="color:#64748b;font-size:0.8rem;">Domain</span><br><span style="color:#f1f5f9;font-weight:600;">{domain}</span></div>
            <div><span style="color:#64748b;font-size:0.8rem;">Questions</span><br><span style="color:#f1f5f9;font-weight:600;">{total_questions}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Start Interview", type="primary", use_container_width=True, key="start_mock"):
        # Create interview record in DB
        interview_row = db_insert("interviews", {
            "user_id": user_id,
            "interview_type": interview_type.lower().replace(" ", "_"),
            "domain": domain,
            "company": company,
            "difficulty": difficulty.lower(),
            "persona": persona,
            "total_questions": total_questions,
            "status": "in_progress",
        })

        # Initialize session state
        st.session_state["mock_active"] = True
        st.session_state["mock_complete"] = False
        st.session_state["mock_interview_id"] = interview_row["id"] if interview_row else generate_session_id()
        st.session_state["mock_current_q"] = 0
        st.session_state["mock_qa_list"] = []   # list of {question, answer, score}
        st.session_state["mock_start_time"] = time.time()
        st.session_state["mock_type_val"] = interview_type
        st.session_state["mock_persona_val"] = persona
        st.session_state["mock_domain_val"] = domain
        st.session_state["mock_company_val"] = company
        st.session_state["mock_difficulty_val"] = difficulty
        st.rerun()


# ── PHASE 2: Active Interview ─────────────────────────────────────────────────
elif st.session_state.get("mock_active") and not st.session_state.get("mock_complete"):
    qa_list = st.session_state.get("mock_qa_list", [])
    current_q = st.session_state.get("mock_current_q", 0)
    total_q = st.session_state.get("mock_total_q", 8)
    persona = st.session_state.get("mock_persona_val", "Friendly Recruiter")
    interview_type = st.session_state.get("mock_type_val", "Technical")
    domain = st.session_state.get("mock_domain_val", "DSA")
    company = st.session_state.get("mock_company_val", "General")
    difficulty = st.session_state.get("mock_difficulty_val", "Medium")

    # Progress header
    st.markdown(f"""
    <div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
         border-radius:12px;padding:0.75rem 1.25rem;margin-bottom:1.5rem;
         display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
        <div style="display:flex;align-items:center;gap:1rem;">
            {badge(persona, '#6366f1')}
            {badge(interview_type, '#8b5cf6')}
            {badge(domain, '#06b6d4')}
        </div>
        <div style="color:#94a3b8;font-size:0.85rem;">Question {current_q + 1} of {total_q}</div>
    </div>
    """, unsafe_allow_html=True)

    # Progress bar
    st.progress((current_q) / total_q)

    # Chat transcript (previous Q&A)
    if qa_list:
        st.markdown("**📜 Interview Transcript**")
        for idx, qa in enumerate(qa_list):
            # AI question
            st.markdown(f"""
            <div style="display:flex;gap:0.75rem;margin-bottom:0.75rem;">
                <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                     display:flex;align-items:center;justify-content:center;font-size:1rem;flex-shrink:0;">🤖</div>
                <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);
                     border-radius:12px 12px 12px 4px;padding:0.75rem 1rem;flex:1;">
                    <div style="color:#818cf8;font-size:0.75rem;font-weight:600;margin-bottom:0.3rem;">{persona.upper()}</div>
                    <div style="color:#e2e8f0;line-height:1.6;">{qa.get('question','')}</div>
                </div>
            </div>
            <div style="display:flex;gap:0.75rem;margin-bottom:1rem;flex-direction:row-reverse;">
                <div style="width:36px;height:36px;border-radius:50%;background:rgba(6,182,212,0.2);
                     border:1px solid rgba(6,182,212,0.3);
                     display:flex;align-items:center;justify-content:center;font-size:0.85rem;flex-shrink:0;">
                     {candidate_name[0].upper()}</div>
                <div style="background:rgba(6,182,212,0.08);border:1px solid rgba(6,182,212,0.2);
                     border-radius:12px 12px 4px 12px;padding:0.75rem 1rem;flex:1;text-align:right;">
                    <div style="color:#06b6d4;font-size:0.75rem;font-weight:600;margin-bottom:0.3rem;">YOU</div>
                    <div style="color:#e2e8f0;line-height:1.6;">{qa.get('answer','')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Generate or use stored current question
    if "mock_current_question" not in st.session_state:
        context = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in qa_list[-3:]])
        with st.spinner(f"🤖 {persona} is thinking of the next question..."):
            q_result = generate_mock_question(
                persona=persona,
                interview_type=interview_type,
                company=company,
                candidate_name=candidate_name,
                domain=domain,
                difficulty=difficulty,
                current_q=current_q + 1,
                total_q=total_q,
                context=context or "This is the first question.",
                persona_traits=PERSONA_TRAITS.get(persona, ""),
            )
        if q_result:
            st.session_state["mock_current_question"] = q_result.get("question", "Tell me about yourself.")
            interviewer_comment = q_result.get("interviewer_comment", "")
            if interviewer_comment:
                st.markdown(f'<div style="color:#64748b;font-style:italic;margin-bottom:0.5rem;">"{interviewer_comment}"</div>', unsafe_allow_html=True)
        else:
            st.session_state["mock_current_question"] = "Can you tell me about your background and experience?"

    current_question = st.session_state["mock_current_question"]

    # Current question display
    st.markdown(f"""
    <div style="display:flex;gap:0.75rem;margin-bottom:1.5rem;">
        <div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#8b5cf6);
             display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0;
             box-shadow:0 0 20px rgba(99,102,241,0.4);">🤖</div>
        <div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);
             border-radius:12px 12px 12px 4px;padding:1rem 1.25rem;flex:1;
             animation:fadeInUp 0.4s ease;">
            <div style="color:#818cf8;font-size:0.75rem;font-weight:600;margin-bottom:0.4rem;">{persona.upper()} · Q{current_q+1}/{total_q}</div>
            <div style="color:#f1f5f9;font-size:1rem;line-height:1.65;">{current_question}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Answer input
    user_answer = st.text_area(
        "Your Answer",
        placeholder=f"Answer {persona}'s question naturally. Take your time to structure your thoughts...",
        height=150,
        key=f"mock_answer_{current_q}",
        label_visibility="collapsed",
    )

    col_submit, col_end = st.columns([3, 1])
    with col_submit:
        submit_answer = st.button("📤 Submit Answer & Next Question", type="primary", use_container_width=True, key="mock_submit")
    with col_end:
        end_interview = st.button("🏁 End Interview", use_container_width=True, key="mock_end")

    if submit_answer and user_answer.strip():
        # Save Q&A
        qa_list.append({"question": current_question, "answer": user_answer, "q_num": current_q + 1})
        st.session_state["mock_qa_list"] = qa_list
        st.session_state["mock_current_q"] = current_q + 1
        del st.session_state["mock_current_question"]

        if current_q + 1 >= total_q:
            st.session_state["mock_active"] = False
            st.session_state["mock_complete"] = True
        st.rerun()

    elif submit_answer and not user_answer.strip():
        st.warning("Please type your answer before submitting.")

    if end_interview:
        st.session_state["mock_active"] = False
        st.session_state["mock_complete"] = True
        st.rerun()


# ── PHASE 3: Final Report ─────────────────────────────────────────────────────
elif st.session_state.get("mock_complete"):
    qa_list = st.session_state.get("mock_qa_list", [])
    interview_type = st.session_state.get("mock_type_val", "Mixed")
    duration = int((time.time() - st.session_state.get("mock_start_time", time.time())) / 60)

    st.markdown("""
    <div style="text-align:center;padding:1.5rem 0;animation:fadeInUp 0.5s ease;">
        <div style="font-size:3rem;margin-bottom:0.5rem;">🎉</div>
        <h2 style="color:#f1f5f9;font-weight:800;">Interview Complete!</h2>
        <p style="color:#94a3b8;">Generating your comprehensive performance report...</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.get("mock_report"):
        transcript = "\n\n".join([f"Q{i+1}: {qa['question']}\nAnswer: {qa['answer']}" for i, qa in enumerate(qa_list)])
        with st.spinner("🤖 AI is generating your comprehensive report..."):
            report = generate_mock_report(interview_type, candidate_name, duration, len(qa_list), transcript)

        if report:
            st.session_state["mock_report"] = report
            # Update interview record
            interview_id = st.session_state.get("mock_interview_id")
            if interview_id:
                db_update("interviews", {"id": interview_id}, {
                    "status": "completed",
                    "overall_score": report.get("overall_score", 0),
                    "technical_score": report.get("technical_score", 0),
                    "hr_score": report.get("hr_score", 0),
                    "communication_score": report.get("communication_score", 0),
                    "confidence_score": report.get("confidence_score", 0),
                    "answered_questions": len(qa_list),
                    "duration_minutes": duration,
                    "feedback": report.get("performance_summary", ""),
                })
            xp = calculate_xp_for_interview(report.get("overall_score", 0), interview_type.lower())
            award_xp(user_id, xp)
        else:
            st.error("Failed to generate report. Please try again.")

    report = st.session_state.get("mock_report")
    if report:
        # Overall score hero
        overall = report.get("overall_score", 0)
        emoji = score_to_emoji(overall)
        readiness = report.get("interview_readiness", "Needs Practice")

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(139,92,246,0.1));
             border:1px solid rgba(99,102,241,0.3);border-radius:20px;padding:2rem;text-align:center;margin-bottom:2rem;">
            <div style="font-size:3.5rem;margin-bottom:0.5rem;">{emoji}</div>
            <div style="font-size:3.5rem;font-weight:900;color:#6366f1;line-height:1;">{overall:.0f}<span style="font-size:1.5rem;color:#94a3b8;">/100</span></div>
            <div style="color:#818cf8;font-size:1.1rem;font-weight:600;margin:0.5rem 0;">{readiness}</div>
            <div style="color:#64748b;">Duration: {duration} min · {len(qa_list)} questions answered</div>
        </div>
        """, unsafe_allow_html=True)

        # Score breakdown
        scores = {
            "Technical": report.get("technical_score", 0),
            "HR": report.get("hr_score", 0),
            "Communication": report.get("communication_score", 0),
            "Confidence": report.get("confidence_score", 0),
        }
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(score_bar_chart(scores, "Score Breakdown"), use_container_width=True, config={"displayModeBar": False})
        with c2:
            st.plotly_chart(radar_chart(scores, "Skill Distribution"), use_container_width=True, config={"displayModeBar": False})

        # Summary
        col_s, col_i = st.columns(2)
        with col_s:
            st.markdown("**💪 Strengths**")
            for s in report.get("strengths", []):
                st.markdown(f'<div style="color:#4ade80;padding:0.2rem 0;">✓ {s}</div>', unsafe_allow_html=True)
        with col_i:
            st.markdown("**📈 Areas to Improve**")
            for a in report.get("areas_for_improvement", []):
                st.markdown(f'<div style="color:#fbbf24;padding:0.2rem 0;">→ {a}</div>', unsafe_allow_html=True)

        # Performance summary
        if report.get("performance_summary"):
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:1rem;margin:1rem 0;">
                <div style="color:#94a3b8;font-size:0.85rem;margin-bottom:0.3rem;">AI Summary</div>
                <div style="color:#e2e8f0;line-height:1.65;">{report["performance_summary"]}</div>
            </div>
            """, unsafe_allow_html=True)

        # Hire recommendation
        hire = report.get("hire_recommendation", "")
        if hire:
            hire_colors = {"Strong Hire": "#22c55e", "Hire": "#4ade80", "No Hire": "#f97316", "Strong No Hire": "#ef4444"}
            hire_color = hire_colors.get(hire, "#6366f1")
            st.markdown(f'<div style="text-align:center;padding:0.75rem;background:rgba(255,255,255,0.04);border-radius:10px;color:{hire_color};font-weight:700;font-size:1.1rem;">Final Recommendation: {hire}</div>', unsafe_allow_html=True)

        # Q&A Breakdown
        with st.expander("📋 Question-by-Question Breakdown"):
            for qa in report.get("question_by_question", []):
                score_v = qa.get("score", 0)
                color = "#22c55e" if score_v >= 80 else "#f59e0b" if score_v >= 60 else "#ef4444"
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:0.6rem;margin-bottom:0.3rem;">
                    <div style="color:#e2e8f0;font-size:0.9rem;">{qa.get('question','')[:100]}</div>
                    <div style="color:{color};font-size:0.8rem;margin-top:0.2rem;">Score: {score_v}/100 · {qa.get('brief_feedback','')[:80]}</div>
                </div>
                """, unsafe_allow_html=True)

        # Next steps
        if report.get("next_steps"):
            st.markdown("**🗺️ Next Steps**")
            for i, step in enumerate(report["next_steps"], 1):
                st.markdown(f'<div style="color:#818cf8;padding:0.2rem 0;">{i}. {step}</div>', unsafe_allow_html=True)

        # Download PDF
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        col_dl, col_new = st.columns(2)
        with col_dl:
            pdf_bytes = generate_interview_report(report, candidate_name)
            st.download_button("📥 Download PDF Report", data=pdf_bytes,
                file_name=f"mock_interview_report_{interview_type.lower()}.pdf",
                mime="application/pdf", use_container_width=True)
        with col_new:
            if st.button("🔄 Start New Interview", use_container_width=True):
                for key in ["mock_active", "mock_complete", "mock_report", "mock_qa_list",
                             "mock_current_question", "mock_interview_id"]:
                    st.session_state.pop(key, None)
                st.rerun()
