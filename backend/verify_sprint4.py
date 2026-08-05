"""
Sprint 4 - Step 3: End-to-end verification script
"""
import sqlite3
import json
import requests
import jwt
from datetime import datetime, timedelta, timezone

DB_PATH = r"c:\AI quiz generator\AI-quiz-generator\backend\quiz_generator.db"
SECRET_KEY = "ai-quiz-generator-secret-key-2024"
ALGORITHM = "HS256"

# 1. Fetch user 1
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, email FROM users WHERE id=1")
user = cur.fetchone()
conn.close()

user_id = user["id"]

# 2. Generate valid JWT token directly
now = datetime.now(timezone.utc)
payload = {
    "sub": str(user_id),
    "exp": now + timedelta(minutes=60)
}
token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
headers = {"Authorization": f"Bearer {token}"}

print(f"User: {user['email']} (ID={user_id})")
print(f"Token: {token[:25]}...")

# 3. Call AI endpoint for topic quiz (MCQ + True/False)
print("\nRequesting AI Quiz: Topic='Photosynthesis', types=['mcq', 'true_false'], num=4...")
url = "http://localhost:8000/api/quizzes/generate-from-topic"
req_body = {
    "topic": "Photosynthesis",
    "num_questions": 4,
    "difficulty": "easy",
    "question_types": ["mcq", "true_false"]
}

res = requests.post(url, json=req_body, headers=headers)
print(f"API Response Status: {res.status_code}")

if res.status_code not in (200, 201):
    print("API Error:", res.text)
    exit(1)

data = res.json()
quiz_id = data["id"]
print(f"Quiz Created: ID={quiz_id}, Title='{data['title']}'")

# 4. Verify SQLite DB rows
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id, type, payload, answer_key, question_text FROM questions WHERE quiz_id=? ORDER BY order_index", (quiz_id,))
rows = cur.fetchall()
conn.close()

print(f"\nVerifying {len(rows)} questions in Database:")
type_counts = {}
all_ok = True

for r in rows:
    t = r["type"]
    type_counts[t] = type_counts.get(t, 0) + 1
    p = json.loads(r["payload"]) if r["payload"] else {}
    ak = json.loads(r["answer_key"]) if r["answer_key"] else {}

    if t == "mcq":
        ok = "options" in p and "correct_index" in ak
    elif t == "true_false":
        ok = "correct" in ak
    else:
        ok = False

    if not ok:
        all_ok = False

    status = "PASS" if ok else "FAIL"
    print(f"  [Q#{r['id']}] Type: {t:12s} | Schema: {status} | Text: {r['question_text'][:55]}...")

print("\nQuestion Distribution:", type_counts)
if all_ok and len(rows) > 0:
    print("\nRESULT: PASS -- Sprint 4 multi-format AI generation fully verified end-to-end!")
else:
    print("\nRESULT: FAIL -- Check errors above")
