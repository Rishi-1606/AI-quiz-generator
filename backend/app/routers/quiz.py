from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import json

from app.database import get_db
from app.models.user import User
from app.models.upload import Upload
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.attempt import Attempt
from app.models.generation_job import GenerationJob
from app.schemas.quiz import (
    QuizResponse, 
    QuizSummaryResponse,
    QuizWithAnswersResponse
)
from app.schemas.attempt import SubmitQuizRequest, AttemptResponse
from app.middleware.auth import get_current_user
from app.services.text_processor import process_text
from app.services.ai_service import generate_questions_from_chunk, generate_feedback, generate_questions_from_topic
from app.services.grading_service import grade_question
from app.services.job_service import run_quiz_from_doc_job, run_quiz_from_topic_job
from app.limiter import limiter

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])

# ─── Request schemas ────────────────────────────────────────────────────────

class GenerateQuizRequest(BaseModel):
    upload_id: int
    num_questions: int = 5
    difficulty: str = "medium"
    question_types: list[str] = ["mcq"]  # Sprint 4: multi-format support


class GenerateTopicQuizRequest(BaseModel):
    topic: str
    num_questions: int = 5
    difficulty: str = "medium"
    question_types: list[str] = ["mcq"]  # Sprint 4: multi-format support


# ─── Generate quiz ───────────────────────────────────────────────────────────

@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/hour")
def generate_quiz(
    request: Request,
    body: GenerateQuizRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enqueue a background quiz-generation job and return immediately.
    Poll GET /api/quizzes/jobs/{job_id}/status to track progress.
    """
    # Validate inputs before queueing so the user gets fast feedback on bad requests.
    upload = (
        db.query(Upload)
        .filter(Upload.id == body.upload_id, Upload.user_id == current_user.id)
        .first()
    )
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or does not belong to you.",
        )
    if not upload.extracted_text or not upload.extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text could be extracted from this document. Cannot generate a quiz.",
        )
    if body.difficulty not in ("easy", "medium", "hard"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid difficulty. Must be 'easy', 'medium', or 'hard'.",
        )

    # Create the job row
    job = GenerationJob(
        user_id=current_user.id,
        job_type="quiz_from_doc",
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue background worker
    background_tasks.add_task(
        run_quiz_from_doc_job,
        job_id=job.id,
        upload_id=body.upload_id,
        num_questions=max(1, min(body.num_questions, 15)),
        difficulty=body.difficulty,
        question_types=body.question_types,
    )

    return {"job_id": job.id, "status": "pending"}


# ─── Generate quiz from topic ─────────────────────────────────────────────────

@router.post("/generate-from-topic", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/hour")
def generate_quiz_from_topic(
    request: Request,
    body: GenerateTopicQuizRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enqueue a topic-based quiz generation job and return immediately."""
    topic = body.topic.strip()
    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic cannot be empty.")

    job = GenerationJob(
        user_id=current_user.id,
        job_type="quiz_from_topic",
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_quiz_from_topic_job,
        job_id=job.id,
        topic=topic,
        num_questions=max(1, min(body.num_questions, 15)),
        difficulty=body.difficulty,
        question_types=body.question_types,
    )

    return {"job_id": job.id, "status": "pending"}


# ─── Job status (quiz jobs) ───────────────────────────────────────────────────

@router.get("/jobs/{job_id}/status")
def get_quiz_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Poll the status of a quiz generation job.
    Returns: { job_id, status, result_id, error_message }
      - status: "pending" | "processing" | "complete" | "failed"
      - result_id: quiz ID (only when status=="complete")
      - error_message: set when status=="failed"
    """
    job = (
        db.query(GenerationJob)
        .filter(
            GenerationJob.id == job_id,
            GenerationJob.user_id == current_user.id,
            GenerationJob.job_type.in_(["quiz_from_doc", "quiz_from_topic"]),
        )
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    return {
        "job_id":        job.id,
        "status":        job.status,
        "result_id":     job.result_id,
        "error_message": job.error_message,
    }


# ─── List quizzes ─────────────────────────────────────────────────────────────

@router.get("", response_model=List[QuizSummaryResponse])
def get_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all quizzes created by the current user (no questions, for list views)."""
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == current_user.id)
        .order_by(Quiz.created_at.desc())
        .all()
    )
    return quizzes


