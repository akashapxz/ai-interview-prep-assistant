"""
Live end-to-end test — calls the real Gemini API with gemini-2.5-flash
and prints the raw result. Run this from the project root.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.ai.gemini_client import generate_text, generate_json

print("=== Test 1: generate_text ===")
try:
    r = generate_text("Say 'Hello from Gemini!' and nothing else.", temperature=0.1)
    print(f"PASS: {r}")
except Exception as e:
    print(f"FAIL: {e}")

print("\n=== Test 2: generate_json (technical question) ===")
try:
    r = generate_json(
        'Generate 1 easy Python question. Return JSON: {"questions": [{"question": "...", "hints": []}]}',
        temperature=0.5
    )
    if r and r.get("questions"):
        print(f"PASS: {r['questions'][0]['question'][:100]}")
    else:
        print(f"FAIL: returned None or empty — {r}")
except Exception as e:
    print(f"FAIL: {e}")
