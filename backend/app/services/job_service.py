"""
Job Service — Background workers for async AI generation (Sprint 10)
----------------------------------------------------------------------
Each function is designed to be passed to FastAPI's BackgroundTasks.
They open their own DB session (can't use FastAPI's Depends() in the
background) and update the GenerationJob row as they progress.

In-memory response cache
------------------------
A module-level dict stores previously computed Gemini responses keyed
by a SHA-256 hash of the inputs that affect output. Cache entries expire
after CACHE_TTL_SECONDS. The cache lives as long as the server process,
which is fine for a single-process deployment.

Cache key inputs:
  - Doc quiz:   sha256(doc_text_hash + difficulty + num_questions + sorted_types)
  - Topic quiz: sha256("topic:" + topic.lower().strip() + difficulty + num_questions + sorted_types)
  - Flashcards: sha256("flash:" + doc_text_hash + num_cards)
"""

import hashlib
import json
import time
import logging
from datetime import datetime

from app.database import SessionLocal
from app.models.generation_job import GenerationJob
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.upload import Upload
from app.services.ai_service import (
    generate_questions_from_chunk,
    generate_questions_from_topic,
    generate_flashcards,
)
from app.services.text_processor import process_text

logger = logging.getLogger(__name__)

# ─── In-memory cache ──────────────────────────────────────────────────────────

CACHE_TTL_SECONDS = 86_400  # 24 hours

# { cache_key: {"result": <data>, "expires_at": <unix_timestamp>} }
_cache: dict[str, dict] = {}


