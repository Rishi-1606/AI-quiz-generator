"""
AI Service — Gemini Quiz Generator
------------------------------------
Sends cleaned text chunks to Google Gemini and returns
structured quiz questions in multiple formats.

Supported question types (Sprint 4):
  "mcq"          — Multiple choice (4 options)
  "true_false"   — True or False
  "fill_blank"   — Fill in the blank
  "short_answer" — Open-ended text (AI-graded in Sprint 5)

Usage:
    from app.services.ai_service import generate_questions_from_chunk

    questions = generate_questions_from_chunk(
        text="...cleaned study content...",
        num_questions=5,
        difficulty="medium",
        question_types=["mcq", "true_false"]
    )
"""

import json
import random
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

# The Gemini model we'll use (free tier: 15 RPM)
MODEL_NAME = "gemini-3.1-flash-lite"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _strip_fences(raw: str) -> str:
    """Remove markdown code fences that Gemini adds despite instructions."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if raw.endswith("```"):
        raw = raw[:raw.rfind("```")].strip()
    return raw


def _parse_json(raw: str) -> list:
    """Parse JSON from Gemini response, raising ValueError on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw:\n{raw[:500]}")


# ─── Per-type prompt fragments ────────────────────────────────────────────────

# Each fragment tells Gemini the exact JSON shape for that type.
TYPE_PROMPTS = {
    "mcq": """
TYPE: mcq
JSON shape:
{
  "type": "mcq",
  "question": "Question text here?",
  "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
  "correct_option": 1,
  "explanation": "Why the correct answer is right."
}
Rules: exactly 4 options. correct_option is 0-indexed (0=A, 1=B, 2=C, 3=D).
""",

    "true_false": """
TYPE: true_false
JSON shape:
{
  "type": "true_false",
  "question": "A clear statement that is either true or false.",
  "correct_answer": true,
  "explanation": "Why this statement is true/false."
}
Rules: correct_answer must be a JSON boolean (true or false, not a string).
""",

    "fill_blank": """
TYPE: fill_blank
JSON shape:
{
  "type": "fill_blank",
  "question": "Sentence with ___ where the blank appears.",
  "text_with_blanks": "The ___ is the powerhouse of the cell.",
  "accepted_answers": ["mitochondria", "mitochondrion"],
  "explanation": "Brief explanation of the answer."
}
Rules: use exactly ___ (three underscores) to mark blanks. accepted_answers lists all valid spellings.
""",

    "short_answer": """
TYPE: short_answer
JSON shape:
{
  "type": "short_answer",
  "question": "Open-ended question requiring a 1-2 sentence answer.",
  "reference_answer": "Model answer for grading.",
  "explanation": "Key points the answer should cover."
}
Rules: question must be answerable in 1-3 sentences. reference_answer is used by AI grader.
""",
}


def _build_type_distribution(question_types: list[str], num_questions: int) -> list[str]:
    """
    Distribute num_questions evenly across requested types.
    e.g. types=["mcq","true_false"], num=5 -> ["mcq","mcq","mcq","true_false","true_false"]
    """
    if not question_types:
        question_types = ["mcq"]
    # Cycle through types to fill num_questions
    distribution = []
    for i in range(num_questions):
        distribution.append(question_types[i % len(question_types)])
    return distribution


# ─── Prompt builders ──────────────────────────────────────────────────────────

def _build_mixed_prompt(
    content_section: str,
    num_questions: int,
    difficulty: str,
    question_types: list[str],
) -> str:
    """
    Build a multi-format prompt supporting both document and topic content.
    content_section: pre-built string like 'STUDY MATERIAL: ...' or 'TOPIC: ...'
    """
    type_set = list(dict.fromkeys(question_types))  # deduplicate, preserve order
    type_fragments = "\n".join(TYPE_PROMPTS[t] for t in type_set if t in TYPE_PROMPTS)
    distribution = _build_type_distribution(question_types, num_questions)
    dist_summary = ", ".join(f"{distribution.count(t)}x {t}" for t in type_set)

    return f"""You are an expert quiz creator for students and learners.

Generate exactly {num_questions} quiz questions with this distribution: {dist_summary}.

Difficulty level: {difficulty.upper()}
- easy   : factual recall, basic definitions
- medium : conceptual understanding, application
- hard   : analysis, edge cases, deeper reasoning

QUESTION TYPE SPECS (use EXACTLY these JSON shapes):
{type_fragments}

STRICT RULES:
1. Output ONLY a valid JSON array — no markdown, no code fences, no extra text.
2. Each object in the array must have a "type" field matching the spec above.
3. Generate the distribution specified: {dist_summary}.
4. Every question must have an "explanation" field.
5. Questions must be based ONLY on the provided content.
6. Do NOT mix up the JSON shapes between types.

{content_section}

Return ONLY the JSON array with exactly {num_questions} questions now:"""


# ─── Validator ────────────────────────────────────────────────────────────────

