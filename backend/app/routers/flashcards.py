from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.upload import Upload
from app.middleware.auth import get_current_user
from app.services.text_processor import process_text
from app.services.ai_service import generate_flashcards

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


@router.post("/generate", response_model=FlashcardsResponse, status_code=status.HTTP_200_OK)
def generate(
    body: GenerateFlashcardsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate flashcards from an uploaded document using Gemini AI."""
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

    processed = process_text(upload.extracted_text)
    text_chunk = processed["chunks"][0] if processed["chunks"] else upload.extracted_text[:3000]

    cards = generate_flashcards(text_chunk, num_cards=body.num_cards)

    if not cards:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="AI could not generate flashcards. Please try again.")

    return FlashcardsResponse(
        upload_id=upload.id,
        filename=upload.filename,
        cards=[FlashcardItem(**c) for c in cards],
    )
