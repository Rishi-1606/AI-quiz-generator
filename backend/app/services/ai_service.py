"""
AI Service — Gemini Quiz Generator
------------------------------------
Sends cleaned text chunks to Google Gemini and returns
structured multiple-choice quiz questions.

Usage:
    from app.services.ai_service import generate_questions_from_chunk

    questions = generate_questions_from_chunk(
        text="...cleaned study content...",
        num_questions=5,
        difficulty="medium"
    )
"""

import json
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

# The Gemini model we'll use (free tier: 15 RPM)
MODEL_NAME = "gemini-3.1-flash-lite"


# ─────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────

def _build_prompt(text: str, num_questions: int, difficulty: str) -> str:
    """
    Build the prompt that instructs Gemini to generate quiz questions.
    Strictly enforces JSON output so it can be parsed reliably.
    """
    return f"""You are an expert quiz creator for college-level students.

Given the following study material, generate exactly {num_questions} multiple-choice questions.

Difficulty level: {difficulty.upper()}
- easy   : factual recall, straightforward definitions
- medium : conceptual understanding, application
- hard   : analysis, evaluation, edge cases

STRICT RULES:
1. Each question must have exactly 4 options (A, B, C, D).
2. Only ONE option is correct.
3. The "correct_option" field must be the index (0 for A, 1 for B, 2 for C, 3 for D).
4. "explanation" must be 1-2 sentences explaining WHY the correct answer is right.
5. Questions must be based ONLY on the provided material. Do NOT add outside knowledge.
6. Output ONLY valid JSON — no markdown, no extra text, no code fences.

OUTPUT FORMAT (return this exact structure):
[
  {{
    "question": "...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_option": 0,
    "explanation": "..."
  }}
]

STUDY MATERIAL:
\"\"\"
{text}
\"\"\"

Generate {num_questions} questions now:"""


# ─────────────────────────────────────────────────────────
# CORE FUNCTION
# ─────────────────────────────────────────────────────────

def generate_questions_from_chunk(
    text: str,
    num_questions: int = 5,
    difficulty: str = "medium",
) -> list[dict]:
    """
    Send a text chunk to Gemini and return a list of parsed question dicts.

    Each returned dict has:
      - question        (str)
      - options         (list of 4 str)
      - correct_option  (int, 0-3)
      - explanation     (str)

    Raises:
      ValueError  if Gemini returns unparseable JSON.
      Exception   for API errors (rate limit, invalid key, etc.)
    """
    if not text or not text.strip():
        return []

    # Clamp num_questions to a safe range (1–15)
    num_questions = max(1, min(num_questions, 15))

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = _build_prompt(text, num_questions, difficulty)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,       # Lower = more factual, less creative
            top_p=0.9,
            max_output_tokens=4096,
        ),
    )

    raw = response.text.strip()

    # Strip markdown code fences if Gemini adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if raw.endswith("```"):
        raw = raw[: raw.rfind("```")].strip()

    try:
        questions = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON: {e}\nRaw response:\n{raw[:500]}"
        )

    # Validate each question has required fields
    validated = []
    for q in questions:
        if all(k in q for k in ("question", "options", "correct_option", "explanation")):
            if isinstance(q["options"], list) and len(q["options"]) == 4:
                validated.append(q)

    return validated


# ─────────────────────────────────────────────────────────
# FEEDBACK GENERATOR
# ─────────────────────────────────────────────────────────

def generate_feedback(
    wrong_questions: list[dict],
    correct_count: int,
    total: int,
    difficulty: str,
) -> str:
    """
    Given a list of questions the user got wrong, ask Gemini to produce
    a short, personalized study recommendation.

    Each item in wrong_questions should have:
      - question_text (str)
      - correct_option (int)
      - options        (list[str])
      - explanation    (str)

    Returns a plain-text string (2–4 sentences).
    Returns empty string on any failure (feedback is optional, not critical).
    """
    if not wrong_questions:
        # Perfect score — return a congratulatory message
        return (
            f"Excellent work! You answered all {total} questions correctly on the "
            f"{difficulty} difficulty quiz. You have a strong grasp of this material. "
            "Consider trying the hard difficulty next!"
        )

    # Build a compact summary of mistakes for the prompt
    mistake_lines = []
    for i, q in enumerate(wrong_questions[:5], 1):   # cap at 5 to save tokens
        correct_text = q["options"][q["correct_option"]] if q["options"] else "—"
        mistake_lines.append(
            f"{i}. Q: {q['question_text']}\n"
            f"   Correct answer: {correct_text}\n"
            f"   Hint: {q.get('explanation', '')}"
        )
    mistakes_block = "\n".join(mistake_lines)

    prompt = f"""A student just completed a {difficulty.upper()} difficulty quiz and scored {correct_count}/{total}.

They got the following questions wrong:
{mistakes_block}

Write a SHORT (2-4 sentences) personalized study recommendation for this student.
- Identify the specific concepts or topics they struggled with.
- Give ONE concrete action they can take to improve (e.g. "review chapter on X", "practice Y type of problems").
- Be encouraging but honest.
- Write in second person ("You...").
- Do NOT repeat the questions or answers back.
- Output plain text only, no markdown, no bullet points."""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=256,
            ),
        )
        return response.text.strip()
    except Exception:
        return ""   # Feedback is optional — swallow errors silently
