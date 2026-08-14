"""
Sprint 10 tests: async generation endpoints, worker logic, in-memory cache, rate limiting.

All Gemini calls are mocked at the job_service layer (not the ai_service layer).
Mock targets: app.services.job_service.generate_questions_from_chunk
              app.services.job_service.generate_questions_from_topic
              app.services.job_service.generate_flashcards

Worker tests call the worker functions DIRECTLY (not via HTTP) and patch
`app.services.job_service.SessionLocal` so workers use the test in-memory
DB rather than the real SQLite file.
"""

import json
import pytest
from unittest.mock import MagicMock, patch


# ─── Shared mock AI payload ────────────────────────────────────────────────────

MCQ_QUESTION = {
    "type":        "mcq",
    "question":    "What is 2 + 2?",
    "payload":     {"options": ["1", "2", "3", "4"]},
    "answer_key":  {"correct_index": 3},
    "explanation": "2 + 2 = 4.",
}

FLASHCARD = {"front": "Photosynthesis", "back": "Process by which plants convert sunlight to energy."}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _mock_ai_in_worker(mocker, questions=None, flashcards=None):
    """Patch the three AI functions as imported inside job_service."""
    mocker.patch("app.services.job_service.generate_questions_from_chunk",
                 return_value=questions or [MCQ_QUESTION])
    mocker.patch("app.services.job_service.generate_questions_from_topic",
                 return_value=questions or [MCQ_QUESTION])
    mocker.patch("app.services.job_service.generate_flashcards",
                 return_value=flashcards or [FLASHCARD])


def _make_worker_session(test_db):
    """
    Wrap test_db in a MagicMock so the worker's SessionLocal() returns it
    but calling close() on it doesn't actually close the test session.
    """
    mock_session = MagicMock(wraps=test_db)
    mock_session.close = MagicMock()  # no-op: keeps test_db alive
    return mock_session


# ─── Per-test fixture: an upload row in the test DB ───────────────────────────

@pytest.fixture()
def test_upload(test_db, client, auth_headers):
    """
    Insert an Upload row directly into the test DB.
    Returns the upload ID.
    Depends on `auth_headers` to ensure the test user exists in the DB first.
    """
    from app.models.user import User
    from app.models.upload import Upload

    user = test_db.query(User).filter(User.email == "testuser@example.com").first()
    upload = Upload(
        user_id=user.id,
        filename="study_doc.pdf",
        file_type="pdf",
        file_size=2048,
        storage_path="test_uploads/study_doc.pdf",
        extracted_text="Photosynthesis is the process plants use to make food. " * 60,
    )
    test_db.add(upload)
    test_db.commit()
    test_db.refresh(upload)
    return upload.id


# ─── Endpoint: immediate 202 + job_id ─────────────────────────────────────────

def test_generate_quiz_returns_202_with_job_id(client, auth_headers, test_upload):
    """POST /generate returns 202 and a job_id immediately — no blocking Gemini call."""
    with patch("app.routers.quiz.run_quiz_from_doc_job"):
        resp = client.post("/api/quizzes/generate", headers=auth_headers, json={
            "upload_id":      test_upload,
            "num_questions":  1,
            "difficulty":     "easy",
            "question_types": ["mcq"],
        })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"


def test_generate_from_topic_returns_202_with_job_id(client, auth_headers):
    """POST /generate-from-topic returns 202 and a job_id immediately."""
    with patch("app.routers.quiz.run_quiz_from_topic_job"):
        resp = client.post("/api/quizzes/generate-from-topic", headers=auth_headers, json={
            "topic":          "Photosynthesis",
            "num_questions":  1,
            "difficulty":     "easy",
            "question_types": ["mcq"],
        })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"


def test_flashcards_generate_returns_202_with_job_id(client, auth_headers, test_upload):
    """POST /flashcards/generate returns 202 and a job_id immediately."""
    with patch("app.routers.flashcards.run_flashcards_job"):
        resp = client.post("/api/flashcards/generate", headers=auth_headers, json={
            "upload_id": test_upload,
            "num_cards": 5,
        })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"


# ─── Status endpoint ──────────────────────────────────────────────────────────

