from sqlalchemy import Column, Integer, Text, JSON, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id       = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)

    # ── New generalized columns (Sprint 1) ────────────────────────────────────
    type       = Column(String(20), nullable=False, default="mcq")
    # payload:    JSON shape depends on `type` — see app/constants/question_types.py
    payload    = Column(JSON, nullable=True)
    # answer_key: JSON shape depends on `type` — never returned to client during quiz
    answer_key = Column(JSON, nullable=True)
    points     = Column(Integer, nullable=False, default=1)
    media_url  = Column(Text, nullable=True)

    # ── DEPRECATED columns (kept for backward compat — drop in Sprint 12) ─────
    # These are still written via dual-write in Sprint 1.
    # Do NOT add new code that reads these directly; use payload/answer_key instead.
    options        = Column(JSON, nullable=True)    # DEPRECATED: use payload["options"]
    correct_option = Column(Integer, nullable=True) # DEPRECATED: use answer_key["correct_index"]

    explanation = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")

    def __repr__(self):
        return f"<Question(id={self.id}, type='{self.type}', quiz_id={self.quiz_id}, order={self.order_index})>"
