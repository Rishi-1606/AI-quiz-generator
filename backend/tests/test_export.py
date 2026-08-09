"""
Sprint 6 -- Export helper unit tests.

Tests _format_question_txt, _format_answer_key_line, and _format_question_json
for all 7 question types in both TXT and JSON formats.

No DB, no HTTP server, no Gemini calls needed -- pure unit tests using mock
Question objects.
"""
import sys, os, json

# Make sure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.routers.quiz import (
    _format_question_txt,
    _format_answer_key_line,
    _format_question_json,
)


# --- Mock Question ---

class MockQuestion:
    def __init__(self, q_type, payload, answer_key, question_text="Sample question?",
                 explanation="Sample explanation.", options=None, correct_option=None, points=1):
        self.type           = q_type
        self.payload        = payload
        self.answer_key     = answer_key
        self.question_text  = question_text
        self.explanation    = explanation
        self.options        = options
        self.correct_option = correct_option
        self.points         = points


# --- MCQ ---

def test_mcq_txt():
    q = MockQuestion("mcq", {"options": ["Paris", "London", "Berlin", "Rome"]}, {"correct_index": 0},
                     question_text="What is the capital of France?", explanation="Paris is the capital.")
    lines = _format_question_txt(1, q, include_answers=True)
    text = "\n".join(lines)
    assert "[MCQ]" in text
    assert "A) Paris" in text
    assert "B) London" in text
    assert "C) Berlin" in text
    assert "D) Rome" in text
    assert "Answer: A" in text
    assert "Paris is the capital" in text

def test_mcq_json():
    q = MockQuestion("mcq", {"options": ["Paris","London","Berlin","Rome"]}, {"correct_index": 0})
    r = _format_question_json(q, include_answers=True)
    assert r["type"] == "mcq"
    assert r["payload"]["options"] == ["Paris","London","Berlin","Rome"]
    assert r["answer_key"]["correct_index"] == 0

def test_mcq_json_no_answers():
    q = MockQuestion("mcq", {"options": ["Paris","London","Berlin","Rome"]}, {"correct_index": 0})
    r = _format_question_json(q, include_answers=False)
    assert "answer_key" not in r


# --- True / False ---

def test_true_false_txt():
    q = MockQuestion("true_false", {}, {"correct": True},
                     question_text="The Earth orbits the Sun.", explanation="Heliocentric model.")
    lines = _format_question_txt(2, q, include_answers=True)
    text = "\n".join(lines)
    assert "[TRUE_FALSE]" in text
    assert "Answer: True" in text
    assert "Heliocentric" in text

def test_true_false_answer_key_line():
    q = MockQuestion("true_false", {}, {"correct": False})
    assert _format_answer_key_line(2, q) == ["Q2: False"]

def test_true_false_json():
    q = MockQuestion("true_false", {}, {"correct": True})
    r = _format_question_json(q, include_answers=True)
    assert r["type"] == "true_false"
    assert r["answer_key"]["correct"] is True


# --- Fill in the Blank ---

def test_fill_blank_txt():
    q = MockQuestion("fill_blank",
                     {"text_with_blanks": "Photosynthesis converts ___ into glucose."},
                     {"accepted_answers": ["light","sunlight","light energy"]},
                     question_text="Fill in the blank.", explanation="Plants use light energy.")
    lines = _format_question_txt(3, q, include_answers=True)
    text = "\n".join(lines)
    assert "[FILL_BLANK]" in text
    assert "Photosynthesis converts" in text
    assert "Accepted:" in text
    assert "light" in text

def test_fill_blank_answer_key_line():
    q = MockQuestion("fill_blank", {}, {"accepted_answers": ["mitosis","cell division"]})
    r = _format_answer_key_line(3, q)
    assert "mitosis" in r[0]
    assert "cell division" in r[0]

def test_fill_blank_json():
    q = MockQuestion("fill_blank", {"text_with_blanks": "The ___ is the powerhouse."},
                     {"accepted_answers": ["mitochondria"]})
    r = _format_question_json(q, include_answers=True)
    assert r["type"] == "fill_blank"
    assert "text_with_blanks" in r["payload"]
    assert r["answer_key"]["accepted_answers"] == ["mitochondria"]


# --- Short Answer ---

def test_short_answer_txt():
    q = MockQuestion("short_answer", {}, {"reference_answer": "Photosynthesis converts light to glucose."},
                     question_text="Explain photosynthesis.", explanation="Key concept.")
    lines = _format_question_txt(4, q, include_answers=True)
    text = "\n".join(lines)
    assert "[SHORT_ANSWER]" in text
    assert "Reference Answer:" in text
    assert "glucose" in text
    assert "A)" not in text

def test_short_answer_answer_key_line():
    q = MockQuestion("short_answer", {}, {"reference_answer": "Newton's first law states..."})
    r = _format_answer_key_line(4, q)
    assert "Newton" in r[0]

def test_short_answer_json():
    q = MockQuestion("short_answer", {}, {"reference_answer": "Gravity is attraction between masses."})
    r = _format_question_json(q, include_answers=True)
    assert r["type"] == "short_answer"
    assert "reference_answer" in r["answer_key"]


# --- Matching ---

