from datetime import datetime
from pydantic import BaseModel
from typing import List


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    options: List[str]          # 4 choices
    correct_option: int         # 0-indexed
    explanation: str | None
    order_index: int

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    id: int
    upload_id: int
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
    upload_id: int
    title: str
    difficulty: str
    time_limit: int
    total_questions: int
    created_at: datetime

    class Config:
        from_attributes = True