def test_quiz_job_status_returns_pending(client, auth_headers, test_upload):
    """Status endpoint immediately returns 'pending' after job creation."""
    with patch("app.routers.quiz.run_quiz_from_doc_job"):
        resp = client.post("/api/quizzes/generate", headers=auth_headers, json={
            "upload_id": test_upload, "num_questions": 1,
            "difficulty": "easy", "question_types": ["mcq"],
        })
    job_id = resp.json()["job_id"]

    status_resp = client.get(f"/api/quizzes/jobs/{job_id}/status", headers=auth_headers)
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "pending"
    assert data["result_id"] is None
    assert data["error_message"] is None


def test_quiz_job_not_found_for_other_user(client, auth_headers, auth_headers_b, test_upload):
    """User B gets 404 when polling User A's job — ownership enforced."""
    with patch("app.routers.quiz.run_quiz_from_doc_job"):
        resp = client.post("/api/quizzes/generate", headers=auth_headers, json={
            "upload_id": test_upload, "num_questions": 1,
            "difficulty": "easy", "question_types": ["mcq"],
        })
    job_id = resp.json()["job_id"]

    resp_b = client.get(f"/api/quizzes/jobs/{job_id}/status", headers=auth_headers_b)
    assert resp_b.status_code == 404


# ─── Worker: quiz from document ───────────────────────────────────────────────

def test_worker_completes_quiz_from_doc(test_db, mocker, client, auth_headers, test_upload):
    """
    Worker for doc-based quiz transitions job to 'complete' and
    creates a Quiz + Questions row in the DB.
    """
    from app.models.user import User
    from app.models.generation_job import GenerationJob
    from app.models.quiz import Quiz
    from app.services.job_service import run_quiz_from_doc_job, _cache

    _cache.clear()
    _mock_ai_in_worker(mocker)

    user = test_db.query(User).filter(User.email == "testuser@example.com").first()
    job = GenerationJob(user_id=user.id, job_type="quiz_from_doc", status="pending")
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    mock_session = _make_worker_session(test_db)
    with patch("app.services.job_service.SessionLocal", return_value=mock_session):
        run_quiz_from_doc_job(
            job_id=job.id,
            upload_id=test_upload,
            num_questions=1,
            difficulty="easy",
            question_types=["mcq"],
        )

    test_db.refresh(job)
    assert job.status == "complete"
    assert job.result_id is not None

    quiz = test_db.query(Quiz).filter(Quiz.id == job.result_id).first()
    assert quiz is not None
    assert quiz.difficulty == "easy"
    assert quiz.total_questions == 1


def test_worker_completes_quiz_from_topic(test_db, mocker, client, auth_headers):
    """Worker for topic-based quiz completes and saves quiz to DB."""
    from app.models.user import User
    from app.models.generation_job import GenerationJob
    from app.models.quiz import Quiz
    from app.services.job_service import run_quiz_from_topic_job, _cache

    _cache.clear()
    _mock_ai_in_worker(mocker)

    user = test_db.query(User).filter(User.email == "testuser@example.com").first()
    job = GenerationJob(user_id=user.id, job_type="quiz_from_topic", status="pending")
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    mock_session = _make_worker_session(test_db)
    with patch("app.services.job_service.SessionLocal", return_value=mock_session):
        run_quiz_from_topic_job(
            job_id=job.id,
            topic="Photosynthesis",
            num_questions=1,
            difficulty="medium",
            question_types=["mcq"],
        )

    test_db.refresh(job)
    assert job.status == "complete"
    assert job.result_id is not None

    quiz = test_db.query(Quiz).filter(Quiz.id == job.result_id).first()
    assert "Photosynthesis" in quiz.title


def test_worker_completes_flashcard_job(test_db, mocker, client, auth_headers, test_upload):
    """Worker for flashcards stores result_data JSON and sets status to 'complete'."""
    from app.models.user import User
    from app.models.generation_job import GenerationJob
    from app.services.job_service import run_flashcards_job, _cache

    _cache.clear()
    _mock_ai_in_worker(mocker)

    user = test_db.query(User).filter(User.email == "testuser@example.com").first()
    job = GenerationJob(user_id=user.id, job_type="flashcards", status="pending")
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    mock_session = _make_worker_session(test_db)
    with patch("app.services.job_service.SessionLocal", return_value=mock_session):
        run_flashcards_job(job_id=job.id, upload_id=test_upload, num_cards=5)

    test_db.refresh(job)
    assert job.status == "complete"
    assert job.result_data is not None

    result = json.loads(job.result_data)
    assert "cards" in result
    assert len(result["cards"]) > 0


