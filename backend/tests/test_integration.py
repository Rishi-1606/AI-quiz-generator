"""
Sprint 7 - Step 4: Integration tests for the core quiz flow.

Uses FastAPI TestClient + in-memory SQLite DB from conftest.py fixtures.

Sprint 10 update: quiz generation endpoints are now async (return 202 + job_id).
Tests that need an existing quiz use `_direct_quiz` to insert directly into the
test DB instead of going through the generation API.

Mock target for feedback: app.routers.quiz.generate_feedback
"""

import json
import pytest
from unittest.mock import patch

from app.models.quiz import Quiz
from app.models.question import Question


# ---------------------------------------------------------------------------
# Shared mock question payloads
# ---------------------------------------------------------------------------

MCQ_QUESTION = {
    "type":           "mcq",
    "question":       "What is 2 + 2?",
    "options":        ["1", "2", "3", "4"],
    "correct_option": 3,
    "explanation":    "2 + 2 = 4.",
    "payload":        {"options": ["1", "2", "3", "4"]},
    "answer_key":     {"correct_index": 3},
}

TRUE_FALSE_QUESTION = {
    "type":           "true_false",
    "question":       "The sky is blue.",
    "options":        ["True", "False"],
    "correct_option": 0,
    "explanation":    "Rayleigh scattering makes the sky appear blue.",
    "payload":        {},
    "answer_key":     {"correct": True},
}

TWO_MCQ = [
    {
        "type": "mcq", "question": "Q1?",
        "options": ["A","B","C","D"], "correct_option": 0,
        "explanation": "A is correct.",
        "payload": {"options": ["A","B","C","D"]},
        "answer_key": {"correct_index": 0},
    },
    {
        "type": "mcq", "question": "Q2?",
        "options": ["W","X","Y","Z"], "correct_option": 2,
        "explanation": "Y is correct.",
        "payload": {"options": ["W","X","Y","Z"]},
        "answer_key": {"correct_index": 2},
    },
]


# ---------------------------------------------------------------------------
# Sprint 10: direct DB insertion helper (replaces the old _generate_quiz
# which called the now-async generation API and expected a 201 + quiz body)
# ---------------------------------------------------------------------------

def _direct_quiz(test_db, user_email, questions, topic="Test Topic", difficulty="medium"):
    """
    Insert a quiz + questions directly into the test DB.
    Returns a dict that mirrors the old API response shape so all existing
    test assertions (data["id"], data["questions"][0]["id"], etc.) still work.
    """
    from app.models.user import User

    user = test_db.query(User).filter(User.email == user_email).first()
    assert user is not None, f"User {user_email!r} not found in test DB"

    quiz = Quiz(
        user_id=user.id,
        title=f"{topic} \u2014 {difficulty.capitalize()} Quiz",
        difficulty=difficulty,
        time_limit=len(questions) * 60,
        total_questions=len(questions),
    )
    test_db.add(quiz)
    test_db.flush()

    rows = []
    for i, q in enumerate(questions):
        row = Question(
            quiz_id=quiz.id,
            question_text=q["question"],
            type=q.get("type", "mcq"),
            payload=q.get("payload", {}),
            answer_key=q.get("answer_key", {}),
            points=1,
            explanation=q.get("explanation", ""),
            order_index=i,
        )
        test_db.add(row)
        rows.append(row)

    test_db.commit()
    test_db.refresh(quiz)
    for row in rows:
        test_db.refresh(row)

    return {
        "id":              quiz.id,
        "title":           quiz.title,
        "difficulty":      quiz.difficulty,
        "total_questions": quiz.total_questions,
        "questions": [
            {
                "id":            row.id,
                "question_text": row.question_text,
                "type":          row.type,
                "payload":       row.payload,
                "answer_key":    row.answer_key,
                "explanation":   row.explanation,
            }
            for row in rows
        ],
    }


# ===========================================================================
# AUTH FLOW
# ===========================================================================

