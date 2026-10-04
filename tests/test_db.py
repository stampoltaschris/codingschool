import os
import json
import sqlite3
import pytest
import db_installer
import app

def test_json_loading(tmp_path):
    test_json = tmp_path / "test_questions.json"
    data = [
        {
            "id": "t1",
            "chapter": "Test Chapter",
            "question_text": "2 + 2 = ?",
            "options": ["3", "4", "5"],
            "correct_answer": "4",
            "explanation": "2+2=4"
        }
    ]
    test_json.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    loaded = db_installer.load_questions_from_json(str(test_json))
    assert len(loaded) == 1
    assert loaded[0]["id"] == "t1"
    assert loaded[0]["correct_answer"] == "4"

def test_db_setup_and_upsert(tmp_path):
    db_path = tmp_path / "test_exercises.db"
    conn = sqlite3.connect(str(db_path))

    db_installer.create_table(conn)

    questions = [
        {
            "id": "t1",
            "chapter": "Chapter 1",
            "question_text": "1 + 1",
            "options": ["1", "2"],
            "correct_answer": "2",
            "explanation": "1+1=2"
        },
        {
            "id": "t2",
            "chapter": "Chapter 1",
            "question_text": "5 - 3",
            "options": None,
            "correct_answer": "2",
            "explanation": "5-3=2"
        }
    ]

    db_installer.upsert_questions(conn, questions)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM exercises")
    count = cursor.fetchone()[0]
    assert count == 2

    # Test Upsert: update t1
    questions[0]["question_text"] = "1 + 1 updated"
    db_installer.upsert_questions(conn, questions)

    cursor.execute("SELECT question_text FROM exercises WHERE id = 't1'")
    updated_text = cursor.fetchone()[0]
    assert updated_text == "1 + 1 updated"

    conn.close()

def test_app_db_fetch(monkeypatch, tmp_path):
    db_path = tmp_path / "app_test.db"
    conn = sqlite3.connect(str(db_path))
    db_installer.create_table(conn)
    questions = [
        {
            "id": "q1",
            "chapter": "Math 101",
            "question_text": "10 / 2",
            "options": ["5", "10"],
            "correct_answer": "5",
            "explanation": "10/2=5"
        }
    ]
    db_installer.upsert_questions(conn, questions)
    conn.close()

    monkeypatch.setattr(app, "DB_NAME", str(db_path))

    chapters = app.fetch_chapters()
    assert chapters == ["Math 101"]

    qs = app.fetch_questions_by_chapter("Math 101")
    assert len(qs) == 1
    assert qs[0]["id"] == "q1"
    assert qs[0]["options_list"] == ["5", "10"]