# ─── Delete quiz ──────────────────────────────────────────────────────────────

@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a quiz (and all its questions/attempts via cascade)."""
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")
    db.delete(quiz)
    db.commit()


# ─── Submit quiz ─────────────────────────────────────────────────────────────

@router.post("/{quiz_id}/submit", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
def submit_quiz(
    quiz_id: int,
    body: SubmitQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grade a submitted quiz attempt.

    Steps:
      1. Fetch the quiz and verify ownership.
      2. Load all questions for this quiz.
      3. Compare user answers to correct answers — count correct/wrong/skipped.
      4. Compute percentage score.
      5. Save the Attempt record.
      6. Return the AttemptResponse.
    """
    # 1. Fetch quiz
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found.",
        )

    # 2. Load questions
    questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.order_index)
        .all()
    )
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This quiz has no questions.",
        )

    # 3. Grade: dispatch by question type via grading_service
    correct_count  = 0
    wrong_count    = 0
    skipped_count  = 0
    points_earned  = 0
    points_total   = sum(q.points for q in questions)
    question_results: dict[str, bool | None] = {}  # {question_id_str: True/False/None}

    for question in questions:
        q_id_str    = str(question.id)
        user_answer = body.answers.get(q_id_str)  # Any type or None

        if user_answer is None:
            skipped_count += 1
            question_results[q_id_str] = None   # skipped
        else:
            result = grade_question(question, user_answer)
            question_results[q_id_str] = result.correct
            if result.correct:
                correct_count += 1
                points_earned += result.points_earned
            else:
                wrong_count += 1

    total      = len(questions)
    percentage = round((correct_count / total) * 100, 2) if total > 0 else 0.0

    # 4. Generate AI feedback on wrong answers
    wrong_q_data = []
    for question in questions:
        q_id_str    = str(question.id)
        user_answer = body.answers.get(q_id_str)
        if user_answer is not None:
            result = grade_question(question, user_answer)
            if not result.correct:
                wrong_q_data.append({
                    "question_text": question.question_text,
                    "answer_key":    question.answer_key,
                    "payload":       question.payload,
                    "explanation":   question.explanation or "",
                })

    ai_feedback = generate_feedback(
        wrong_questions=wrong_q_data,
        correct_count=correct_count,
        total=total,
        difficulty=quiz.difficulty,
    )

    # 5. Save Attempt
    attempt = Attempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=correct_count,
        total=total,
        correct=correct_count,
        wrong=wrong_count,
        skipped=skipped_count,
        percentage=percentage,
        answers=body.answers,
        time_taken=body.time_taken,
        ai_feedback=ai_feedback,
        question_results=question_results,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # Attach computed fields not stored as DB columns
    attempt.points_earned = points_earned
    attempt.points_total  = points_total

    return attempt


# ─── Get single quiz ──────────────────────────────────────────────────────────

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single quiz with all its questions."""
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found.",
        )
    return quiz


@router.get("/{quiz_id}/with-answers", response_model=QuizWithAnswersResponse)
def get_quiz_with_answers(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single quiz with all its questions AND their answer keys. Used for Results page."""
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found.",
        )
    return quiz


# ─── Export helpers (type-aware) ─────────────────────────────────────────────