def test_signup_returns_token(client):
    resp = client.post("/api/auth/signup", json={
        "name": "Alice", "email": "alice@test.com",
        "password": "password123", "role": "student",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_signup_duplicate_email_returns_400(client):
    payload = {"name": "Bob", "email": "bob@test.com", "password": "password123", "role": "student"}
    client.post("/api/auth/signup", json=payload)
    resp = client.post("/api/auth/signup", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_login_valid_credentials_returns_token(client):
    client.post("/api/auth/signup", json={
        "name": "Carol", "email": "carol@test.com",
        "password": "mypassword", "role": "student",
    })
    resp = client.post("/api/auth/login", json={
        "email": "carol@test.com", "password": "mypassword",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_returns_401(client):
    client.post("/api/auth/signup", json={
        "name": "Dave", "email": "dave@test.com",
        "password": "correct", "role": "student",
    })
    resp = client.post("/api/auth/login", json={
        "email": "dave@test.com", "password": "wrong",
    })
    assert resp.status_code == 401


def test_get_me_returns_current_user(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "testuser@example.com"
    assert "password_hash" not in data


def test_get_me_unauthenticated_returns_401(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


# ===========================================================================
# QUIZ GENERATION (Sprint 10: async — endpoints now return 202 + job_id)
# ===========================================================================

def test_generate_quiz_from_topic_returns_202(client, auth_headers):
    """Sprint 10: generation endpoint returns 202 + job_id immediately."""
    with patch("app.routers.quiz.run_quiz_from_topic_job"):
        resp = client.post("/api/quizzes/generate-from-topic", headers=auth_headers, json={
            "topic": "Mathematics",
            "num_questions": 1,
            "difficulty": "easy",
            "question_types": ["mcq"],
        })
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "pending"


def test_generate_quiz_empty_topic_returns_400(client, auth_headers):
    resp = client.post("/api/quizzes/generate-from-topic", headers=auth_headers, json={
        "topic": "   ", "num_questions": 1, "difficulty": "easy", "question_types": ["mcq"],
    })
    assert resp.status_code == 400


# ===========================================================================
# FETCH QUIZ
# ===========================================================================

def test_fetch_quiz_returns_questions(client, auth_headers, test_db):
    quiz_data = _direct_quiz(test_db, "testuser@example.com", [MCQ_QUESTION])
    quiz_id   = quiz_data["id"]

    resp = client.get(f"/api/quizzes/{quiz_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == 1


def test_fetch_nonexistent_quiz_returns_404(client, auth_headers):
    resp = client.get("/api/quizzes/99999", headers=auth_headers)
    assert resp.status_code == 404


# ===========================================================================
# SUBMIT QUIZ
# ===========================================================================

def _generate_quiz(client, auth_headers, test_db, questions, topic="Test Topic"):
    """Sprint 10 wrapper: insert quiz directly, bypassing the async generation API."""
    return _direct_quiz(test_db, "testuser@example.com", questions, topic)


def test_submit_all_correct(client, auth_headers, test_db):
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION])
    quiz_id = quiz_data["id"]
    q_id = str(quiz_data["questions"][0]["id"])
    correct_answer = 3   # correct_index is 3

    with patch("app.routers.quiz.generate_feedback", return_value="Well done!"):
        resp = client.post(f"/api/quizzes/{quiz_id}/submit", headers=auth_headers, json={
            "answers": {q_id: correct_answer},
            "time_taken": 30,
        })
    assert resp.status_code == 201
    data = resp.json()
    assert data["correct"] == 1
    assert data["wrong"] == 0
    assert data["skipped"] == 0
    assert data["percentage"] == 100.0


def test_submit_all_wrong(client, auth_headers, test_db):
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION])
    quiz_id = quiz_data["id"]
    q_id = str(quiz_data["questions"][0]["id"])

    with patch("app.routers.quiz.generate_feedback", return_value="Review your basics."):
        resp = client.post(f"/api/quizzes/{quiz_id}/submit", headers=auth_headers, json={
            "answers": {q_id: 0},   # wrong answer (correct is 3)
            "time_taken": 15,
        })
    assert resp.status_code == 201
    data = resp.json()
    assert data["correct"] == 0
    assert data["wrong"] == 1
    assert data["percentage"] == 0.0


def test_submit_all_skipped(client, auth_headers, test_db):
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION])
    quiz_id = quiz_data["id"]

    with patch("app.routers.quiz.generate_feedback", return_value="Try to answer next time."):
        resp = client.post(f"/api/quizzes/{quiz_id}/submit", headers=auth_headers, json={
            "answers": {},   # no answers submitted
            "time_taken": 0,
        })
    assert resp.status_code == 201
    data = resp.json()
    assert data["skipped"] == 1
    assert data["correct"] == 0
    assert data["percentage"] == 0.0


def test_submit_mixed_two_questions(client, auth_headers, test_db):
    """2 questions: answer Q1 correctly, skip Q2 → score 50%."""
    quiz_data = _generate_quiz(client, auth_headers, test_db, TWO_MCQ)
    quiz_id = quiz_data["id"]
    questions = quiz_data["questions"]
    q1_id = str(questions[0]["id"])
    # Q1 correct_index = 0

    with patch("app.routers.quiz.generate_feedback", return_value="Good partial work."):
        resp = client.post(f"/api/quizzes/{quiz_id}/submit", headers=auth_headers, json={
            "answers": {q1_id: 0},   # Q1 correct, Q2 skipped
            "time_taken": 60,
        })
    assert resp.status_code == 201
    data = resp.json()
    assert data["correct"] == 1
    assert data["skipped"] == 1
    assert data["percentage"] == 50.0


def test_submit_attempt_saved_to_db(client, auth_headers, test_db):
    """Verify attempt is persisted: submit once, submit again → 2 attempts exist (no duplicate check)."""
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION])
    quiz_id = quiz_data["id"]
    q_id = str(quiz_data["questions"][0]["id"])

    with patch("app.routers.quiz.generate_feedback", return_value="Good."):
        r1 = client.post(f"/api/quizzes/{quiz_id}/submit", headers=auth_headers, json={
            "answers": {q_id: 3}, "time_taken": 10,
        })
        r2 = client.post(f"/api/quizzes/{quiz_id}/submit", headers=auth_headers, json={
            "answers": {q_id: 0}, "time_taken": 10,
        })
    assert r1.status_code == 201
    assert r2.status_code == 201
    # Two distinct attempt IDs
    assert r1.json()["id"] != r2.json()["id"]


