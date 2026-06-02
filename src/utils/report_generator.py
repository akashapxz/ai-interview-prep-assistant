"""
PDF Report Generator — Generates professional interview reports as downloadable PDFs.
Uses FPDF2 for clean, branded report generation.
"""

import io
from datetime import datetime
from typing import Dict, Any, Optional

from fpdf import FPDF
from src.utils.helpers import score_to_grade, score_to_emoji


class InterviewReportPDF(FPDF):
    """Custom FPDF class with branded header/footer."""

    def __init__(self, candidate_name: str):
        super().__init__()
        self.candidate_name = candidate_name
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_fill_color(99, 102, 241)   # indigo
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 18, "  AI Interview Preparation Assistant", ln=True, align="L")
        self.set_text_color(30, 30, 30)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()} | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | AI Interview Prep", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(238, 240, 255)
        self.set_text_color(99, 102, 241)
        self.cell(0, 9, f"  {title}", ln=True, fill=True)
        self.set_text_color(30, 30, 30)
        self.ln(2)

    def score_badge(self, label: str, score: float, x: float, y: float, w: float = 45, h: float = 22):
        r, g, b = (34, 197, 94) if score >= 80 else (245, 158, 11) if score >= 60 else (239, 68, 68)
        self.set_xy(x, y)
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(w, h // 2, f"{score:.0f}/100", border=0, align="C", fill=True, ln=True)
        self.set_xy(x, y + h // 2)
        self.set_fill_color(r - 20, g - 20, b - 20)
        self.set_font("Helvetica", "", 8)
        self.cell(w, h // 2, label, border=0, align="C", fill=True, ln=True)
        self.set_text_color(30, 30, 30)


def generate_interview_report(report_data: Dict[str, Any], candidate_name: str) -> bytes:
    """
    Generate a professional PDF report from interview results.
    Returns PDF as bytes (ready for st.download_button).
    """
    pdf = InterviewReportPDF(candidate_name)
    pdf.add_page()

    # ── Title block ──────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 50)
    pdf.cell(0, 12, "Interview Performance Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 120)
    pdf.cell(0, 7, f"Candidate: {candidate_name}  |  Date: {datetime.now().strftime('%B %d, %Y')}", ln=True, align="C")
    pdf.ln(6)

    # ── Score badges ─────────────────────────────────────────────
    pdf.section_title("Overall Performance")
    pdf.ln(3)
    scores = [
        ("Overall", report_data.get("overall_score", 0)),
        ("Technical", report_data.get("technical_score", 0)),
        ("Communication", report_data.get("communication_score", 0)),
        ("Confidence", report_data.get("confidence_score", 0)),
    ]
    start_x = 15
    for i, (label, score) in enumerate(scores):
        pdf.score_badge(label, score, start_x + i * 48, pdf.get_y(), 44, 22)
    pdf.ln(28)

    # ── Readiness ────────────────────────────────────────────────
    readiness = report_data.get("interview_readiness", "Needs Practice")
    grade = score_to_grade(report_data.get("overall_score", 0))
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Grade: {grade}   |   Readiness: {readiness}", ln=True)
    pdf.ln(3)

    # ── Performance Summary ───────────────────────────────────────
    pdf.section_title("Performance Summary")
    pdf.set_font("Helvetica", "", 10)
    summary = report_data.get("performance_summary", "No summary available.")
    pdf.multi_cell(0, 6, summary)
    pdf.ln(3)

    # ── Strengths ─────────────────────────────────────────────────
    pdf.section_title("Key Strengths")
    pdf.set_font("Helvetica", "", 10)
    for s in report_data.get("strengths", [])[:5]:
        pdf.cell(8, 6, "", ln=False)
        pdf.cell(0, 6, f"-  {s}", ln=True)
    pdf.ln(2)

    # ── Areas for Improvement ────────────────────────────────────
    pdf.section_title("Areas for Improvement")
    pdf.set_font("Helvetica", "", 10)
    for area in report_data.get("areas_for_improvement", [])[:5]:
        pdf.cell(8, 6, "", ln=False)
        pdf.cell(0, 6, f"-  {area}", ln=True)
    pdf.ln(2)

    # ── Next Steps ────────────────────────────────────────────────
    pdf.section_title("Recommended Next Steps")
    pdf.set_font("Helvetica", "", 10)
    for i, step in enumerate(report_data.get("next_steps", [])[:5], 1):
        pdf.cell(0, 6, f"{i}. {step}", ln=True)
    pdf.ln(2)

    # ── Q&A Breakdown ────────────────────────────────────────────
    if report_data.get("question_by_question"):
        pdf.add_page()
        pdf.section_title("Question-by-Question Breakdown")
        pdf.set_font("Helvetica", "", 10)
        for i, qa in enumerate(report_data["question_by_question"][:10], 1):
            pdf.set_font("Helvetica", "B", 10)
            q_text = qa.get("question", "")[:120] + ("..." if len(qa.get("question", "")) > 120 else "")
            pdf.multi_cell(0, 6, f"Q{i}. {q_text}")
            pdf.set_font("Helvetica", "", 10)
            score_val = qa.get("score", 0)
            pdf.cell(0, 6, f"     Score: {score_val}/100  |  {qa.get('brief_feedback', '')[:80]}", ln=True)
            pdf.ln(2)

    # ── Hire Recommendation ──────────────────────────────────────
    hire_rec = report_data.get("hire_recommendation", "")
    if hire_rec:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(99, 102, 241)
        pdf.cell(0, 8, f"Final Recommendation: {hire_rec}", ln=True, align="C")

    return bytes(pdf.output())


def generate_resume_report(resume_data: Dict, candidate_name: str) -> bytes:
    """Generate a professional resume analysis PDF report."""
    pdf = InterviewReportPDF(candidate_name)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 50)
    pdf.cell(0, 12, "Resume Analysis Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 120)
    pdf.cell(0, 7, f"Candidate: {candidate_name}  |  Date: {datetime.now().strftime('%B %d, %Y')}", ln=True, align="C")
    pdf.ln(6)

    # ATS Score
    pdf.section_title("Resume Scores")
    pdf.ln(3)
    pdf.score_badge("ATS Score", resume_data.get("ats_score", 0), 15, pdf.get_y(), 60, 22)
    pdf.score_badge("Readiness", resume_data.get("readiness_score", 0), 78, pdf.get_y() - 22, 60, 22)
    pdf.ln(28)

    # Summary
    pdf.section_title("Professional Summary")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, resume_data.get("summary", ""))
    pdf.ln(2)

    # Skills
    pdf.section_title("Identified Skills")
    pdf.set_font("Helvetica", "", 10)
    skills = ", ".join(resume_data.get("skills", []))
    pdf.multi_cell(0, 6, skills or "No skills extracted")
    pdf.ln(2)

    # Strengths
    pdf.section_title("Strengths")
    for s in resume_data.get("strengths", [])[:5]:
        pdf.cell(0, 6, f"-  {s}", ln=True)
    pdf.ln(2)

    # Missing Skills
    pdf.section_title("Missing / Recommended Skills")
    for s in resume_data.get("missing_skills", [])[:8]:
        pdf.cell(0, 6, f"-  {s}", ln=True)
    pdf.ln(2)

    # Recommendations
    pdf.section_title("Recommendations")
    for i, rec in enumerate(resume_data.get("recommendations", [])[:6], 1):
        pdf.multi_cell(0, 6, f"{i}. {rec}")
        pdf.ln(1)

    return bytes(pdf.output())
