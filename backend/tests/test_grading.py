"""
Sprint 7 - Step 2: Unit tests for grading_service.py

Tests grade_question() for all 7 question types:
  - at least one clearly-correct case per type
  - at least one clearly-wrong case per type
  - one edge case per type

Uses a minimal MockQuestion object so we never touch the DB.
The short_answer grader calls grade_short_answer_with_ai (Gemini),
so that one is mocked via pytest-mock.
"""

import pytest
from unittest.mock import patch

from app.services.grading_service import grade_question, GradeResult


# ---------------------------------------------------------------------------
# Minimal mock question — mirrors the ORM columns grading_service reads
# ---------------------------------------------------------------------------

class MockQuestion:
    def __init__(self, q_type, answer_key, correct_option=0, points=1, question_text="Sample question?"):
        self.type          = q_type
        self.answer_key    = answer_key   # pass as dict; _parse_json handles it
        self.correct_option = correct_option
        self.points        = points
        self.question_text = question_text


# ===========================================================================
# MCQ
# ===========================================================================

def test_mcq_correct():
    q = MockQuestion("mcq", {"correct_index": 2}, points=3)
    result = grade_question(q, user_answer=2)
    assert result.correct is True
    assert result.points_earned == 3

def test_mcq_wrong():
    q = MockQuestion("mcq", {"correct_index": 2}, points=3)
    result = grade_question(q, user_answer=0)
    assert result.correct is False
    assert result.points_earned == 0

def test_mcq_none_answer_skipped():
    """None answer must be treated as skipped — no points, not correct."""
    q = MockQuestion("mcq", {"correct_index": 1}, points=1)
    result = grade_question(q, user_answer=None)
    assert result.correct is False
    assert result.points_earned == 0

def test_mcq_legacy_fallback_no_answer_key():
    """When answer_key has no correct_index, fall back to correct_option."""
    q = MockQuestion("mcq", {}, correct_option=1, points=1)
    result = grade_question(q, user_answer=1)
    assert result.correct is True

def test_mcq_legacy_fallback_wrong():
    q = MockQuestion("mcq", {}, correct_option=1, points=1)
    result = grade_question(q, user_answer=3)
    assert result.correct is False


# ===========================================================================
# True / False
# ===========================================================================

def test_true_false_correct_true():
    q = MockQuestion("true_false", {"correct": True}, points=1)
    result = grade_question(q, user_answer=True)
    assert result.correct is True
    assert result.points_earned == 1

def test_true_false_correct_false():
    q = MockQuestion("true_false", {"correct": False}, points=1)
    result = grade_question(q, user_answer=False)
    assert result.correct is True

def test_true_false_wrong():
    q = MockQuestion("true_false", {"correct": True}, points=1)
    result = grade_question(q, user_answer=False)
    assert result.correct is False
    assert result.points_earned == 0

def test_true_false_none_answer_skipped():
    q = MockQuestion("true_false", {"correct": True}, points=1)
    result = grade_question(q, user_answer=None)
    assert result.correct is False
    assert result.points_earned == 0

def test_true_false_missing_key_returns_wrong():
    """If answer_key has no 'correct' key, grade as wrong (safe default)."""
    q = MockQuestion("true_false", {}, points=1)
    result = grade_question(q, user_answer=True)
    assert result.correct is False


# ===========================================================================
# Fill in the Blank
# ===========================================================================

def test_fill_blank_correct():
    q = MockQuestion("fill_blank", {"accepted_answers": ["mitochondria", "mitochondrion"]}, points=1)
    result = grade_question(q, user_answer="mitochondria")
    assert result.correct is True
    assert result.points_earned == 1

def test_fill_blank_wrong():
    q = MockQuestion("fill_blank", {"accepted_answers": ["mitochondria"]}, points=1)
    result = grade_question(q, user_answer="nucleus")
    assert result.correct is False
    assert result.points_earned == 0

def test_fill_blank_case_insensitive():
    """Matching must be case-insensitive — 'MITOCHONDRIA' == 'mitochondria'."""
    q = MockQuestion("fill_blank", {"accepted_answers": ["mitochondria"]}, points=1)
    result = grade_question(q, user_answer="MITOCHONDRIA")
    assert result.correct is True

def test_fill_blank_whitespace_trimmed():
    """Leading/trailing whitespace in user answer must be ignored."""
    q = MockQuestion("fill_blank", {"accepted_answers": ["mitochondria"]}, points=1)
    result = grade_question(q, user_answer="  mitochondria  ")
    assert result.correct is True

def test_fill_blank_empty_string_skipped():
    q = MockQuestion("fill_blank", {"accepted_answers": ["mitochondria"]}, points=1)
    result = grade_question(q, user_answer="")
    assert result.correct is False