def _validate_question(q: dict) -> dict | None:
    """
    Validate a question dict from Gemini and normalize it to
    the internal format used by the quiz router (always has
    'question', 'options', 'correct_option', 'explanation' + new fields).
    Returns None if invalid.
    """
    q_type = q.get("type", "mcq")

    if q_type == "mcq":
        if not all(k in q for k in ("question", "options", "correct_option", "explanation")):
            return None
        if not isinstance(q["options"], list) or len(q["options"]) != 4:
            return None
        return {
            "type":           "mcq",
            "question":       q["question"],
            "options":        q["options"],
            "correct_option": int(q["correct_option"]),
            "explanation":    q.get("explanation", ""),
            # New generalized fields
            "payload":    {"options": q["options"]},
            "answer_key": {"correct_index": int(q["correct_option"])},
        }

    elif q_type == "true_false":
        if not all(k in q for k in ("question", "correct_answer", "explanation")):
            return None
        correct = q["correct_answer"]
        if not isinstance(correct, bool):
            # Try to coerce string "true"/"false"
            if isinstance(correct, str):
                correct = correct.lower() == "true"
            else:
                return None
        return {
            "type":           "true_false",
            "question":       q["question"],
            "options":        ["True", "False"],          # for legacy compat display
            "correct_option": 0 if correct else 1,        # legacy compat
            "explanation":    q.get("explanation", ""),
            "payload":    {},
            "answer_key": {"correct": correct},
        }

    elif q_type == "fill_blank":
        if not all(k in q for k in ("question", "accepted_answers", "explanation")):
            return None
        answers = q["accepted_answers"]
        if isinstance(answers, str):
            answers = [answers]
        return {
            "type":           "fill_blank",
            "question":       q["question"],
            "options":        [],                          # no options for this type
            "correct_option": 0,                          # placeholder
            "explanation":    q.get("explanation", ""),
            "payload":    {"text_with_blanks": q.get("text_with_blanks", q["question"])},
            "answer_key": {"accepted_answers": answers},
        }

    elif q_type == "short_answer":
        if not all(k in q for k in ("question", "reference_answer", "explanation")):
            return None
        return {
            "type":           "short_answer",
            "question":       q["question"],
            "options":        [],
            "correct_option": 0,
            "explanation":    q.get("explanation", ""),
            "payload":    {},
            "answer_key": {"reference_answer": q["reference_answer"]},
        }

    return None  # unknown type


# ─────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────

def generate_questions_from_chunk(
    text: str,
    num_questions: int = 5,
    difficulty: str = "medium",
    question_types: list[str] | None = None,
) -> list[dict]:
    """
    Send a text chunk to Gemini and return a list of parsed question dicts.

    question_types: list of type strings, e.g. ["mcq", "true_false"].
                    Defaults to ["mcq"] for full backward compatibility.
    """
    if not text or not text.strip():
        return []
    if question_types is None:
        question_types = ["mcq"]

    num_questions = max(1, min(num_questions, 15))
    content_section = f'STUDY MATERIAL:\n"""\n{text[:4000]}\n"""'
    prompt = _build_mixed_prompt(content_section, num_questions, difficulty, question_types)

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            top_p=0.9,
            max_output_tokens=4096,
        ),
    )

    raw = _strip_fences(response.text)
    questions = _parse_json(raw)

    validated = []
    for q in questions:
        result = _validate_question(q)
        if result:
            validated.append(result)

    return validated


def generate_questions_from_topic(
    topic: str,
    num_questions: int = 5,
    difficulty: str = "medium",
    question_types: list[str] | None = None,
) -> list[dict]:
    """
    Generate quiz questions from a free-text topic using Gemini's knowledge.

    question_types: defaults to ["mcq"] for backward compatibility.
    """
    if not topic or not topic.strip():
        return []
    if question_types is None:
        question_types = ["mcq"]

    num_questions = max(1, min(num_questions, 15))
    content_section = f"TOPIC: {topic}\nUse accurate, widely-accepted knowledge for this topic."
    prompt = _build_mixed_prompt(content_section, num_questions, difficulty, question_types)

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.5,
            top_p=0.9,
            max_output_tokens=4096,
        ),
    )

    raw = _strip_fences(response.text)
    questions = _parse_json(raw)

    validated = []
    for q in questions:
        result = _validate_question(q)
        if result:
            validated.append(result)

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

    Returns a plain-text string (2-4 sentences).
    Returns empty string on any failure (feedback is optional, not critical).
    """
    if not wrong_questions:
        return (
            f"Excellent work! You answered all {total} questions correctly on the "
            f"{difficulty} difficulty quiz. You have a strong grasp of this material. "
            "Consider trying the hard difficulty next!"
        )

    mistake_lines = []
    for i, q in enumerate(wrong_questions[:5], 1):
        correct_text = q["options"][q["correct_option"]] if q.get("options") else "—"
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
        return ""


# ─────────────────────────────────────────────────────────
# FLASHCARD GENERATOR
# ─────────────────────────────────────────────────────────

def generate_flashcards(text: str, num_cards: int = 10) -> list[dict]:
    """
    Extract key concept flashcards from study material.
    Returns: [{ "front": "Term / Question", "back": "Definition / Answer" }]
    """
    if not text or not text.strip():
        return []

    num_cards = max(5, min(num_cards, 20))

    prompt = f"""You are an expert tutor creating study flashcards.

From the study material below, extract exactly {num_cards} important concepts as flashcards.

STRICT RULES:
1. "front" must be a short term, concept name, or question (max 15 words).
2. "back" must be a clear, concise definition or answer (max 40 words).
3. Cover the most important and distinct concepts from the material.
4. Output ONLY valid JSON — no markdown, no code fences, no extra text.

OUTPUT FORMAT:
[
  {{"front": "Term or question", "back": "Definition or answer"}},
  ...
]

STUDY MATERIAL:
\"\"\"
{text[:3000]}
\"\"\"

Generate {num_cards} flashcards now:"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )
        raw = _strip_fences(response.text)
        cards = json.loads(raw)
        return [c for c in cards if "front" in c and "back" in c]
    except Exception:
        return []
