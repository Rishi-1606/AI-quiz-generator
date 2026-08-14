from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import json

from app.database import get_db
from app.models.user import User
from app.models.upload import Upload
from app.models.generation_job import GenerationJob
from app.middleware.auth import get_current_user
from app.services.job_service import run_flashcards_job
from app.limiter import limiter

router = APIRouter(prefix="/api/flashcards", tags=["Flashcards"])


class FlashcardItem(BaseModel):
    front: str
    back: str


class GenerateFlashcardsRequest(BaseModel):
    upload_id: int
    num_cards: int = 10


class FlashcardsResponse(BaseModel):
    upload_id: int
    filename:  str
    cards:     List[FlashcardItem]


# ─── Generate flashcards (async) ─────────────────────────────────────────────

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/hour")
def generate(
    request: Request,
    body: GenerateFlashcardsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enqueue a background flashcard-generation job and return immediately.
    Poll GET /api/flashcards/jobs/{job_id}/status to track progress.
    """
    upload = (
        db.query(Upload)
        .filter(Upload.id == body.upload_id, Upload.user_id == current_user.id)
        .first()
    )
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Document not found.")
    if not upload.extracted_text or not upload.extracted_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No text could be extracted from this document.")

    job = GenerationJob(
        user_id=current_user.id,
        job_type="flashcards",
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_flashcards_job,
        job_id=job.id,
        upload_id=body.upload_id,
        num_cards=body.num_cards,
    )

    return {"job_id": job.id, "status": "pending"}


# ─── Job status (flashcard jobs) ──────────────────────────────────────────────

@router.get("/jobs/{job_id}/status")
def get_flashcard_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Poll the status of a flashcard generation job.
    Returns: { job_id, status, result, error_message }
      - status: "pending" | "processing" | "complete" | "failed"
      - result: FlashcardsResponse payload (only when status=="complete")
      - error_message: set when status=="failed"
    """
    job = (
        db.query(GenerationJob)
        .filter(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id,
            GenerationJob.job_type == "flashcards",
        )
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    result = None
    if job.status == "complete" and job.result_data:
        result = json.loads(job.result_data)

    return {
        "job_id":        job.id,
        "status":        job.status,
        "result":        result,
        "error_message": job.error_message,
    }