def test_fill_blank_non_string_skipped():
    """Non-string user answer (e.g. accidentally sent int) must not crash."""
    q = MockQuestion("fill_blank", {"accepted_answers": ["42"]}, points=1)
    result = grade_question(q, user_answer=42)
    assert result.correct is False


# ===========================================================================
# Short Answer  (Gemini grader mocked)
# ===========================================================================

def test_short_answer_correct_via_ai(mocker):
    """AI returns score=0.8 → correct=True, points_earned proportional."""
    mock_ai = mocker.patch(
        "app.services.grading_service.grade_short_answer_with_ai",
        return_value={"correct": True, "score": 0.8, "points_earned": 2, "ai_feedback": "Good."},
    )
    q = MockQuestion("short_answer", {"reference_answer": "Photosynthesis converts light to glucose."}, points=2)
    result = grade_question(q, user_answer="Plants use sunlight to make glucose.")
    assert result.correct is True
    assert result.points_earned == 2
    mock_ai.assert_called_once()

def test_short_answer_wrong_via_ai(mocker):
    """AI returns score=0.3 → correct=False."""
    mocker.patch(
        "app.services.grading_service.grade_short_answer_with_ai",
        return_value={"correct": False, "score": 0.3, "points_earned": 0, "ai_feedback": "Incomplete."},
    )
    q = MockQuestion("short_answer", {"reference_answer": "Photosynthesis converts light to glucose."}, points=1)
    result = grade_question(q, user_answer="Plants need water.")
    assert result.correct is False
    assert result.points_earned == 0

def test_short_answer_boundary_score_060_is_correct(mocker):
    """Score exactly 0.6 must be correct (>= 0.6 threshold)."""
    mocker.patch(
        "app.services.grading_service.grade_short_answer_with_ai",
        return_value={"correct": True, "score": 0.6, "points_earned": 1, "ai_feedback": "Borderline."},
    )
    q = MockQuestion("short_answer", {"reference_answer": "Some reference."}, points=1)
    result = grade_question(q, user_answer="Some partial answer.")
    assert result.correct is True

def test_short_answer_empty_skipped_no_ai_call(mocker):
    """Empty answer must short-circuit before calling AI."""
    mock_ai = mocker.patch("app.services.grading_service.grade_short_answer_with_ai")
    q = MockQuestion("short_answer", {"reference_answer": "Some reference."}, points=1)
    result = grade_question(q, user_answer="")
    assert result.correct is False
    assert result.points_earned == 0
    mock_ai.assert_not_called()

def test_short_answer_no_reference_returns_wrong(mocker):
    """If no reference_answer is stored, grade as wrong (safe default)."""
    mock_ai = mocker.patch("app.services.grading_service.grade_short_answer_with_ai")
    q = MockQuestion("short_answer", {}, points=1)
    result = grade_question(q, user_answer="Some valid answer here.")
    assert result.correct is False
    mock_ai.assert_not_called()


# ===========================================================================
# Matching
# ===========================================================================

def test_matching_all_correct():
    q = MockQuestion("matching", {"pairs": [[0, 0], [1, 1], [2, 2]]}, points=1)
    result = grade_question(q, user_answer=[[0, 0], [1, 1], [2, 2]])
    assert result.correct is True
    assert result.points_earned == 1

def test_matching_wrong_pair():
    q = MockQuestion("matching", {"pairs": [[0, 0], [1, 1]]}, points=1)
    result = grade_question(q, user_answer=[[0, 1], [1, 0]])   # swapped
    assert result.correct is False
    assert result.points_earned == 0

def test_matching_order_of_pairs_doesnt_matter():
    """Submitting pairs in different order must still be correct (set comparison)."""
    q = MockQuestion("matching", {"pairs": [[0, 0], [1, 1]]}, points=1)
    result = grade_question(q, user_answer=[[1, 1], [0, 0]])   # reversed order
    assert result.correct is True

def test_matching_one_pair_wrong_is_all_wrong():
    """Grader is all-or-nothing — one wrong pair means zero points."""
    q = MockQuestion("matching", {"pairs": [[0, 0], [1, 1], [2, 2]]}, points=3)
    result = grade_question(q, user_answer=[[0, 0], [1, 1], [2, 1]])   # last pair wrong
    assert result.correct is False
    assert result.points_earned == 0

def test_matching_none_answer_skipped():
    q = MockQuestion("matching", {"pairs": [[0, 0]]}, points=1)
    result = grade_question(q, user_answer=None)
    assert result.correct is False

