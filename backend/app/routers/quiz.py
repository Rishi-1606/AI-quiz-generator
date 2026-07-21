from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

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
from app.services.ai_service import generate_questions_from_chunk, generate_feedback

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])

# ─── Request schema ──────────────────────────────────────────────────────────

class GenerateQuizRequest(BaseModel):
    upload_id: int
    num_questions: int = 5         # default 5 questions
    difficulty: str = "medium"     # easy | medium | hard


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

    # Save Questions
    for index, q in enumerate(ai_questions):
        question = Question(
            quiz_id=new_quiz.id,
            question_text=q["question"],
            options=q["options"],
            correct_option=q["correct_option"],
            explanation=q.get("explanation", ""),
            order_index=index,
        )
        db.add(question)

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

    # 3. Grade: compare user answers against correct_option
    correct_count = 0
    wrong_count   = 0
    skipped_count = 0

    for question in questions:
        q_id_str = str(question.id)
        user_choice = body.answers.get(q_id_str)  # int or None

        if user_choice is None:
            skipped_count += 1
        elif user_choice == question.correct_option:
            correct_count += 1
        else:
            wrong_count += 1

    total = len(questions)
    percentage = round((correct_count / total) * 100, 2) if total > 0 else 0.0

    # 4. Generate AI feedback on wrong answers
    wrong_q_data = []
    for question in questions:
        q_id_str    = str(question.id)
        user_choice = body.answers.get(q_id_str)
        if user_choice is not None and user_choice != question.correct_option:
            wrong_q_data.append({
                "question_text":  question.question_text,
                "options":        question.options,
                "correct_option": question.correct_option,
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