def test_matching_txt():
    q = MockQuestion("matching",
                     {"left": ["Dog","Cat"], "right": ["Canine","Feline"]},
                     {"pairs": [[0,0],[1,1]]},
                     question_text="Match animal to classification.", explanation="Dog=Canine, Cat=Feline.")
    lines = _format_question_txt(5, q, include_answers=True)
    text = "\n".join(lines)
    assert "[MATCHING]" in text
    assert "Left items:" in text
    assert "1. Dog" in text
    assert "Right items:" in text
    assert "A. Canine" in text
    assert "Pairs:" in text
    assert "1" in text

def test_matching_no_crash_none_payload():
    q = MockQuestion("matching", None, None)
    lines = _format_question_txt(5, q, include_answers=True)
    assert any("MATCHING" in l for l in lines)

def test_matching_json():
    q = MockQuestion("matching", {"left":["Dog","Cat"],"right":["Canine","Feline"]}, {"pairs":[[0,0],[1,1]]})
    r = _format_question_json(q, include_answers=True)
    assert r["type"] == "matching"
    assert r["payload"]["left"] == ["Dog","Cat"]
    assert r["answer_key"]["pairs"] == [[0,0],[1,1]]


# --- Ordering ---

def test_ordering_txt():
    q = MockQuestion("ordering",
                     {"items": ["Boil water","Add pasta","Drain","Serve"]},
                     {"correct_order": [0,1,2,3]},
                     question_text="Put pasta steps in order.", explanation="Boil first.")
    lines = _format_question_txt(6, q, include_answers=True)
    text = "\n".join(lines)
    assert "[ORDERING]" in text
    assert "Arrange in correct order:" in text
    assert "1. Boil water" in text
    assert "Correct order: 1, 2, 3, 4" in text

def test_ordering_no_crash_none_payload():
    q = MockQuestion("ordering", None, None)
    lines = _format_question_txt(6, q, include_answers=True)
    assert any("ORDERING" in l for l in lines)

def test_ordering_json():
    q = MockQuestion("ordering", {"items":["Step A","Step B","Step C"]}, {"correct_order":[2,0,1]})
    r = _format_question_json(q, include_answers=True)
    assert r["type"] == "ordering"
    assert r["payload"]["items"] == ["Step A","Step B","Step C"]
    assert r["answer_key"]["correct_order"] == [2,0,1]


# --- Numeric ---

def test_numeric_txt():
    q = MockQuestion("numeric",
                     {"unit": "km", "tolerance": 0.5},
                     {"value": 384400.0, "tolerance": 0.5},
                     question_text="Distance Earth to Moon?", explanation="~384,400 km.")
    lines = _format_question_txt(7, q, include_answers=True)
    text = "\n".join(lines)
    assert "[NUMERIC]" in text
    assert "Enter a numeric value in km" in text
    assert "384400.0" in text
    assert "0.5" in text

def test_numeric_no_crash_none_payload():
    q = MockQuestion("numeric", None, None)
    lines = _format_question_txt(7, q, include_answers=True)
    assert any("NUMERIC" in l for l in lines)

def test_numeric_answer_key_line():
    q = MockQuestion("numeric", {"unit": "C"}, {"value": 100.0})
    r = _format_answer_key_line(7, q)
    assert "100.0" in r[0]

def test_numeric_json():
    q = MockQuestion("numeric", {"unit":"km","tolerance":0.5}, {"value":384400.0,"tolerance":0.5})
    r = _format_question_json(q, include_answers=True)
    assert r["type"] == "numeric"
    assert r["payload"]["unit"] == "km"
    assert r["answer_key"]["value"] == 384400.0


# --- Integration ---

def test_mixed_quiz_no_crash():
    questions = [
        MockQuestion("mcq",          {"options":["A","B","C","D"]},     {"correct_index":0}),
        MockQuestion("true_false",   {},                                 {"correct":True}),
        MockQuestion("fill_blank",   {"text_with_blanks":"The ___."},    {"accepted_answers":["sun"]}),
        MockQuestion("short_answer", {},                                 {"reference_answer":"Some answer."}),
        MockQuestion("matching",     {"left":["X"],"right":["Y"]},      {"pairs":[[0,0]]}),
        MockQuestion("ordering",     {"items":["A","B"]},                {"correct_order":[0,1]}),
        MockQuestion("numeric",      {"unit":"m"},                       {"value":9.8,"tolerance":0.1}),
    ]
    for i, q in enumerate(questions, 1):
        assert isinstance(_format_question_txt(i, q, True), list)
        assert isinstance(_format_answer_key_line(i, q), list)
        d = _format_question_json(q, True)
        assert isinstance(d, dict)
        assert d["type"] == q.type

def test_include_answers_false_hides_keys():
    types = [
        MockQuestion("mcq",          {"options":["A","B","C","D"]},  {"correct_index":0}),
        MockQuestion("true_false",   {},                              {"correct":True}),
        MockQuestion("short_answer", {},                              {"reference_answer":"Ans."}),
        MockQuestion("numeric",      {"unit":"kg"},                   {"value":10.0}),
    ]
    for q in types:
        r = _format_question_json(q, include_answers=False)
        assert "answer_key" not in r, f"answer_key present for {q.type} when include_answers=False"