# ─── Worker: failure handling ─────────────────────────────────────────────────

def test_worker_fails_on_gemini_error(test_db, mocker, client, auth_headers, test_upload):
    """When Gemini raises an exception the job ends in 'failed' with an error_message."""
    from app.models.user import User
    from app.models.generation_job import GenerationJob
    from app.services.job_service import run_quiz_from_doc_job, _cache

    _cache.clear()
    mocker.patch(
        "app.services.job_service.generate_questions_from_chunk",
        side_effect=RuntimeError("Gemini API timeout"),
    )

    user = test_db.query(User).filter(User.email == "testuser@example.com").first()
    job = GenerationJob(user_id=user.id, job_type="quiz_from_doc", status="pending")
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    mock_session = _make_worker_session(test_db)
    with patch("app.services.job_service.SessionLocal", return_value=mock_session):
        run_quiz_from_doc_job(
            job_id=job.id,
            upload_id=test_upload,
            num_questions=1,
            difficulty="easy",
            question_types=["mcq"],
        )

    test_db.refresh(job)
    assert job.status == "failed"
    assert job.error_message is not None
    assert "Gemini API timeout" in job.error_message


# ─── Cache ────────────────────────────────────────────────────────────────────

def test_cache_hit_skips_gemini_call(test_db, mocker, client, auth_headers, test_upload):
    """
    Running the same doc+settings twice calls Gemini only once.
    The second run should hit the in-memory cache and skip the API call.
    """
    from app.models.user import User
    from app.models.generation_job import GenerationJob
    from app.services.job_service import run_quiz_from_doc_job, _cache

    _cache.clear()

    mock_gemini = mocker.patch(
        "app.services.job_service.generate_questions_from_chunk",
        return_value=[MCQ_QUESTION],
    )

    user = test_db.query(User).filter(User.email == "testuser@example.com").first()
    mock_session = _make_worker_session(test_db)

    def _create_and_run():
        job = GenerationJob(user_id=user.id, job_type="quiz_from_doc", status="pending")
        test_db.add(job)
        test_db.commit()
        test_db.refresh(job)
        with patch("app.services.job_service.SessionLocal", return_value=mock_session):
            run_quiz_from_doc_job(
                job_id=job.id,
                upload_id=test_upload,
                num_questions=1,
                difficulty="easy",
                question_types=["mcq"],
            )
        test_db.refresh(job)
        return job

    job1 = _create_and_run()
    job2 = _create_and_run()  # identical inputs — should hit cache

    assert mock_gemini.call_count == 1, "Gemini should be called only once; second run should use cache"
    assert job1.status == "complete"
    assert job2.status == "complete"


# ─── Rate limiting ────────────────────────────────────────────────────────────

def test_rate_limit_returns_429_after_10_requests(client):
    """
    The 11th AI generation request within one hour returns 429.
    Uses a unique user so this test's bucket is isolated from the rest of the suite.
    """
    # Sign up a unique user just for this test (fresh rate limit bucket)
    resp = client.post("/api/auth/signup", json={
        "name":     "Rate Limit Tester",
        "email":    "rate_limit_isolated@test.com",
        "password": "password123",
        "role":     "student",
    })
    assert resp.status_code == 201
    token   = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Make 10 successful requests (mocking the worker to avoid real work)
    with patch("app.routers.quiz.run_quiz_from_topic_job"):
        for i in range(10):
            r = client.post("/api/quizzes/generate-from-topic", headers=headers, json={
                "topic": "Biology", "num_questions": 1,
                "difficulty": "easy", "question_types": ["mcq"],
            })
            assert r.status_code == 202, (
                f"Request {i + 1} should be 202 but got {r.status_code}: {r.text}"
            )

        # 11th request must be blocked
        r = client.post("/api/quizzes/generate-from-topic", headers=headers, json={
            "topic": "Biology", "num_questions": 1,
            "difficulty": "easy", "question_types": ["mcq"],
        })

    assert r.status_code == 429, f"Expected 429 but got {r.status_code}: {r.text}"
