"""
Sprint 5 - Direct code verification (no HTTP server needed).
Tests ai_service and grading_service directly with the actual code.
"""
import sys, sqlite3, json
sys.path.insert(0, r"c:\AI quiz generator\AI-quiz-generator\backend")

# Load .env
from dotenv import load_dotenv
load_dotenv(r"c:\AI quiz generator\AI-quiz-generator\backend\.env")

from app.services.ai_service import generate_questions_from_topic, grade_short_answer_with_ai

# ── PART 1: Generate short_answer questions and check types ──────────────────
print("=== PART 1: Generate short_answer quiz ===")
questions = generate_questions_from_topic(
    topic="Photosynthesis",
    num_questions=2,
    difficulty="easy",
    question_types=["short_answer"],
)

print(f"Questions generated: {len(questions)}")
all_correct_type = True
for i, q in enumerate(questions):
    t = q.get("type", "MISSING")
    ak = q.get("answer_key", {})
    has_ref = "reference_answer" in ak
    ok = t == "short_answer" and has_ref
    if not ok:
        all_correct_type = False
    print(f"  Q{i+1}: type={t} | has_reference_answer={has_ref} -> {'PASS' if ok else 'FAIL'}")
    print(f"        text: {q.get('question','')[:70]}...")
    if has_ref:
        print(f"        ref:  {ak['reference_answer'][:70]}...")

# ── PART 2: AI Grader correctness ────────────────────────────────────────────
print("\n=== PART 2: AI Grader ===")
good = grade_short_answer_with_ai(
    question_text    = "What is photosynthesis?",
    reference_answer = "Photosynthesis is the process by which plants convert light energy into chemical energy stored as glucose.",
    user_answer      = "Photosynthesis is when plants use sunlight, water and CO2 to produce glucose and oxygen.",
    points=2,
)
weak = grade_short_answer_with_ai(
    question_text    = "What is photosynthesis?",
    reference_answer = "Photosynthesis is the process by which plants convert light energy into chemical energy stored as glucose.",
    user_answer      = "Plants do something with sunlight",
    points=2,
)
grader_ok = good["score"] > weak["score"] and good["correct"] and not weak["correct"]
print(f"  Good answer: score={good['score']:.2f} correct={good['correct']} pts={good['points_earned']} -> {'PASS' if good['correct'] else 'FAIL'}")
print(f"    Feedback: {good['ai_feedback']}")
print(f"  Weak answer: score={weak['score']:.2f} correct={weak['correct']} pts={weak['points_earned']} -> {'PASS' if not weak['correct'] else 'FAIL'}")
print(f"    Feedback: {weak['ai_feedback']}")
print(f"  Grader ranks correctly: {grader_ok}")

# ── PART 3: Router save logic check (verify imports work) ────────────────────
print("\n=== PART 3: Router save logic imports ===")
from app.routers.quiz import router
from app.models.question import Question
import inspect

# Check the source code has the fix
import app.routers.quiz as quiz_mod
src = inspect.getsource(quiz_mod)
has_fix = 'type=q.get("type", "mcq")' in src
print(f"  Router uses q.get('type') instead of hardcoded: {'PASS' if has_fix else 'FAIL'}")

# ── FINAL ────────────────────────────────────────────────────────────────────
print("\n=== FINAL RESULT ===")
if all_correct_type and grader_ok and has_fix:
    print("PASS -- Sprint 5 fully verified!")
    print("  - Gemini generates correct short_answer type with reference_answers")
    print("  - AI grader scores good > weak answer correctly")
    print("  - Router save logic uses dynamic type from ai_questions")
else:
    if not all_correct_type:
        print("FAIL: Gemini not returning short_answer type")
    if not grader_ok:
        print("FAIL: AI grader ranking incorrect")
    if not has_fix:
        print("FAIL: Router still has hardcoded type='mcq'")
