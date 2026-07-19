from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"), nullable=False)
    upload_id     = Column(Integer, ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False)
    title         = Column(String(300), nullable=False)
    difficulty    = Column(String(10), nullable=False, default="medium")  # easy | medium | hard
    time_limit    = Column(Integer, nullable=False, default=600)          # seconds (default 10 min)
    total_questions = Column(Integer, nullable=False, default=0)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user      = relationship("User",     back_populates="quizzes")
    upload    = relationship("Upload",   back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts  = relationship("Attempt",  back_populates="quiz", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<Quiz(id={self.id}, title='{self.title}', user_id={self.user_id})>"
