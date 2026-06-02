"""
Seeder Script — Populates mock performance data, dashboard history, and challenges.
Useful for demonstration, QA testing, and UI validation.
"""

import sys, os
from datetime import date, timedelta
import random

# Add parent path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.supabase_client import get_supabase_admin, db_insert, db_select
from src.auth.supabase_auth import get_supabase_client as get_auth_client

def seed_user_data(email: str):
    """Seed dashboard history, mock interviews, and challenges for a given user email."""
    client = get_supabase_admin()
    
    # 1. Fetch user by email from profiles
    res = client.table("profiles").select("*").eq("email", email).execute()
    if not res.data:
        print(f"[Error] User with email '{email}' not found. Please register the user in the app first.")
        return False
    
    user_profile = res.data[0]
    user_id = user_profile["id"]
    print(f"[Info] Found user profile: {user_profile['full_name']} ({user_id})")
    
    # 2. Seed performance history metrics (last 14 days)
    print("[Action] Seeding performance metrics...")
    today = date.today()
    for i in range(14, -1, -1):
        metric_date = str(today - timedelta(days=i))
        
        # Check if already exists
        exists = client.table("performance_metrics").select("id").eq("user_id", user_id).eq("metric_date", metric_date).execute()
        if exists.data:
            continue
            
        # Add random scores to show trendlines
        tech = round(random.uniform(65, 95), 1)
        hr = round(random.uniform(70, 95), 1)
        coding = round(random.uniform(50, 98), 1)
        comm = round(random.uniform(70, 90), 1)
        conf = round(random.uniform(75, 95), 1)
        overall = round((tech + hr + coding + comm + conf) / 5, 1)
        
        client.table("performance_metrics").insert({
            "user_id": user_id,
            "metric_date": metric_date,
            "technical_score": tech,
            "hr_score": hr,
            "coding_score": coding,
            "communication_score": comm,
            "confidence_score": conf,
            "overall_score": overall,
            "interviews_completed": random.randint(1, 3),
            "problems_solved": random.randint(1, 5),
            "study_minutes": random.randint(20, 120),
            "weak_areas": ["Dynamic Programming", "STAR Structure", "Speaking Speed"] if i % 3 == 0 else ["Pointers", "System Design"],
            "strong_areas": ["SQL Queries", "OOP Concepts", "Clarity"]
        }).execute()
        
    # 3. Seed mock interviews
    print("[Action] Seeding mock interview records...")
    interviews = [
        ("technical", "Software Engineer", "Google", "medium"),
        ("hr", "Technical Program Manager", "Amazon", "easy"),
        ("coding", "Backend Developer", "Meta", "hard"),
        ("mock", "Full Stack Developer", "Netflix", "medium"),
    ]
    for itype, domain, company, diff in interviews:
        # Create completed interviews
        res_int = client.table("interviews").insert({
            "user_id": user_id,
            "interview_type": itype,
            "domain": domain,
            "company": company,
            "difficulty": diff,
            "status": "completed",
            "overall_score": round(random.uniform(75, 95), 1),
            "technical_score": round(random.uniform(70, 95), 1),
            "communication_score": round(random.uniform(75, 95), 1),
            "confidence_score": round(random.uniform(80, 95), 1),
            "duration_minutes": random.randint(15, 45),
            "total_questions": 5,
            "answered_questions": 5,
            "feedback": f"Demonstrated solid core understanding of {domain} concepts. Communication was clear.",
        }).execute()
        
    # 4. Seed user achievements
    print("[Action] Seeding achievements completed...")
    achievements_res = client.table("achievements").select("*").execute()
    if achievements_res.data:
        # Award top 3 achievements
        for ach in achievements_res.data[:3]:
            try:
                client.table("user_achievements").insert({
                    "user_id": user_id,
                    "achievement_id": ach["id"]
                }).execute()
            except Exception:
                pass # Avoid duplicate issues
                
    # 5. Set user streak & XP in profile
    print("[Action] Updating user profile stats...")
    client.table("profiles").update({
        "xp_points": 1250,
        "streak_days": 5,
        "last_active": str(today)
    }).eq("id", user_id).execute()
    
    print("[Success] Database seeding completed successfully!")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed Supabase DB for development and testing.")
    parser.add_argument("--email", type=str, required=True, help="User email address registered in the app")
    args = parser.parse_args()
    seed_user_data(args.email)
