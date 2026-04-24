import sqlite3

from src.init_db import init_db
from src.runtime_data import (
    build_channel_roi_reference,
    build_learning_signal_context,
    build_signal_fallback_entries,
    build_social_posts,
)
# Không test sanitize_vietnamese_text vì đã thay thế bằng LLM-as-a-Judge (QA Reviewer)


def test_learning_signal_context_uses_saved_signals(tmp_path):
    db_path = tmp_path / "marketing.db"
    init_db(str(db_path))

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                learning_content TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO learning_signals (timestamp, insight_type, learning_content)
            VALUES (datetime('now'), 'trend_alert', 'Theo doi phan hoi ve tinh nang AI.')
            """
        )
        conn.commit()

    context = build_learning_signal_context(limit=3, lookback_days=30, db_path=db_path)

    assert "trend_alert" in context
    assert "Theo doi phan hoi" in context


def test_signal_fallback_entries_are_derived_from_database(tmp_path):
    db_path = tmp_path / "marketing.db"
    init_db(str(db_path))

    entries = build_signal_fallback_entries("bao cao demo", db_path=db_path)

    assert len(entries) == 3
    assert {entry["insight_type"] for entry in entries} == {
        "low_performer",
        "budget_realloc",
        "trend_alert",
    }


def test_social_posts_and_roi_reference_use_real_tables(tmp_path):
    db_path = tmp_path / "marketing.db"
    init_db(str(db_path))

    posts = build_social_posts(limit=3, db_path=db_path)
    roi_reference = build_channel_roi_reference(db_path=db_path)

    assert len(posts) == 3
    assert all("summary" in post for post in posts)
    assert "=" in roi_reference



