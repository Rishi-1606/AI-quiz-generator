"""
Sprint 7 - Step 3: Unit tests for ai_service.py

All Gemini API calls are mocked — no real API keys or network needed.
Mock target: app.services.ai_service.genai.Client

Each test patches the Client constructor so that
client.models.generate_content(...).text returns a controlled JSON string,
letting us test our parsing, validation, and logic in isolation.
"""

import json
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helper: build a mock genai.Client that returns a given text response
# ---------------------------------------------------------------------------

def _mock_client(mocker, response_text: str):
    """
    Patch genai.Client so any instantiation returns a mock whose
    models.generate_content(...).text == response_text.
    Returns the mock instance for assertion checks.
    """
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value.text = response_text
    mocker.patch("app.services.ai_service.genai.Client", return_value=mock_instance)
    return mock_instance


# ===========================================================================
# generate_questions_from_chunk
# ===========================================================================

def test_chunk_generates_valid_mcq(mocker):
    """Valid MCQ JSON returned by Gemini is parsed and validated correctly."""
    from app.services.ai_service import generate_questions_from_chunk

    raw = json.dumps([{
        "type": "mcq",
        "question": "What is 2 + 2?",
        "options": ["1", "2", "3", "4"],
        "correct_option": 3,
        "explanation": "2 + 2 equals 4.",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_chunk("Some study text.", num_questions=1, question_types=["mcq"])

    assert len(result) == 1
    q = result[0]
    assert q["type"] == "mcq"
    assert q["payload"]["options"] == ["1", "2", "3", "4"]
    assert q["answer_key"]["correct_index"] == 3
    assert q["explanation"] == "2 + 2 equals 4."


def test_chunk_generates_valid_true_false(mocker):
    """Valid true_false JSON is parsed and answer_key has correct bool."""
    from app.services.ai_service import generate_questions_from_chunk

    raw = json.dumps([{
        "type": "true_false",
        "question": "The sky is blue.",
        "correct_answer": True,
        "explanation": "The sky appears blue due to Rayleigh scattering.",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_chunk("Some text.", num_questions=1, question_types=["true_false"])

    assert len(result) == 1
    q = result[0]
    assert q["type"] == "true_false"
    assert q["answer_key"]["correct"] is True


def test_chunk_generates_valid_fill_blank(mocker):
    """Valid fill_blank JSON is parsed; accepted_answers preserved."""
    from app.services.ai_service import generate_questions_from_chunk

    raw = json.dumps([{
        "type": "fill_blank",
        "question": "The ___ is the powerhouse of the cell.",
        "text_with_blanks": "The ___ is the powerhouse of the cell.",
        "accepted_answers": ["mitochondria", "mitochondrion"],
        "explanation": "Mitochondria produce ATP.",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_chunk("Some text.", num_questions=1, question_types=["fill_blank"])

    assert len(result) == 1
    q = result[0]
    assert q["type"] == "fill_blank"
    assert "mitochondria" in q["answer_key"]["accepted_answers"]


def test_chunk_generates_valid_short_answer(mocker):
    """Valid short_answer JSON is parsed; reference_answer stored in answer_key."""
    from app.services.ai_service import generate_questions_from_chunk

    raw = json.dumps([{
        "type": "short_answer",
        "question": "Explain photosynthesis.",
        "reference_answer": "Plants convert light energy into glucose using CO2 and water.",
        "explanation": "Key concept: light-dependent reactions.",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_chunk("Some text.", num_questions=1, question_types=["short_answer"])

    assert len(result) == 1
    q = result[0]
    assert q["type"] == "short_answer"
    assert "reference_answer" in q["answer_key"]


def test_chunk_rejects_unknown_type(mocker):
    """Questions with a type not in allowed_types are silently dropped."""
    from app.services.ai_service import generate_questions_from_chunk

    raw = json.dumps([{
        "type": "essay",
        "question": "Write an essay about history.",
        "answer": "Some long answer.",
        "explanation": "N/A",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_chunk("Some text.", num_questions=1, question_types=["mcq"])

    # "essay" is not in allowed_types ["mcq"] — must be filtered out
    assert result == []


def test_chunk_rejects_mcq_with_wrong_option_count(mocker):
    """MCQ with fewer than 4 options is rejected by the validator."""
    from app.services.ai_service import generate_questions_from_chunk

    raw = json.dumps([{
        "type": "mcq",
        "question": "Pick one.",
        "options": ["A", "B"],      # only 2 — validator requires exactly 4
        "correct_option": 0,
        "explanation": "Explanation.",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_chunk("Some text.", num_questions=1, question_types=["mcq"])

    assert result == []


def test_chunk_returns_empty_on_empty_text(mocker):
    """Empty or whitespace-only text must return [] without calling Gemini."""
    from app.services.ai_service import generate_questions_from_chunk

    mock_instance = MagicMock()
    mocker.patch("app.services.ai_service.genai.Client", return_value=mock_instance)

    result = generate_questions_from_chunk("   ", num_questions=5)

    assert result == []
    mock_instance.models.generate_content.assert_not_called()


def test_chunk_strips_markdown_code_fences(mocker):
    """Gemini sometimes wraps JSON in ```json ... ``` — _strip_fences must handle it."""
    from app.services.ai_service import generate_questions_from_chunk

    inner = json.dumps([{
        "type": "mcq",
        "question": "What is H2O?",
        "options": ["Fire", "Water", "Earth", "Air"],
        "correct_option": 1,
        "explanation": "H2O is the chemical formula for water.",
    }])
    # Simulate Gemini wrapping response in code fences
    fenced = f"```json\n{inner}\n```"
    _mock_client(mocker, fenced)

    result = generate_questions_from_chunk("Some text.", num_questions=1, question_types=["mcq"])

    assert len(result) == 1
    assert result[0]["type"] == "mcq"


def test_chunk_true_false_string_coercion(mocker):
    """If Gemini returns correct_answer as string 'true', it must be coerced to bool True."""
    from app.services.ai_service import generate_questions_from_chunk

    raw = json.dumps([{
        "type": "true_false",
        "question": "Water boils at 100°C at sea level.",
        "correct_answer": "true",   # string instead of JSON bool
        "explanation": "At standard atmospheric pressure, 100°C.",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_chunk("Some text.", num_questions=1, question_types=["true_false"])

    assert len(result) == 1
    assert result[0]["answer_key"]["correct"] is True


def test_chunk_fill_blank_string_answer_wrapped(mocker):
    """If accepted_answers is a bare string, validator must wrap it in a list."""
    from app.services.ai_service import generate_questions_from_chunk

    raw = json.dumps([{
        "type": "fill_blank",
        "question": "The capital of France is ___.",
        "accepted_answers": "Paris",   # string, not list
        "explanation": "Paris is the capital.",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_chunk("Some text.", num_questions=1, question_types=["fill_blank"])

    assert len(result) == 1
    assert isinstance(result[0]["answer_key"]["accepted_answers"], list)
    assert "Paris" in result[0]["answer_key"]["accepted_answers"]


# ===========================================================================
# generate_questions_from_topic
# ===========================================================================

def test_topic_generates_valid_mcq(mocker):
    """Topic-based generation returns valid MCQ when Gemini responds correctly."""
    from app.services.ai_service import generate_questions_from_topic

    raw = json.dumps([{
        "type": "mcq",
        "question": "What planet is closest to the Sun?",
        "options": ["Venus", "Mercury", "Earth", "Mars"],
        "correct_option": 1,
        "explanation": "Mercury is the closest planet to the Sun.",
    }])
    _mock_client(mocker, raw)

    result = generate_questions_from_topic("Solar System", num_questions=1, question_types=["mcq"])

    assert len(result) == 1
    assert result[0]["type"] == "mcq"
    assert result[0]["answer_key"]["correct_index"] == 1


def test_topic_returns_empty_on_empty_topic(mocker):
    """Empty or whitespace topic must return [] without calling Gemini."""
    from app.services.ai_service import generate_questions_from_topic

    mock_instance = MagicMock()
    mocker.patch("app.services.ai_service.genai.Client", return_value=mock_instance)

    result = generate_questions_from_topic("   ")

    assert result == []
    mock_instance.models.generate_content.assert_not_called()


# ===========================================================================
# grade_short_answer_with_ai
# ===========================================================================

def test_grade_short_answer_correct(mocker):
    """score=0.8 >= 0.6 threshold → correct=True, points_earned proportional."""
    from app.services.ai_service import grade_short_answer_with_ai

    _mock_client(mocker, json.dumps({"score": 0.8, "feedback": "Good answer."}))

    result = grade_short_answer_with_ai(
        question_text="Explain gravity.",
        reference_answer="Gravity is the force that attracts masses.",
        user_answer="Gravity pulls objects toward each other.",
        points=2,
    )

    assert result["correct"] is True
    assert result["score"] == 0.8
    assert result["points_earned"] == round(0.8 * 2)
    assert "Good answer." in result["ai_feedback"]


def test_grade_short_answer_wrong(mocker):
    """score=0.3 < 0.6 threshold → correct=False."""
    from app.services.ai_service import grade_short_answer_with_ai

    _mock_client(mocker, json.dumps({"score": 0.3, "feedback": "Incomplete answer."}))

    result = grade_short_answer_with_ai(
        question_text="Explain gravity.",
        reference_answer="Gravity is the force that attracts masses.",
        user_answer="Something vague.",
        points=1,
    )

    assert result["correct"] is False
    assert result["score"] == 0.3
    assert result["points_earned"] == 0


def test_grade_short_answer_boundary_exactly_06(mocker):
    """score exactly 0.6 must be correct (>= threshold, not >)."""
    from app.services.ai_service import grade_short_answer_with_ai

    _mock_client(mocker, json.dumps({"score": 0.6, "feedback": "Borderline."}))

    result = grade_short_answer_with_ai(
        question_text="What is osmosis?",
        reference_answer="Movement of water across a semi-permeable membrane.",
        user_answer="Water moving through a membrane.",
        points=1,
    )

    assert result["correct"] is True


def test_grade_short_answer_empty_no_api_call(mocker):
    """Empty user_answer returns immediately without calling Gemini."""
    from app.services.ai_service import grade_short_answer_with_ai

    mock_instance = MagicMock()
    mocker.patch("app.services.ai_service.genai.Client", return_value=mock_instance)

    result = grade_short_answer_with_ai(
        question_text="Explain gravity.",
        reference_answer="Some reference.",
        user_answer="",
        points=1,
    )

    assert result["correct"] is False
    assert result["score"] == 0.0
    assert result["points_earned"] == 0
    mock_instance.models.generate_content.assert_not_called()


def test_grade_short_answer_score_clamped(mocker):
    """Score > 1.0 returned by Gemini must be clamped to 1.0."""
    from app.services.ai_service import grade_short_answer_with_ai

    _mock_client(mocker, json.dumps({"score": 1.5, "feedback": "Excellent!"}))

    result = grade_short_answer_with_ai(
        question_text="Q?",
        reference_answer="Reference.",
        user_answer="Perfect answer.",
        points=1,
    )

    assert result["score"] == 1.0
    assert result["correct"] is True


# ===========================================================================
# generate_feedback
# ===========================================================================

def test_generate_feedback_with_wrong_questions(mocker):
    """When wrong_questions is non-empty, Gemini is called and text returned."""
    from app.services.ai_service import generate_feedback

    mock_instance = _mock_client(mocker, "You should review the topic of photosynthesis.")

    wrong = [{
        "question_text": "What is photosynthesis?",
        "options": ["A", "B", "C", "D"],
        "correct_option": 1,
        "explanation": "Light-dependent reactions.",
    }]

    result = generate_feedback(wrong_questions=wrong, correct_count=4, total=5, difficulty="medium")

    assert "photosynthesis" in result.lower()
    mock_instance.models.generate_content.assert_called_once()


def test_generate_feedback_all_correct_no_api_call(mocker):
    """Perfect score returns canned message without calling Gemini."""
    from app.services.ai_service import generate_feedback

    mock_instance = MagicMock()
    mocker.patch("app.services.ai_service.genai.Client", return_value=mock_instance)

    result = generate_feedback(wrong_questions=[], correct_count=5, total=5, difficulty="easy")

    assert "5" in result          # mentions total
    assert result != ""           # not empty
    mock_instance.models.generate_content.assert_not_called()
