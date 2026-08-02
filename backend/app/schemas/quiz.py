from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class QuestionResponse(BaseModel):
    id:            int
    question_text: str
    explanation:   Optional[str]
    order_index:   int
    points:        int = 1

    # ── New generalized fields (Sprint 1) ─────────────────────────────────────
    type:       str = "mcq"         # "mcq" | "true_false" | "fill_blank" | etc.
    payload:    Optional[Dict[str, Any]] = None  # shape depends on `type`
    # Note: answer_key is intentionally EXCLUDED here —
    #       it must never be sent to the client during an active quiz session.

    # ── DEPRECATED fields (kept for backward compat with existing frontend) ───
    # TakeQuiz.jsx and QuizResults.jsx still read these until Sprint 3 refactor.
    options:        Optional[List[str]] = None   # DEPRECATED: use payload["options"]
    correct_option: Optional[int]       = None   # DEPRECATED: use answer_key["correct_index"]

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    id: int
    upload_id: Optional[int] = None
    title: str
    difficulty: str
    time_limit: int
    total_questions: int
    created_at: datetime
    questions: List[QuestionResponse]

    class Config:
        from_attributes = True


class QuizSummaryResponse(BaseModel):
    """Lightweight quiz card — used in list views (no questions)."""
    id: int
    upload_id: Optional[int] = None
    title: str
    difficulty: str
    time_limit: int
    total_questions: int
    created_at: datetime

    class Config:
        from_attributes = True
