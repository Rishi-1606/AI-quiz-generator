from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, pptx, txt
    file_size = Column(Integer, nullable=False)  # in bytes
    storage_path = Column(String(500), nullable=False)  # path on disk
    extracted_text = Column(Text, nullable=True)  # extracted raw text
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user    = relationship("User", back_populates="uploads")
    quizzes = relationship("Quiz", back_populates="upload", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Upload(id={self.id}, filename='{self.filename}', user_id={self.user_id})>"
