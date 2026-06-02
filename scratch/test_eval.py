"""
Scratch script to test evaluate_technical_answer live.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.ai.gemini_client import evaluate_technical_answer

q = "What is the difference between SQL and NoSQL databases?"
ans = "SQL databases are relational and table-based, while NoSQL databases are non-relational and document/key-value based. SQL uses strict schemas, NoSQL is dynamic."
domain = "DBMS"
difficulty = "medium"

print("Evaluating...")
res = evaluate_technical_answer(q, ans, domain, difficulty)
print("Result:")
print(res)
