"""
Helper utilities — formatting, scoring, XP, date helpers, etc.
"""

import re
import uuid
import hashlib
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any


def generate_session_id() -> str:
    return str(uuid.uuid4())


def score_to_grade(score: float) -> str:
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "F"


def score_to_color(score: float) -> str:
    if score >= 80: return "#22c55e"   # green
    if score >= 60: return "#f59e0b"   # amber
    if score >= 40: return "#f97316"   # orange
    return "#ef4444"                   # red


def score_to_emoji(score: float) -> str:
    if score >= 90: return "emoji_events"
    if score >= 75: return "grade"
    if score >= 60: return "thumb_up"
    if score >= 40: return "trending_up"
    return "fitness_center"


def calculate_xp_for_interview(score: float, interview_type: str) -> int:
    base = int(score * 1.5)
    bonus = {"mock": 50, "voice": 40, "coding": 30, "technical": 25, "hr": 20}.get(interview_type, 10)
    return base + bonus


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def time_ago(dt: datetime) -> str:
    now = datetime.utcnow()
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return "some time ago"
    diff = now - dt
    if diff.days > 365: return f"{diff.days // 365}y ago"
    if diff.days > 30: return f"{diff.days // 30}mo ago"
    if diff.days > 0: return f"{diff.days}d ago"
    hours = diff.seconds // 3600
    if hours > 0: return f"{hours}h ago"
    mins = diff.seconds // 60
    if mins > 0: return f"{mins}m ago"
    return "just now"


def clean_json_text(raw: str) -> str:
    """Strip markdown code fences from LLM JSON output."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        raw = "\n".join(lines[start:end])
    return raw.strip()


def truncate_text(text: str, max_chars: int = 500) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def sanitize_input(text: str) -> str:
    """Basic XSS/injection prevention for user input."""
    text = re.sub(r"<[^>]+>", "", text)           # strip HTML tags
    text = re.sub(r"[;\-\-]", " ", text)          # strip SQL injection patterns
    return text.strip()[:5000]                     # limit length


def week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def get_date_range(days: int) -> List[str]:
    today = date.today()
    return [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]


def calculate_streak(activity_dates: List[str]) -> int:
    """Calculate current streak from a list of ISO date strings."""
    if not activity_dates:
        return 0
    dates = sorted(set(activity_dates), reverse=True)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if dates[0] not in (today, yesterday):
        return 0
    streak = 1
    for i in range(1, len(dates)):
        d1 = date.fromisoformat(dates[i - 1])
        d2 = date.fromisoformat(dates[i])
        if (d1 - d2).days == 1:
            streak += 1
        else:
            break
    return streak


def readiness_label(score: int) -> str:
    if score >= 85: return "Interview Ready"
    if score >= 70: return "Almost Ready"
    if score >= 50: return "Needs Practice"
    return "Needs Intensive Prep"


SKILL_DOMAINS = [
    "DSA", "DBMS", "OOP", "Operating Systems", "Computer Networks",
    "Machine Learning", "Artificial Intelligence", "Data Science",
    "Web Development", "Cloud Computing", "Cybersecurity", "DevOps",
    "System Design",
]

COMPANIES = [
    "Google", "Amazon", "Microsoft", "Meta", "Apple",
    "Netflix", "Infosys", "TCS", "Wipro", "Accenture",
    "Flipkart", "Paytm", "Razorpay", "Zomato", "Swiggy",
]

CODING_TOPICS = [
    "Arrays", "Strings", "Linked Lists", "Stacks & Queues",
    "Trees", "Graphs", "Dynamic Programming", "Recursion",
    "Backtracking", "Searching", "Sorting", "Hashing",
    "Bit Manipulation", "Greedy Algorithms", "Math",
]
