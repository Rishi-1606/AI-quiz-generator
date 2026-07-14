import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.upload import Upload
from app.schemas.upload import UploadResponse
from app.middleware.auth import get_current_user
from app.config import UPLOAD_DIR
from app.services.extractor import extract_text

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a document, validate it, save it to the local filesystem,
    and record its metadata in the database.
    """
    # Extract file extension
    filename = file.filename or "unnamed_file"
    file_ext = filename.split(".")[-1].lower() if "." in filename else ""

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Determine file size
    try:
        # Seek to the end of the file to determine size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        # Seek back to the beginning of the file so we can read it later
        file.file.seek(0)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file size: {str(e)}",
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is too large. Maximum size allowed is 10 MB.",
        )

    # Ensure uploads directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate a unique filename to prevent collisions on disk
    unique_filename = f"{uuid.uuid4()}_{filename}"
    storage_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file to disk
    try:
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file to storage: {str(e)}",
        )

    # Save metadata to database
    try:
        # Extract text from the file immediately after saving
        extracted = extract_text(storage_path, file_ext)

        new_upload = Upload(
            user_id=current_user.id,
            filename=filename,
            file_type=file_ext,
            file_size=file_size,
            storage_path=storage_path,
            extracted_text=extracted,
        )
        db.add(new_upload)
        db.commit()
        db.refresh(new_upload)
    except Exception as e:
        # Clean up the file if DB insert fails
        if os.path.exists(storage_path):
            os.remove(storage_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record upload metadata: {str(e)}",
        )

    return new_upload


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
