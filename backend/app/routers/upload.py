import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.upload import Upload
from app.schemas.upload import UploadResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])


@router.get("", response_model=List[UploadResponse])
def get_uploads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all uploaded documents for the current user."""
    uploads = db.query(Upload).filter(Upload.user_id == current_user.id).order_by(Upload.uploaded_at.desc()).all()
    return uploads


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an uploaded document by ID (database metadata and file on disk)."""
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == current_user.id).first()
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete the physical file if it exists
    if upload.storage_path and os.path.exists(upload.storage_path):
        try:
            os.remove(upload.storage_path)
        except Exception as e:
            # We can log this but still proceed with DB deletion
            print(f"[ERROR] Failed to delete file at {upload.storage_path}: {e}")

    db.delete(upload)
    db.commit()
    return None
