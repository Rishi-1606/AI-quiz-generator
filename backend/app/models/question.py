from sqlalchemy import Column, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id             = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text       = Column(Text, nullable=False)
    options             = Column(JSON, nullable=False)   # list of 4 strings ["A. ...", "B. ...", ...]
    correct_option      = Column(Integer, nullable=False) # 0-indexed (0=A, 1=B, 2=C, 3=D)
    explanation         = Column(Text, nullable=True)    # Why the correct answer is right
    order_index         = Column(Integer, nullable=False, default=0)  # question order in the quiz

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")

    def __repr__(self):
        return f"<Question(id={self.id}, quiz_id={self.quiz_id}, order={self.order_index})>"
