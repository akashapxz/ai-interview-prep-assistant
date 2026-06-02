"""
Create and Seed Test User
Creates a fully confirmed test user directly in Supabase (bypassing email validation)
and seeds their dashboard history and performance stats.
"""

import sys
import os

# Add parent path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.supabase_client import get_supabase_admin
from src.database.seed_db import seed_user_data

def create_and_seed_user():
    email = "testuser@example.com"
    password = "Password123!"
    full_name = "John Doe"
    college = "Tech Institute"
    branch = "Computer Science"
    
    try:
        print("[Connecting] Connecting to Supabase with Admin credentials...")
        admin_client = get_supabase_admin()
        
        # Check if user already exists
        print(f"[Check] Checking if user '{email}' already exists...")
        res = admin_client.table("profiles").select("id").eq("email", email).execute()
        
        if res.data:
            print(f"[Info] User '{email}' already exists in profiles.")
        else:
            print(f"[Action] Creating fully confirmed user '{email}' via Admin auth API...")
            user_res = admin_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name,
                    "college": college,
                    "branch": branch
                }
            })
            
            # The database trigger on auth.users will create the profile automatically.
            # Double check/ensure profile row is populated
            print(f"[Success] User created successfully (ID: {user_res.user.id})")
            
        # Seed performance history metrics, mock interviews, and badges
        print(f"[Action] Seeding dashboard data for '{email}'...")
        success = seed_user_data(email)
        if success:
            print(f"\n[Done] Test user ready!")
            print(f"       Email: {email}")
            print(f"       Password: {password}")
            print(f"       App URL: http://localhost:8501")
        else:
            print("[Error] Failed to seed user data.")
            
    except Exception as e:
        print(f"[Error] Exception occurred: {e}")

if __name__ == "__main__":
    create_and_seed_user()
