from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Optional


class SubmitQuizRequest(BaseModel):
    """
    Sent by the frontend when the user submits a quiz.

    answers: maps question_id (str) → chosen option index (int, 0-3)
             or null if the user skipped the question.

    time_taken: how many seconds the user spent on the quiz.

    Example:
    {
        "answers": {"1": 2, "2": null, "3": 0},
        "time_taken": 245
    }
    """
    answers: Dict[str, Optional[int]]   # {question_id: selected_option or null}
    time_taken: Optional[int] = None    # seconds


class AttemptResponse(BaseModel):
    """Returned after a quiz is submitted."""
    id:           int
    quiz_id:      int
    score:        int
    total:        int
    correct:      int
    wrong:        int
    skipped:      int
    percentage:   float
    answers:      Optional[Dict[str, Optional[int]]]
    ai_feedback:  Optional[str]
    time_taken:   Optional[int]
    attempted_at: datetime

    class Config:
        from_attributes = True