def _parse_json_field(value):
    """Safely parse a JSON column that may already be a dict or a JSON string."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


OPTION_LETTERS = ["A", "B", "C", "D"]


def _format_question_txt(i: int, q, include_answers: bool) -> list:
    """
    Return a list of text lines for question i of any question type.
    Used for the per-question body in TXT export.
    """
    q_type  = getattr(q, "type", "mcq") or "mcq"
    payload = _parse_json_field(q.payload)
    ak      = _parse_json_field(q.answer_key)
    lines   = []

    lines.append(f"Q{i}. [{q_type.upper()}] {q.question_text}")

    if q_type == "mcq":
        opts = payload.get("options") or []
        for j, opt in enumerate(opts):
            lines.append(f"    {OPTION_LETTERS[j]}) {opt}")
        if include_answers:
            idx = ak.get("correct_index", 0)
            lines.append(f"    ✔ Answer: {OPTION_LETTERS[idx]}")
            if q.explanation:
                lines.append(f"    💬 {q.explanation}")

    elif q_type == "true_false":
        if include_answers:
            correct = ak.get("correct")
            val = "True" if correct else "False"
            lines.append(f"    ✔ Answer: {val}")
            if q.explanation:
                lines.append(f"    💬 {q.explanation}")

    elif q_type == "fill_blank":
        prompt = payload.get("text_with_blanks") or q.question_text
        if prompt != q.question_text:
            lines.append(f"    Fill in: {prompt}")
        if include_answers:
            accepted = ak.get("accepted_answers", [])
            lines.append(f"    ✔ Accepted: {' / '.join(accepted)}")
            if q.explanation:
                lines.append(f"    💬 {q.explanation}")

    elif q_type == "short_answer":
        if include_answers:
            ref = ak.get("reference_answer", "")
            lines.append(f"    ✔ Reference Answer: {ref}")
            if q.explanation:
                lines.append(f"    💬 {q.explanation}")

    elif q_type == "matching":
        left  = payload.get("left", [])
        right = payload.get("right", [])
        lines.append("    Left items:")
        for j, item in enumerate(left, 1):
            lines.append(f"      {j}. {item}")
        lines.append("    Right items:")
        for j, item in enumerate(right):
            lines.append(f"      {OPTION_LETTERS[j]}. {item}")
        if include_answers:
            pairs = ak.get("pairs", [])
            pair_strs = [f"{p[0]+1}→{OPTION_LETTERS[p[1]]}" for p in pairs if len(p) == 2]
            lines.append(f"    ✔ Pairs: {', '.join(pair_strs)}")
            if q.explanation:
                lines.append(f"    💬 {q.explanation}")

    elif q_type == "ordering":
        items = payload.get("items", [])
        lines.append("    Arrange in correct order:")
        for j, item in enumerate(items, 1):
            lines.append(f"      {j}. {item}")
        if include_answers:
            correct_order = ak.get("correct_order", [])
            order_strs = [str(idx + 1) for idx in correct_order]
            lines.append(f"    ✔ Correct order: {', '.join(order_strs)}")
            if q.explanation:
                lines.append(f"    💬 {q.explanation}")

    elif q_type == "numeric":
        unit = payload.get("unit") or ""
        if unit:
            lines.append(f"    Enter a numeric value in {unit}:")
        if include_answers:
            value     = ak.get("value", "")
            tolerance = ak.get("tolerance")
            tol_str   = f"  (±{tolerance} {unit})".rstrip() if tolerance else ""
            lines.append(f"    ✔ Answer: {value}{tol_str}")
            if q.explanation:
                lines.append(f"    💬 {q.explanation}")

    lines.append("")
    return lines


def _format_answer_key_line(i: int, q) -> list:
    """
    Return a compact answer-key line for question i (used in the answer-key
    block at the bottom of a TXT export when include_answers=False).
    """
    q_type  = getattr(q, "type", "mcq") or "mcq"
    payload = _parse_json_field(q.payload)
    ak      = _parse_json_field(q.answer_key)

    if q_type == "mcq":
        idx = ak.get("correct_index", 0)
        return [f"Q{i}: {OPTION_LETTERS[idx]}"]

    if q_type == "true_false":
        correct = ak.get("correct")
        return [f"Q{i}: {'True' if correct else 'False'}"]

    if q_type == "fill_blank":
        accepted = ak.get("accepted_answers", [])
        return [f"Q{i}: {' / '.join(accepted)}"]

    if q_type == "short_answer":
        ref = ak.get("reference_answer", "")
        return [f"Q{i}: {ref}"]

    if q_type == "matching":
        pairs = ak.get("pairs", [])
        pair_strs = [f"{p[0]+1}→{OPTION_LETTERS[p[1]]}" for p in pairs if len(p) == 2]
        return [f"Q{i}: {', '.join(pair_strs)}"]

    if q_type == "ordering":
        correct_order = ak.get("correct_order", [])
        order_strs = [str(idx + 1) for idx in correct_order]
        return [f"Q{i}: {', '.join(order_strs)}"]

    if q_type == "numeric":
        value = ak.get("value", "")
        unit  = payload.get("unit") or ""
        return [f"Q{i}: {value}{(' ' + unit) if unit else ''}"]

    return [f"Q{i}: (see question)"]


def _format_question_json(q, include_answers: bool) -> dict:
    """
    Return a structured dict for a question of any type.
    Uses the canonical payload / answer_key JSON columns.
    """
    q_type  = getattr(q, "type", "mcq") or "mcq"
    payload = _parse_json_field(q.payload)
    ak      = _parse_json_field(q.answer_key)

    # For MCQ, ensure payload always has options (with legacy fallback)
    if q_type == "mcq" and "options" not in payload:
        payload = {"options": q.options or []}

    result = {
        "type":        q_type,
        "question":    q.question_text,
        "payload":     payload,
        "explanation": q.explanation or "",
    }
    if include_answers:
        result["answer_key"] = ak
    return result


# ─── Export quiz ──────────────────────────────────────────────────────────────

@router.get("/{quiz_id}/export")
def export_quiz(
    quiz_id: int,
    format: str = Query(default="txt", enum=["txt", "json"]),
    include_answers: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export a quiz as a downloadable file.
    - format: 'txt' (human-readable) or 'json' (structured data)
    - include_answers: whether to include correct options and explanations
    """
    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
        .first()
    )
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

    questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.order_index)
        .all()
    )

    safe_title = quiz.title.replace("—", "-").replace(" ", "_")[:50]

    # ── JSON export ────────────────────────────────────────────────────────────
    if format == "json":
        data = {
            "title":      quiz.title,
            "difficulty": quiz.difficulty,
            "questions":  [_format_question_json(q, include_answers) for q in questions],
        }
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.json"'},
        )

    # ── TXT export ─────────────────────────────────────────────────────────────
    lines = []
    lines.append(f"{quiz.title}")
    lines.append(f"Difficulty: {quiz.difficulty.capitalize()}  |  Questions: {len(questions)}")
    lines.append("=" * 60)
    lines.append("")

    for i, q in enumerate(questions, 1):
        lines.extend(_format_question_txt(i, q, include_answers))

    if not include_answers:
        lines.append("=" * 60)
        lines.append("Answer Key")
        lines.append("=" * 60)
        for i, q in enumerate(questions, 1):
            lines.extend(_format_answer_key_line(i, q))

    content = "\n".join(lines)
    return Response(
        content=content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.txt"'},
    )


