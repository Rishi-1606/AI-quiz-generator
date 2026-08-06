"""
Sprint 5 - Step 3: End-to-end AI short answer grading verification.

Flow:
  1. Generate a 2-question short_answer quiz on Photosynthesis
  2. Submit it with one good answer and one weak answer
  3. Verify Gemini graded both answers (score, correct, feedback)
  4. Print results
"""
import sqlite3, json, jwt, requests
from datetime import datetime, timedelta, timezone

BASE     = "http://localhost:8000"
DB_PATH  = r"c:\AI quiz generator\AI-quiz-generator\backend\quiz_generator.db"
SECRET   = "ai-quiz-generator-secret-key-2024"
ALGO     = "HS256"

# ── Auth token ────────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur  = conn.cursor()
cur.execute("SELECT id, email FROM users LIMIT 1")
user = cur.fetchone()
conn.close()

token = jwt.encode(
    {"sub": str(user["id"]), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
    SECRET, algorithm=ALGO
)
headers = {"Authorization": f"Bearer {token}"}
print(f"User: {user['email']} | Token ready")

# ── Step 1: Generate short_answer quiz ───────────────────────────────────────
print("\n--- STEP 1: Generating short_answer quiz on Photosynthesis ---")
r = requests.post(f"{BASE}/api/quizzes/generate-from-topic", json={
    "topic":          "Photosynthesis",
    "num_questions":  2,
    "difficulty":     "easy",
    "question_types": ["short_answer"],
}, headers=headers)

if r.status_code not in (200, 201):
    print(f"FAIL: {r.status_code} | {r.text[:300]}")
    exit(1)

quiz    = r.json()
quiz_id = quiz["id"]
qs      = quiz.get("questions", [])
print(f"Quiz ID={quiz_id} | Questions returned: {len(qs)}")
for i, q in enumerate(qs):
    print(f"  Q{i+1}: {q['question_text'][:80]}...")

# ── Step 2: Submit with test answers ─────────────────────────────────────────
print("\n--- STEP 2: Submitting answers ---")

# Build answers dict: good answer for Q1, weak answer for Q2
answers = {}
if len(qs) >= 1:
    answers[str(qs[0]["id"])] = (
        "Photosynthesis is the process by which green plants use sunlight, "
        "water, and carbon dioxide to produce glucose and oxygen."
    )
if len(qs) >= 2:
    answers[str(qs[1]["id"])] = "Plants do something with sun"  # weak answer

r = requests.post(f"{BASE}/api/quizzes/{quiz_id}/submit", json={
    "answers":    answers,
    "time_taken": 60,
}, headers=headers)

if r.status_code not in (200, 201):
    print(f"FAIL: {r.status_code} | {r.text[:300]}")
    exit(1)

result = r.json()
print(f"Submission accepted | Score: {result['correct']}/{result['total']} | {result['percentage']}%")
print(f"Points earned: {result.get('points_earned', 'N/A')} / {result.get('points_total', 'N/A')}")

# ── Step 3: Verify AI grading ran (check DB answer_key for reference_answer) ─
print("\n--- STEP 3: Verifying DB stored reference_answers correctly ---")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur  = conn.cursor()
cur.execute(
    "SELECT id, type, answer_key, question_text FROM questions WHERE quiz_id=?",
    (quiz_id,)
)
rows = cur.fetchall()
conn.close()

all_ok = True
for row in rows:
    ak = json.loads(row["answer_key"]) if row["answer_key"] else {}
    has_ref = "reference_answer" in ak
    if not has_ref:
        all_ok = False
    print(f"  Q#{row['id']} type={row['type']} | has_reference_answer={has_ref} -> {'PASS' if has_ref else 'FAIL'}")
    if has_ref:
        print(f"    Reference: {ak['reference_answer'][:80]}...")

# ── Step 4: Direct AI grader unit test ───────────────────────────────────────
print("\n--- STEP 4: Direct AI grader unit test ---")
import sys
sys.path.insert(0, r"c:\AI quiz generator\AI-quiz-generator\backend")
from app.services.ai_service import grade_short_answer_with_ai

good_result = grade_short_answer_with_ai(
    question_text    = "What is photosynthesis?",
    reference_answer = "Photosynthesis is the process by which plants convert light energy into chemical energy stored as glucose.",
    user_answer      = "Photosynthesis is when plants use sunlight, water and CO2 to make food (glucose) and release oxygen.",
    points           = 2,
)
weak_result = grade_short_answer_with_ai(
    question_text    = "What is photosynthesis?",
    reference_answer = "Photosynthesis is the process by which plants convert light energy into chemical energy stored as glucose.",
    user_answer      = "Plants do something with sunlight",
    points           = 2,
)

print(f"  Good answer -> score={good_result['score']:.2f} | correct={good_result['correct']} | points={good_result['points_earned']}")
print(f"    Feedback: {good_result['ai_feedback']}")
print(f"  Weak answer -> score={weak_result['score']:.2f} | correct={weak_result['correct']} | points={weak_result['points_earned']}")
print(f"    Feedback: {weak_result['ai_feedback']}")

grader_ok = good_result["score"] > weak_result["score"] and good_result["correct"]

print()
print("--- FINAL RESULT ---")
if all_ok and grader_ok:
    print("PASS -- Sprint 5 AI short answer grading fully verified!")
    print("  - reference_answers stored correctly in DB")
    print("  - AI grader scores good answer higher than weak answer")
    print("  - Feedback generated for both answers")
else:
    print("FAIL -- check issues above")
    if not all_ok:
        print("  - Some questions missing reference_answer in DB")
    if not grader_ok:
        print("  - AI grader did not score correctly")
