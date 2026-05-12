"""
Memory Layer — Persistent Learning Signals storage in dedicated memory.db.

Architecture:
  ┌──────────────────────────────────────────────────────────────────┐
  │  memory.db (data/memory.db)                                      │
  │  ├── learning_signals   — Bài học chiến lược qua các chu kỳ      │
  │  └── run_history        — Lịch sử chạy pipeline (audit trail)    │
  └──────────────────────────────────────────────────────────────────┘

Separation of Concerns:
  - marketing_intelligence.db → Dữ liệu nghiệp vụ (sales, campaigns) — READ ONLY
  - memory.db                 → Dữ liệu học máy (signals, history)   — READ/WRITE

Lý do tách: Tránh race condition giữa lệnh SELECT (Agent đọc) và INSERT (Signal ghi).
"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("memory_layer")


def _default_memory_path() -> str:
    from src.config import DATA_DIR
    return str(DATA_DIR / "memory.db")


def init_memory_db(db_path: Optional[str] = None) -> None:
    """
    Khởi tạo memory.db với schema cho learning_signals và run_history.
    Idempotent — an toàn khi gọi nhiều lần (CREATE TABLE IF NOT EXISTS).
    """
    path = db_path or _default_memory_path()

    with sqlite3.connect(path) as conn:
        cur = conn.cursor()

        # Bảng 1: Learning Signals — Bài học chiến lược
        cur.execute("""
            CREATE TABLE IF NOT EXISTS learning_signals (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id            TEXT,
                insight_type      TEXT NOT NULL CHECK(insight_type IN (
                    'low_performer', 'budget_realloc', 'trend_alert',
                    'quality_issue', 'competitive_shift', 'custom'
                )),
                learning_content  TEXT NOT NULL,
                severity          TEXT DEFAULT 'medium' CHECK(severity IN ('low', 'medium', 'high', 'critical')),
                resolved          INTEGER DEFAULT 0,
                timestamp         DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Bảng 2: Run History — Audit Trail
        cur.execute("""
            CREATE TABLE IF NOT EXISTS run_history (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id            TEXT UNIQUE NOT NULL,
                market_topic      TEXT,
                report_filename   TEXT,
                report_length     INTEGER,
                qa_passed         INTEGER DEFAULT 0,
                reflection_loops  INTEGER DEFAULT 0,
                signals_written   INTEGER DEFAULT 0,
                duration_seconds  REAL,
                error_message     TEXT,
                timestamp         DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index cho truy vấn nhanh
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_type_time
            ON learning_signals(insight_type, timestamp DESC)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_signals_resolved
            ON learning_signals(resolved, timestamp DESC)
        """)

        conn.commit()
    logger.info("✅ Memory DB initialized at: %s", path)


# ---------------------------------------------------------------------------
# LEARNING SIGNALS CRUD
# ---------------------------------------------------------------------------

def write_signal(
    insight_type: str,
    learning_content: str,
    run_id: Optional[str] = None,
    severity: str = "medium",
    db_path: Optional[str] = None,
) -> str:
    """
    Ghi một learning signal vào memory.db.
    Returns: success/error message string (Agent-friendly).
    """
    path = db_path or _default_memory_path()
    init_memory_db(path)  # Ensure table exists

    try:
        with sqlite3.connect(path) as conn:
            conn.execute(
                """
                INSERT INTO learning_signals (run_id, insight_type, learning_content, severity)
                VALUES (?, ?, ?, ?)
                """,
                (run_id, insight_type, learning_content, severity),
            )
            conn.commit()
        return f"✅ Đã ghi signal [{insight_type}] vào memory.db thành công."
    except Exception as e:
        logger.error("Lỗi ghi signal vào memory.db: %s", e)
        return f"❌ Lỗi ghi signal: {e}"


def read_signals(
    limit: int = 10,
    lookback_days: int = 30,
    only_unresolved: bool = True,
    db_path: Optional[str] = None,
) -> list[dict]:
    """
    Đọc learning signals gần đây từ memory.db.
    Dùng để inject context vào prompt cho Agent trong chu kỳ sau.
    """
    path = db_path or _default_memory_path()
    init_memory_db(path)  # Ensure table exists

    try:
        with sqlite3.connect(path) as conn:
            conn.row_factory = sqlite3.Row
            resolved_filter = "AND resolved = 0" if only_unresolved else ""
            rows = conn.execute(
                f"""
                SELECT id, run_id, insight_type, learning_content, severity, resolved, timestamp
                FROM learning_signals
                WHERE timestamp >= datetime('now', ?)
                {resolved_filter}
                ORDER BY
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    timestamp DESC
                LIMIT ?
                """,
                (f"-{lookback_days} days", limit),
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Lỗi đọc signals từ memory.db: %s", e)
        return []


def build_memory_context(
    limit: int = 5,
    lookback_days: int = 30,
    db_path: Optional[str] = None,
) -> str:
    """
    Build formatted context string từ learning signals cho injection vào Agent prompt.
    Đây là 'bộ nhớ dài hạn' giúp Agent không lặp lại lỗi cũ.
    """
    signals = read_signals(limit=limit, lookback_days=lookback_days, db_path=db_path)

    if not signals:
        return (
            "MEMORY: Chua co learning signal nao duoc ghi nhan tu cac chu ky truoc. "
            "Day la lan chay dau tien hoac khong co loi nao duoc phat hien gan day."
        )

    lines = ["📚 LEARNING SIGNALS TU CAC CHU KY TRUOC (Agent PHAI doc va tuan thu):"]
    for s in signals:
        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
            s["severity"], "⚪"
        )
        content = s["learning_content"]
        if len(content) > 200:
            content = content[:197] + "..."
        lines.append(
            f"  {severity_icon} [{s['insight_type']}] ({s['timestamp'][:16]}): {content}"
        )

    return "\n".join(lines)


def mark_signal_resolved(signal_id: int, db_path: Optional[str] = None) -> bool:
    """Đánh dấu một signal đã được xử lý (resolved) để không hiện lại."""
    path = db_path or _default_memory_path()
    try:
        with sqlite3.connect(path) as conn:
            conn.execute(
                "UPDATE learning_signals SET resolved = 1 WHERE id = ?",
                (signal_id,),
            )
            conn.commit()
        return True
    except Exception as e:
        logger.error("Lỗi resolve signal #%d: %s", signal_id, e)
        return False


def count_recent_signals(
    minutes: int = 10,
    db_path: Optional[str] = None,
) -> int:
    """Đếm số signals được ghi trong N phút gần đây."""
    path = db_path or _default_memory_path()
    init_memory_db(path)
    try:
        with sqlite3.connect(path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM learning_signals WHERE timestamp >= datetime('now', ?)",
                (f"-{minutes} minutes",),
            ).fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


def count_signals_for_run(
    run_id: str,
    minutes: int = 10,
    db_path: Optional[str] = None,
) -> int:
    """Đếm số signals được ghi cho một run cụ thể trong N phút gần đây."""
    if not run_id:
        return 0

    path = db_path or _default_memory_path()
    init_memory_db(path)
    try:
        with sqlite3.connect(path) as conn:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM learning_signals
                WHERE run_id = ?
                  AND timestamp >= datetime('now', ?)
                """,
                (run_id, f"-{minutes} minutes"),
            ).fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# RUN HISTORY
# ---------------------------------------------------------------------------

def log_run(
    run_id: str,
    market_topic: str = "",
    report_filename: str = "",
    report_length: int = 0,
    qa_passed: bool = False,
    reflection_loops: int = 0,
    signals_written: int = 0,
    duration_seconds: float = 0.0,
    error_message: str = "",
    db_path: Optional[str] = None,
) -> None:
    """Ghi lại metadata của một lần chạy pipeline."""
    path = db_path or _default_memory_path()
    init_memory_db(path)

    try:
        with sqlite3.connect(path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO run_history
                (run_id, market_topic, report_filename, report_length,
                 qa_passed, reflection_loops, signals_written,
                 duration_seconds, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, market_topic, report_filename, report_length,
                    int(qa_passed), reflection_loops, signals_written,
                    duration_seconds, error_message,
                ),
            )
            conn.commit()
    except Exception as e:
        logger.error("Lỗi ghi run history: %s", e)
