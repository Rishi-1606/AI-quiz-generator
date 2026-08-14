"""
GenerationJob — tracks async AI generation requests.

Status lifecycle: pending → processing → complete | failed

- pending:    Job created, background task queued, not yet started.
- processing: Background worker has started the Gemini call.
- complete:   Gemini returned successfully; result_id holds the quiz ID
              (or result_data holds flashcard JSON).
- failed:     Gemini call or DB save failed; error_message has details.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from app.database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    # UUID string so job IDs are unguessable by other users
    id           = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id      = Column(Integer, nullable=False, index=True)

    # "quiz_from_doc" | "quiz_from_topic" | "flashcards"
    job_type     = Column(String(32), nullable=False)

    # "pending" | "processing" | "complete" | "failed"
    status       = Column(String(16), nullable=False, default="pending")

    # Set on success — quiz ID for quiz jobs
    result_id    = Column(Integer, nullable=True)

    # Set on success for flashcard jobs (JSON array of {front, back})
    result_data  = Column(Text, nullable=True)

    # Set on failure
    error_message = Column(Text, nullable=True)

    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
