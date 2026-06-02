"""
Create Storage Buckets
Programmatically creates the 'resumes' and 'documents' public storage buckets
in the Supabase project using the service role key.
"""

import sys
import os

# Add parent path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.supabase_client import get_supabase_admin

def create_buckets():
    try:
        print("[Connecting] Connecting to Supabase with Admin credentials...")
        admin_client = get_supabase_admin()
        
        buckets = ["resumes", "documents"]
        
        # Get list of existing buckets
        existing_buckets = []
        try:
            list_res = admin_client.storage.list_buckets()
            existing_buckets = [b.id for b in list_res]
            print(f"[Info] Existing buckets: {existing_buckets}")
        except Exception as e:
            print(f"[Warning] Could not retrieve existing buckets: {e}. Attempting creation anyway...")

        for bucket in buckets:
            if bucket in existing_buckets:
                print(f"[Success] Bucket '{bucket}' already exists.")
                continue
                
            print(f"[Action] Creating public bucket '{bucket}'...")
            try:
                # Create public bucket
                admin_client.storage.create_bucket(bucket, options={"public": True})
                print(f"[Success] Successfully created public bucket: '{bucket}'")
            except Exception as e:
                # Double check if it was already created or failed
                print(f"[Error] Failed to create bucket '{bucket}': {e}")
                
        print("\n[Done] Storage initialization completed.")
    except Exception as e:
        print(f"[Error] Exception occurred: {e}")

if __name__ == "__main__":
    create_buckets()