# ─── E2E test seed (TEST_MODE=1 only) ─────────────────────────────────────────

@router.post("/seed-test-quiz", status_code=201, response_model=QuizResponse)
def seed_test_quiz(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a quiz with 2 hardcoded MCQ questions — NO Gemini call.
    Only available when the environment variable TEST_MODE=1.
    Used exclusively by Playwright E2E tests.
    """
    import os
    if os.getenv("TEST_MODE") != "1":
        raise HTTPException(status_code=404, detail="Not found.")

    quiz = Quiz(
        user_id=current_user.id,
        title="E2E Test Quiz",
        difficulty="easy",
        time_limit=300,
        total_questions=2,
    )
    db.add(quiz)
    db.flush()

    hardcoded_questions = [
        {
            "question": "What is 2 + 2?",
            "type": "mcq",
            "payload": {"options": ["1", "2", "3", "4"]},
            "answer_key": {"correct_index": 3},   # "4" is correct
            "explanation": "2 + 2 equals 4.",
        },
        {
            "question": "What is the capital of France?",
            "type": "mcq",
            "payload": {"options": ["Berlin", "Madrid", "Paris", "Rome"]},
            "answer_key": {"correct_index": 2},   # "Paris" is correct
            "explanation": "Paris is the capital of France.",
        },
    ]

    for i, q in enumerate(hardcoded_questions):
        db.add(Question(
            quiz_id=quiz.id,
            question_text=q["question"],
            type=q["type"],
            payload=q["payload"],
            answer_key=q["answer_key"],
            explanation=q["explanation"],
            points=1,
            order_index=i,
        ))

    db.commit()
    db.refresh(quiz)
    return quiz
