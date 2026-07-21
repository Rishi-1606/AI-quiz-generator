from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"), nullable=False)
    quiz_id         = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)

    # Score breakdown
    score           = Column(Integer, nullable=False, default=0)   # number of correct answers
    total           = Column(Integer, nullable=False, default=0)   # total questions in the quiz
    correct         = Column(Integer, nullable=False, default=0)
    wrong           = Column(Integer, nullable=False, default=0)
    skipped         = Column(Integer, nullable=False, default=0)
    percentage      = Column(Float,   nullable=False, default=0.0) # 0.0–100.0

    # User's selected answers: {question_id: selected_option_index or null if skipped}
    answers         = Column(JSON, nullable=True)

    # AI-generated personalized study feedback
    ai_feedback     = Column(Text, nullable=True)

    # Timing
    time_taken      = Column(Integer, nullable=True)               # seconds taken to complete
    attempted_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="attempts")
    quiz = relationship("Quiz", back_populates="attempts")

    def __repr__(self):
        return f"<Attempt(id={self.id}, user_id={self.user_id}, quiz_id={self.quiz_id}, score={self.score}/{self.total})>"