def test_matching_empty_list_skipped():
    q = MockQuestion("matching", {"pairs": [[0, 0]]}, points=1)
    result = grade_question(q, user_answer=[])
    assert result.correct is False


# ===========================================================================
# Ordering
# ===========================================================================

def test_ordering_correct():
    q = MockQuestion("ordering", {"correct_order": [0, 1, 2, 3]}, points=1)
    result = grade_question(q, user_answer=[0, 1, 2, 3])
    assert result.correct is True
    assert result.points_earned == 1

def test_ordering_wrong_completely_reversed():
    q = MockQuestion("ordering", {"correct_order": [0, 1, 2]}, points=1)
    result = grade_question(q, user_answer=[2, 1, 0])
    assert result.correct is False
    assert result.points_earned == 0

def test_ordering_off_by_one_position():
    """One element out of place → entire sequence is wrong."""
    q = MockQuestion("ordering", {"correct_order": [0, 1, 2, 3]}, points=1)
    result = grade_question(q, user_answer=[0, 2, 1, 3])   # positions 1 and 2 swapped
    assert result.correct is False
    assert result.points_earned == 0

def test_ordering_none_answer_skipped():
    q = MockQuestion("ordering", {"correct_order": [0, 1, 2]}, points=1)
    result = grade_question(q, user_answer=None)
    assert result.correct is False

def test_ordering_empty_list_skipped():
    q = MockQuestion("ordering", {"correct_order": [0, 1, 2]}, points=1)
    result = grade_question(q, user_answer=[])
    assert result.correct is False


# ===========================================================================
# Numeric
# ===========================================================================

def test_numeric_exact_match():
    q = MockQuestion("numeric", {"value": 9.8, "tolerance": 0.0}, points=1)
    result = grade_question(q, user_answer=9.8)
    assert result.correct is True
    assert result.points_earned == 1

def test_numeric_within_tolerance():
    q = MockQuestion("numeric", {"value": 9.8, "tolerance": 0.5}, points=1)
    result = grade_question(q, user_answer=10.1)
    assert result.correct is True

def test_numeric_outside_tolerance():
    q = MockQuestion("numeric", {"value": 9.8, "tolerance": 0.5}, points=1)
    result = grade_question(q, user_answer=15.0)
    assert result.correct is False
    assert result.points_earned == 0

def test_numeric_boundary_exactly_at_tolerance_correct():
    """Value exactly at the tolerance boundary (abs diff == tolerance) must be correct."""
    q = MockQuestion("numeric", {"value": 9.8, "tolerance": 0.5}, points=1)
    result = grade_question(q, user_answer=10.3)   # 10.3 - 9.8 = 0.5 exactly
    assert result.correct is True

def test_numeric_just_outside_boundary_wrong():
    """Value just beyond tolerance boundary must be wrong."""
    q = MockQuestion("numeric", {"value": 9.8, "tolerance": 0.5}, points=1)
    result = grade_question(q, user_answer=10.31)
    assert result.correct is False

def test_numeric_string_answer_coerced():
    """Frontend may send number as string — float() coercion must work."""
    q = MockQuestion("numeric", {"value": 100.0, "tolerance": 0.0}, points=1)
    result = grade_question(q, user_answer="100")
    assert result.correct is True

def test_numeric_non_numeric_string_skipped():
    """Non-numeric string must not crash — returns wrong."""
    q = MockQuestion("numeric", {"value": 100.0, "tolerance": 0.0}, points=1)
    result = grade_question(q, user_answer="not-a-number")
    assert result.correct is False

def test_numeric_none_skipped():
    q = MockQuestion("numeric", {"value": 9.8, "tolerance": 0.0}, points=1)
    result = grade_question(q, user_answer=None)
    assert result.correct is False

def test_numeric_zero_tolerance_must_be_exact():
    """tolerance=0 (or null) means exact match only."""
    q = MockQuestion("numeric", {"value": 42.0, "tolerance": None}, points=1)
    result = grade_question(q, user_answer=42.0)
    assert result.correct is True
    result2 = grade_question(q, user_answer=42.1)
    assert result2.correct is False


# ===========================================================================
# Dispatcher fallback
# ===========================================================================

def test_unknown_type_falls_back_to_mcq():
    """grade_question falls back to MCQ grader for unrecognised type strings."""
    q = MockQuestion("essay", {"correct_index": 0}, correct_option=0, points=1)
    result = grade_question(q, user_answer=0)
    assert isinstance(result, GradeResult)
    assert result.correct is True

def test_none_type_falls_back_to_mcq():
    """question.type = None must also fall back to MCQ gracefully."""
    q = MockQuestion(None, {"correct_index": 1}, correct_option=1, points=1)
    result = grade_question(q, user_answer=1)
    assert result.correct is True
