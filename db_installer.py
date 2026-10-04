import json
import sqlite3
from typing import List, Dict, Any, Optional

DB_NAME = "exercises.db"
JSON_FILE = "questions.json"

def create_table(conn: sqlite3.Connection) -> None:
    """Creates the exercises table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id TEXT PRIMARY KEY,
            chapter TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT NOT NULL
        );
    """)
    conn.commit()

def load_questions_from_json(json_filepath: str = JSON_FILE) -> List[Dict[str, Any]]:
    """Loads questions array from JSON file."""
    with open(json_filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def upsert_questions(conn: sqlite3.Connection, questions: List[Dict[str, Any]]) -> None:
    """Inserts or updates question records in the exercises table."""
    cursor = conn.cursor()
    for q in questions:
        q_id = str(q.get("id"))
        chapter = str(q.get("chapter", ""))
        question_text = str(q.get("question_text", ""))

        options_val = q.get("options")
        if options_val is not None and not isinstance(options_val, str):
            options = json.dumps(options_val, ensure_ascii=False)
        elif options_val is None:
            options = None
        else:
            options = options_val

        correct_answer = str(q.get("correct_answer", ""))
        explanation = str(q.get("explanation", ""))

        cursor.execute("""
            INSERT INTO exercises (id, chapter, question_text, options, correct_answer, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                chapter=excluded.chapter,
                question_text=excluded.question_text,
                options=excluded.options,
                correct_answer=excluded.correct_answer,
                explanation=excluded.explanation;
        """, (q_id, chapter, question_text, options, correct_answer, explanation))
    conn.commit()

def setup_database(db_name: str = DB_NAME, json_filepath: str = JSON_FILE) -> None:
    """Main setup procedure to create DB table and import JSON data."""
    conn = sqlite3.connect(db_name)
    try:
        create_table(conn)
        questions = load_questions_from_json(json_filepath)
        upsert_questions(conn, questions)
        print(f"Successfully processed {len(questions)} questions into '{db_name}'.")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()
