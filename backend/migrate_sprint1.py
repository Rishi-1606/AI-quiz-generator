"""
Sprint 1 — DB Migration Script
Adds new columns to `questions` table and backfills existing MCQ rows.
Safe to run multiple times (idempotent via try/except per column).
"""

import json
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "quiz_generator.db")


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print(f"Connected to: {DB_PATH}")

    # ── Step 1: Add new columns (idempotent) ──────────────────────────────────
    new_columns = [
        ("type",       "TEXT    NOT NULL DEFAULT 'mcq'"),
        ("payload",    "TEXT"),       # JSON
        ("answer_key", "TEXT"),       # JSON
        ("points",     "INTEGER NOT NULL DEFAULT 1"),
        ("media_url",  "TEXT"),
    ]

    for col_name, col_def in new_columns:
        try:
            cur.execute(f"ALTER TABLE questions ADD COLUMN {col_name} {col_def}")
            print(f"  [ADDED] column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"  [SKIP] Column already exists: {col_name}")
            else:
                raise

    conn.commit()

    # -- Step 2: Backfill existing MCQ rows -----------------------------------
    cur.execute("SELECT id, options, correct_option, payload, answer_key FROM questions")
    rows = cur.fetchall()

    updated = 0
    skipped = 0

    for row in rows:
        # Skip if already backfilled
        if row["payload"] is not None and row["answer_key"] is not None:
            skipped += 1
            continue

        # Build new-format JSON from old columns
        options_raw = row["options"]
        correct_option = row["correct_option"]

        # options might already be a list (SQLite stored as JSON text)
        if isinstance(options_raw, str):
            options = json.loads(options_raw)
        else:
            options = options_raw or []

        payload    = json.dumps({"options": options})
        answer_key = json.dumps({"correct_index": correct_option})

        cur.execute(
            "UPDATE questions SET payload = ?, answer_key = ?, type = 'mcq' WHERE id = ?",
            (payload, answer_key, row["id"])
        )
        updated += 1

    conn.commit()
    conn.close()

    print(f"\n[DONE] Migration complete!")
    print(f"   Rows backfilled : {updated}")
    print(f"   Rows skipped    : {skipped} (already had payload/answer_key)")


if __name__ == "__main__":
    run()
