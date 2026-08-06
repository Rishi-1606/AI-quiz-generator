from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from app.schemas.quiz import QuizResponse, QuizSummaryResponse
from app.schemas.attempt import SubmitQuizRequest, AttemptResponse
from app.middleware.auth import get_current_user
from app.services.text_processor import process_text
from app.services.ai_service import generate_questions_from_chunk, generate_feedback, generate_questions_from_topic
from app.services.grading_service import grade_question

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

@router.post("/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    body: GenerateQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full pipeline:
      1. Fetch upload + verify ownership
      2. Clean & chunk the extracted text
      3. Send first chunk to Gemini AI
      4. Save Quiz + Questions to database
      5. Return quiz with all questions
    """
    # 1. Fetch the upload and verify it belongs to the current user
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

    # Validate difficulty
    if body.difficulty not in ("easy", "medium", "hard"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid difficulty. Must be 'easy', 'medium', or 'hard'.",
        )

    # Clamp num_questions
    num_questions = max(1, min(body.num_questions, 15))

    # 2. Clean and chunk the extracted text
    processed = process_text(upload.extracted_text)

    if not processed["chunks"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document text is too short to generate a quiz.",
        )

    # Use only the first chunk (largest context window used efficiently)
    text_chunk = processed["chunks"][0]

    # 3. Call Gemini AI
    try:
        ai_questions = generate_questions_from_chunk(
            text=text_chunk,
            num_questions=num_questions,
            difficulty=body.difficulty,
            question_types=body.question_types,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI returned invalid response: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )

    if not ai_questions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI did not return any valid questions. Please try again.",
        )

    # 4. Save Quiz to database
    # Title: "<filename> — <difficulty> quiz"
    display_name = upload.filename.rsplit(".", 1)[0]  # strip extension
    quiz_title = f"{display_name} — {body.difficulty.capitalize()} Quiz"

    # Time limit: 1 min per question (60s × num_questions)
    time_limit = len(ai_questions) * 60

    new_quiz = Quiz(
        user_id=current_user.id,
        upload_id=upload.id,
        title=quiz_title,
        difficulty=body.difficulty,
        time_limit=time_limit,
        total_questions=len(ai_questions),
    )
    db.add(new_quiz)
    db.flush()  # flush to get new_quiz.id before adding questions

    # Save Questions — dual-write: old columns + new generalized columns
    for index, q in enumerate(ai_questions):
        question = Question(
            quiz_id=new_quiz.id,
            question_text=q["question"],
            # ── DEPRECATED (kept for backward compat until Sprint 12) ──
            options=q.get("options", []),
            correct_option=q.get("correct_option", 0),
            # ── New generalized fields (Sprint 1) ─────────────────────
            type=q.get("type", "mcq"),
            payload=q.get("payload", {}),
            answer_key=q.get("answer_key", {}),
            points=1,
            explanation=q.get("explanation", ""),
            order_index=index,
        )
        db.add(question)

    db.commit()
    db.refresh(new_quiz)

    return new_quiz


# ─── Generate quiz from topic ─────────────────────────────────────────────────

@router.post("/generate-from-topic", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz_from_topic(
    body: GenerateTopicQuizRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a quiz from a free-text topic using Gemini's general knowledge."""
    topic = body.topic.strip()
    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic cannot be empty.")

    try:
        ai_questions = generate_questions_from_topic(
            topic=topic,
            num_questions=body.num_questions,
            difficulty=body.difficulty,
            question_types=body.question_types,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"AI service error: {str(e)}")

    if not ai_questions:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI did not return any valid questions. Please try again.")

    quiz_title = f"{topic.title()} — {body.difficulty.capitalize()} Quiz"
    time_limit = len(ai_questions) * 60

    new_quiz = Quiz(
        user_id=current_user.id,
        upload_id=None,
        title=quiz_title,
        difficulty=body.difficulty,
        time_limit=time_limit,
        total_questions=len(ai_questions),
    )
    db.add(new_quiz)
    db.flush()

    # Save Questions — dual-write: old columns + new generalized columns
    for index, q in enumerate(ai_questions):
        db.add(Question(
            quiz_id=new_quiz.id,
            question_text=q["question"],
            # ── DEPRECATED (kept for backward compat until Sprint 12) ──
            options=q.get("options", []),
            correct_option=q.get("correct_option", 0),
            # ── New generalized fields (Sprint 1) ─────────────────────
            type=q.get("type", "mcq"),
            payload=q.get("payload", {}),
            answer_key=q.get("answer_key", {}),
            points=1,
            explanation=q.get("explanation", ""),
            order_index=index,
        ))

    db.commit()
    db.refresh(new_quiz)
    return new_quiz


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

    for question in questions:
        q_id_str    = str(question.id)
        user_answer = body.answers.get(q_id_str)  # Any type or None

        if user_answer is None:
            skipped_count += 1
        else:
            result = grade_question(question, user_answer)
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
        # Only MCQ questions feed into the AI feedback generator (for now)
        if question.type == "mcq" and user_answer is not None:
            result = grade_question(question, user_answer)
            if not result.correct:
                # Build feedback payload using new answer_key with legacy fallback
                import json as _json
                ak = question.answer_key if isinstance(question.answer_key, dict) else (_json.loads(question.answer_key) if question.answer_key else {})
                correct_idx = ak.get("correct_index", question.correct_option)
                wrong_q_data.append({
                    "question_text":  question.question_text,
                    "options":        question.options or [],
                    "correct_option": correct_idx,
                    "explanation":    question.explanation or "",
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
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

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

    option_letters = ["A", "B", "C", "D"]
    safe_title = quiz.title.replace("—", "-").replace(" ", "_")[:50]

    # ── JSON export ────────────────────────────────────────────────────────────
    if format == "json":
        data = {
            "title":      quiz.title,
            "difficulty": quiz.difficulty,
            "questions": [
                {
                    "question": q.question_text,
                    "options":  q.options,
                    **(
                        {
                            "correct_option": q.correct_option,
                            "correct_answer": q.options[q.correct_option] if q.options else "",
                            "explanation":    q.explanation,
                        } if include_answers else {}
                    ),
                }
                for q in questions
            ],
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
        lines.append(f"Q{i}. {q.question_text}")
        for j, opt in enumerate(q.options):
            lines.append(f"    {option_letters[j]}) {opt}")
        if include_answers:
            correct_letter = option_letters[q.correct_option]
            lines.append(f"    ✔ Answer: {correct_letter}")
            if q.explanation:
                lines.append(f"    💬 {q.explanation}")
        lines.append("")

    if not include_answers:
        lines.append("=" * 60)
        lines.append("Answer Key")
        lines.append("=" * 60)
        for i, q in enumerate(questions, 1):
            lines.append(f"Q{i}: {option_letters[q.correct_option]}")

    content = "\n".join(lines)
    return Response(
        content=content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.txt"'},
    )