def _make_key(*parts: str) -> str:
    """SHA-256 hash of all input parts joined by '|'."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def _text_hash(text: str) -> str:
    """SHA-256 of the raw document text — same content = same hash regardless of filename."""
    return hashlib.sha256(text.encode()).hexdigest()


def _cache_get(key: str):
    """Return cached value or None if missing/expired."""
    entry = _cache.get(key)
    if entry is None:
        return None
    if time.time() > entry["expires_at"]:
        del _cache[key]
        return None
    return entry["result"]


def _cache_set(key: str, result) -> None:
    """Store result in cache with a TTL."""
    _cache[key] = {"result": result, "expires_at": time.time() + CACHE_TTL_SECONDS}


# ─── DB helpers ───────────────────────────────────────────────────────────────

def _set_status(db, job: GenerationJob, status: str, **kwargs) -> None:
    """Update job status and any extra fields, then commit."""
    job.status = status
    job.updated_at = datetime.utcnow()
    for k, v in kwargs.items():
        setattr(job, k, v)
    db.commit()


# ─── Worker: quiz from document ───────────────────────────────────────────────

def run_quiz_from_doc_job(
    job_id: str,
    upload_id: int,
    num_questions: int,
    difficulty: str,
    question_types: list[str],
) -> None:
    """
    Background worker for POST /api/quizzes/generate.
    Opens its own DB session — never use FastAPI Depends() here.
    """
    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error("Job %s not found in DB", job_id)
            return

        _set_status(db, job, "processing")

        # Fetch the upload
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload or not upload.extracted_text:
            _set_status(db, job, "failed", error_message="Document not found or has no extractable text.")
            return

        processed = process_text(upload.extracted_text)
        if not processed["chunks"]:
            _set_status(db, job, "failed", error_message="Document text is too short to generate a quiz.")
            return

        text_chunk = processed["chunks"][0]

        # Check cache before calling Gemini
        cache_key = _make_key(
            _text_hash(upload.extracted_text),
            difficulty,
            num_questions,
            *sorted(question_types),
        )
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.info("Cache HIT for job %s", job_id)
            ai_questions = cached
        else:
            logger.info("Cache MISS for job %s — calling Gemini", job_id)
            try:
                ai_questions = generate_questions_from_chunk(
                    text=text_chunk,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    question_types=question_types,
                )
            except Exception as exc:
                _set_status(db, job, "failed", error_message=f"AI service error: {exc}")
                return

            if not ai_questions:
                _set_status(db, job, "failed", error_message="AI did not return any valid questions. Please try again.")
                return

            _cache_set(cache_key, ai_questions)

        # Save quiz + questions to DB
        display_name = upload.filename.rsplit(".", 1)[0]
        quiz_title   = f"{display_name} — {difficulty.capitalize()} Quiz"
        time_limit   = len(ai_questions) * 60

        new_quiz = Quiz(
            user_id=job.user_id,
            upload_id=upload_id,
            title=quiz_title,
            difficulty=difficulty,
            time_limit=time_limit,
            total_questions=len(ai_questions),
        )
        db.add(new_quiz)
        db.flush()

        for index, q in enumerate(ai_questions):
            db.add(Question(
                quiz_id=new_quiz.id,
                question_text=q["question"],
                type=q.get("type", "mcq"),
                payload=q.get("payload", {}),
                answer_key=q.get("answer_key", {}),
                points=1,
                explanation=q.get("explanation", ""),
                order_index=index,
            ))

        _set_status(db, job, "complete", result_id=new_quiz.id)
        db.commit()
        logger.info("Job %s complete — quiz_id=%s", job_id, new_quiz.id)

    except Exception as exc:
        logger.exception("Unhandled error in job %s", job_id)
        try:
            _set_status(db, job, "failed", error_message=f"Unexpected error: {exc}")
        except Exception:
            pass
    finally:
        db.close()


# ─── Worker: quiz from topic ──────────────────────────────────────────────────

def run_quiz_from_topic_job(
    job_id: str,
    topic: str,
    num_questions: int,
    difficulty: str,
    question_types: list[str],
) -> None:
    """
    Background worker for POST /api/quizzes/generate-from-topic.
    """
    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error("Job %s not found in DB", job_id)
            return

        _set_status(db, job, "processing")

        # Check cache
        cache_key = _make_key(
            "topic",
            topic.lower().strip(),
            difficulty,
            num_questions,
            *sorted(question_types),
        )
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.info("Cache HIT for topic job %s", job_id)
            ai_questions = cached
        else:
            logger.info("Cache MISS for topic job %s — calling Gemini", job_id)
            try:
                ai_questions = generate_questions_from_topic(
                    topic=topic,
                    num_questions=num_questions,
                    difficulty=difficulty,
                    question_types=question_types,
                )
            except Exception as exc:
                _set_status(db, job, "failed", error_message=f"AI service error: {exc}")
                return

            if not ai_questions:
                _set_status(db, job, "failed", error_message="AI did not return any valid questions. Please try again.")
                return

            _cache_set(cache_key, ai_questions)

        # Save quiz + questions
        quiz_title = f"{topic.title()} — {difficulty.capitalize()} Quiz"
        time_limit = len(ai_questions) * 60

        new_quiz = Quiz(
            user_id=job.user_id,
            upload_id=None,
            title=quiz_title,
            difficulty=difficulty,
            time_limit=time_limit,
            total_questions=len(ai_questions),
        )
        db.add(new_quiz)
        db.flush()

        for index, q in enumerate(ai_questions):
            db.add(Question(
                quiz_id=new_quiz.id,
                question_text=q["question"],
                type=q.get("type", "mcq"),
                payload=q.get("payload", {}),
                answer_key=q.get("answer_key", {}),
                points=1,
                explanation=q.get("explanation", ""),
                order_index=index,
            ))

        _set_status(db, job, "complete", result_id=new_quiz.id)
        db.commit()
        logger.info("Job %s complete — quiz_id=%s", job_id, new_quiz.id)

    except Exception as exc:
        logger.exception("Unhandled error in topic job %s", job_id)
        try:
            _set_status(db, job, "failed", error_message=f"Unexpected error: {exc}")
        except Exception:
            pass
    finally:
        db.close()


# ─── Worker: flashcards ───────────────────────────────────────────────────────

def run_flashcards_job(
    job_id: str,
    upload_id: int,
    num_cards: int,
) -> None:
    """
    Background worker for POST /api/flashcards/generate.
    Flashcards are not persisted to a DB table — the result JSON is stored
    directly in the GenerationJob.result_data column and returned via the
    status endpoint.
    """
    db = SessionLocal()
    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error("Job %s not found in DB", job_id)
            return

        _set_status(db, job, "processing")

        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if not upload or not upload.extracted_text:
            _set_status(db, job, "failed", error_message="Document not found or has no extractable text.")
            return

        processed = process_text(upload.extracted_text)
        text_chunk = processed["chunks"][0] if processed["chunks"] else upload.extracted_text[:3000]

        # Check cache
        cache_key = _make_key("flash", _text_hash(upload.extracted_text), num_cards)
        cached = _cache_get(cache_key)
        if cached is not None:
            logger.info("Cache HIT for flashcard job %s", job_id)
            cards = cached
        else:
            logger.info("Cache MISS for flashcard job %s — calling Gemini", job_id)
            try:
                cards = generate_flashcards(text_chunk, num_cards=num_cards)
            except Exception as exc:
                _set_status(db, job, "failed", error_message=f"AI service error: {exc}")
                return

            if not cards:
                _set_status(db, job, "failed", error_message="AI could not generate flashcards. Please try again.")
                return

            _cache_set(cache_key, cards)

        # Store cards + upload info as JSON in result_data
        result_payload = json.dumps({
            "upload_id": upload_id,
            "filename":  upload.filename,
            "cards":     cards,
        })
        _set_status(db, job, "complete", result_data=result_payload)
        logger.info("Job %s complete — %d flashcards", job_id, len(cards))

    except Exception as exc:
        logger.exception("Unhandled error in flashcard job %s", job_id)
        try:
            _set_status(db, job, "failed", error_message=f"Unexpected error: {exc}")
        except Exception:
            pass
    finally:
        db.close()
