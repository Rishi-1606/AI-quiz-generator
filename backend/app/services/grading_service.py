"""
Grading Service — Sprint 2

Dispatches question grading by `type` so the submit endpoint
doesn't hardcode MCQ logic.

Each grader receives:
  - question : Question ORM object (has .type, .answer_key, .correct_option, .points)
  - user_answer : whatever the frontend sent for this question (int, str, list, etc.)

Each grader returns:
  GradeResult(correct=bool, points_earned=int)

New question types added in future sprints only need a new
`_grade_<type>()` function added here — no other files change.
"""

from dataclasses import dataclass
from typing import Any, Optional
import json


@dataclass
class GradeResult:
    correct:       bool
    points_earned: int


# ─── Type dispatchers ─────────────────────────────────────────────────────────

def grade_question(question, user_answer: Any) -> GradeResult:
    """
    Main entry point. Dispatch to the correct grader by question.type.
    Falls back to MCQ logic for rows that pre-date Sprint 1 (no type column).
    """
    q_type = getattr(question, "type", "mcq") or "mcq"

    graders = {
        "mcq":          _grade_mcq,
        "true_false":   _grade_true_false,
        "fill_blank":   _grade_fill_blank,
        "short_answer": _grade_short_answer,
        "matching":     _grade_matching,
        "ordering":     _grade_ordering,
        "numeric":      _grade_numeric,
    }

    grader = graders.get(q_type, _grade_mcq)
    return grader(question, user_answer)


# ─── MCQ ──────────────────────────────────────────────────────────────────────

def _grade_mcq(question, user_answer: Optional[int]) -> GradeResult:
    """
    user_answer: 0-indexed int matching chosen option.
    Correct index comes from answer_key["correct_index"] (new)
    with fallback to correct_option (legacy).
    """
    if user_answer is None:
        return GradeResult(correct=False, points_earned=0)

    # Prefer new answer_key column; fall back to legacy correct_option
    answer_key = _parse_json(question.answer_key)
    if answer_key and "correct_index" in answer_key:
        correct_index = answer_key["correct_index"]
    else:
        correct_index = question.correct_option  # legacy fallback

    correct = (user_answer == correct_index)
    return GradeResult(correct=correct, points_earned=question.points if correct else 0)


# ─── True / False ─────────────────────────────────────────────────────────────

def _grade_true_false(question, user_answer: Optional[bool]) -> GradeResult:
    """
    user_answer: True or False (sent as JSON bool from frontend).
    answer_key: {"correct": true|false}
    """
    if user_answer is None:
        return GradeResult(correct=False, points_earned=0)

    answer_key = _parse_json(question.answer_key)
    correct_val = answer_key.get("correct") if answer_key else None

    if correct_val is None:
        return GradeResult(correct=False, points_earned=0)

    correct = (user_answer == correct_val)
    return GradeResult(correct=correct, points_earned=question.points if correct else 0)


# ─── Fill in the Blank ────────────────────────────────────────────────────────

def _grade_fill_blank(question, user_answer: Optional[str]) -> GradeResult:
    """
    user_answer: string typed by user.
    answer_key: {"accepted_answers": ["str", ...]}
    Matching is case-insensitive and strips whitespace.
    AI-assisted fuzzy grading added in Sprint 5.
    """
    if not user_answer or not isinstance(user_answer, str):
        return GradeResult(correct=False, points_earned=0)

    answer_key = _parse_json(question.answer_key)
    accepted = answer_key.get("accepted_answers", []) if answer_key else []

    normalised_input = user_answer.strip().lower()
    correct = any(normalised_input == a.strip().lower() for a in accepted)
    return GradeResult(correct=correct, points_earned=question.points if correct else 0)


# ─── Short Answer (AI-graded — Sprint 5) ─────────────────────────────────────

def _grade_short_answer(question, user_answer: Optional[str]) -> GradeResult:
    """
    Placeholder — AI grading wired up in Sprint 5.
    For now: always returns correct=False, points_earned=0 so it doesn't crash.
    """
    # TODO Sprint 5: call ai_service.grade_open_response()
    return GradeResult(correct=False, points_earned=0)


# ─── Matching ─────────────────────────────────────────────────────────────────

def _grade_matching(question, user_answer: Optional[list]) -> GradeResult:
    """
    user_answer: list of [left_idx, right_idx] pairs chosen by user.
    answer_key:  {"pairs": [[int, int], ...]}
    All pairs must be correct for full points.
    """
    if not user_answer or not isinstance(user_answer, list):
        return GradeResult(correct=False, points_earned=0)

    answer_key = _parse_json(question.answer_key)
    correct_pairs = answer_key.get("pairs", []) if answer_key else []

    # Compare as sets of tuples (order of pairs doesn't matter)
    user_set    = {tuple(p) for p in user_answer}
    correct_set = {tuple(p) for p in correct_pairs}

    correct = (user_set == correct_set)
    return GradeResult(correct=correct, points_earned=question.points if correct else 0)


# ─── Ordering ─────────────────────────────────────────────────────────────────

def _grade_ordering(question, user_answer: Optional[list]) -> GradeResult:
    """
    user_answer: list of int indices in the order the user arranged them.
    answer_key:  {"correct_order": [int, ...]}
    Entire sequence must match exactly.
    """
    if not user_answer or not isinstance(user_answer, list):
        return GradeResult(correct=False, points_earned=0)

    answer_key = _parse_json(question.answer_key)
    correct_order = answer_key.get("correct_order", []) if answer_key else []

    correct = (list(user_answer) == list(correct_order))
    return GradeResult(correct=correct, points_earned=question.points if correct else 0)


# ─── Numeric ──────────────────────────────────────────────────────────────────

def _grade_numeric(question, user_answer) -> GradeResult:
    """
    user_answer: numeric value (int or float) from frontend input.
    answer_key:  {"value": float, "tolerance": float|null}
    tolerance: acceptable ± margin (absolute, not percentage).
    """
    if user_answer is None:
        return GradeResult(correct=False, points_earned=0)

    try:
        user_val = float(user_answer)
    except (ValueError, TypeError):
        return GradeResult(correct=False, points_earned=0)

    answer_key  = _parse_json(question.answer_key)
    correct_val = float(answer_key.get("value", 0)) if answer_key else 0.0
    tolerance   = float(answer_key.get("tolerance") or 0) if answer_key else 0.0

    correct = abs(user_val - correct_val) <= tolerance
    return GradeResult(correct=correct, points_earned=question.points if correct else 0)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json(value) -> Optional[dict]:
    """Safely parse a JSON string or return the dict as-is."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None
