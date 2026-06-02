import inspect
from supabase import create_client

url = "https://oxqfdzpaqvnehbkpyorg.supabase.co"
key = "dummy"
c = create_client(url, key)

print("--- auth._request source code ---")
try:
    print(inspect.getsource(c.auth._request))
except Exception as e:
    print(f"Error: {e}")
