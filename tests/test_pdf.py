"""
Unit Tests for PDF Report Generators
"""

import pytest
from src.utils.report_generator import generate_resume_report, generate_interview_report

def test_resume_pdf_report():
    mock_data = {
        "ats_score": 85,
        "readiness_score": 90,
        "summary": "Experienced software architect",
        "skills": ["Python", "Docker", "PostgreSQL"],
        "strengths": ["Architecture", "System Design"],
        "weaknesses": ["Frontend CSS"],
        "recommendations": ["Learn React"]
    }
    pdf_bytes = generate_resume_report(mock_data, "John Doe")
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
