"""
Question Types — Single source of truth for all supported question formats.

Each type defines the expected shape of `payload` and `answer_key` JSON columns.

Types:
  mcq           — Multiple choice (4 options, one correct)
  true_false    — True or False
  fill_blank    — Sentence with blank(s); user types answer
  short_answer  — Open-ended; AI-graded (Sprint 5)
  matching      — Match left-column items to right-column items
  ordering      — Arrange items in correct sequence
  numeric       — Enter a numeric value (with optional unit & tolerance)
"""

# Valid question type identifiers
QUESTION_TYPES = [
    "mcq",
    "true_false",
    "fill_blank",
    "short_answer",
    "matching",
    "ordering",
    "numeric",
]

# ── Payload shapes (what the client needs to render the question) ─────────────

PAYLOAD_SHAPES = {
    "mcq": {
        # options: list of exactly 4 answer strings
        "options": ["str", "str", "str", "str"],
    },
    "true_false": {
        # No extra payload needed — the question_text IS the statement
    },
    "fill_blank": {
        # text_with_blanks: the sentence with ___ marking each blank
        "text_with_blanks": "str",
    },
    "short_answer": {
        # No payload — user gets a free-text box
    },
    "matching": {
        # left: list of terms,  right: list of definitions (order is shuffled on client)
        "left":  ["str"],
        "right": ["str"],
    },
    "ordering": {
        # items: list of steps/events presented in SHUFFLED order to the user
        "items": ["str"],
    },
    "numeric": {
        # unit: optional unit label shown next to input (e.g. "km", "°C")
        # tolerance: acceptable margin of error (e.g. 0.01 means ±1%)
        "unit":      "str | null",
        "tolerance": "float | null",
    },
}

# ── Answer key shapes (stored server-side, never sent to client during quiz) ──

ANSWER_KEY_SHAPES = {
    "mcq": {
        # correct_index: 0-based index into payload.options
        "correct_index": "int (0–3)",
    },
    "true_false": {
        "correct": "bool",
    },
    "fill_blank": {
        # accepted_answers: list of acceptable strings (case-insensitive match)
        "accepted_answers": ["str"],
    },
    "short_answer": {
        # reference_answer: model answer used by AI grader (Sprint 5)
        "reference_answer": "str",
    },
    "matching": {
        # pairs: list of [left_index, right_index] correct pairings
        "pairs": [[0, 1], [1, 0]],   # example only
    },
    "ordering": {
        # correct_order: correct sequence expressed as indices into payload.items
        "correct_order": [2, 0, 1],  # example only
    },
    "numeric": {
        "value": "float",
    },
}