# ===========================================================================
# EXPORT
# ===========================================================================

def test_export_txt_mcq_with_answers(client, auth_headers, test_db):
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION], topic="Math Quiz")
    quiz_id = quiz_data["id"]

    resp = client.get(
        f"/api/quizzes/{quiz_id}/export",
        headers=auth_headers,
        params={"format": "txt", "include_answers": True},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    body = resp.text
    assert "[MCQ]" in body
    assert "What is 2 + 2?" in body
    assert "Answer: D" in body   # correct_index=3 → D


def test_export_txt_mcq_without_answers(client, auth_headers, test_db):
    """Practice sheet (include_answers=False) must show Answer Key block but not inline answers."""
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION])
    quiz_id = quiz_data["id"]

    resp = client.get(
        f"/api/quizzes/{quiz_id}/export",
        headers=auth_headers,
        params={"format": "txt", "include_answers": False},
    )
    assert resp.status_code == 200
    body = resp.text
    assert "Answer Key" in body
    # Inline answer tick must not appear in the question block
    assert "✔ Answer" not in body.split("Answer Key")[0]


def test_export_json_true_false(client, auth_headers, test_db):
    quiz_data = _generate_quiz(client, auth_headers, test_db, [TRUE_FALSE_QUESTION])
    quiz_id = quiz_data["id"]

    resp = client.get(
        f"/api/quizzes/{quiz_id}/export",
        headers=auth_headers,
        params={"format": "json", "include_answers": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "questions" in data
    q = data["questions"][0]
    assert q["type"] == "true_false"
    assert q["answer_key"]["correct"] is True


def test_export_json_excludes_answer_key_when_false(client, auth_headers, test_db):
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION])
    quiz_id = quiz_data["id"]

    resp = client.get(
        f"/api/quizzes/{quiz_id}/export",
        headers=auth_headers,
        params={"format": "json", "include_answers": False},
    )
    assert resp.status_code == 200
    q = resp.json()["questions"][0]
    assert "answer_key" not in q


# ===========================================================================
# LIST & DELETE
# ===========================================================================

def test_list_quizzes_returns_all_user_quizzes(client, auth_headers, test_db):
    _direct_quiz(test_db, "testuser@example.com", [MCQ_QUESTION], topic="Topic A")
    _direct_quiz(test_db, "testuser@example.com", [MCQ_QUESTION], topic="Topic B")

    resp = client.get("/api/quizzes", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_delete_quiz_removes_it(client, auth_headers, test_db):
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION])
    quiz_id = quiz_data["id"]

    del_resp = client.delete(f"/api/quizzes/{quiz_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/quizzes/{quiz_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_nonexistent_quiz_returns_404(client, auth_headers):
    resp = client.delete("/api/quizzes/99999", headers=auth_headers)
    assert resp.status_code == 404


# ===========================================================================
# OWNERSHIP ISOLATION
# ===========================================================================

def test_user_cannot_access_other_users_quiz(client, auth_headers, auth_headers_b, test_db):
    """User A creates a quiz; User B must get 404 when fetching it."""
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION], topic="Private Quiz")
    quiz_id = quiz_data["id"]

    resp = client.get(f"/api/quizzes/{quiz_id}", headers=auth_headers_b)
    assert resp.status_code == 404


def test_user_cannot_delete_other_users_quiz(client, auth_headers, auth_headers_b, test_db):
    """User A creates a quiz; User B must get 404 on delete (not a 403 — same as get)."""
    quiz_data = _generate_quiz(client, auth_headers, test_db, [MCQ_QUESTION], topic="Other Quiz")
    quiz_id = quiz_data["id"]

    resp = client.delete(f"/api/quizzes/{quiz_id}", headers=auth_headers_b)
    assert resp.status_code == 404


def test_users_quiz_lists_are_isolated(client, auth_headers, auth_headers_b, test_db):
    """User A and User B each have their own quiz list — no cross-contamination."""
    _direct_quiz(test_db, "testuser@example.com",  [MCQ_QUESTION], topic="User A Topic")
    _direct_quiz(test_db, "otheruser@example.com", [MCQ_QUESTION], topic="User B Topic")

    list_a = client.get("/api/quizzes", headers=auth_headers).json()
    list_b = client.get("/api/quizzes", headers=auth_headers_b).json()

    assert len(list_a) == 1
    assert len(list_b) == 1
    assert list_a[0]["id"] != list_b[0]["id"]
