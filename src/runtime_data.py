import re
import sqlite3
from pathlib import Path

from src.config import DATABASE_PATH, get_runtime_model_info, load_pipeline_settings, setup_logging

logger = setup_logging("runtime_data")


def _database_path(db_path: str | Path | None = None) -> str:
    return str(Path(db_path) if db_path else DATABASE_PATH)


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def format_regions(settings: dict | None = None) -> str:
    settings = settings or load_pipeline_settings()
    return ", ".join(settings["analysis"]["allowed_regions"])


def build_channel_roi_reference(db_path: str | Path | None = None, settings: dict | None = None) -> str:
    settings = settings or load_pipeline_settings()
    fallback = settings["analysis"]["reference_roi_data"]

    try:
        with sqlite3.connect(_database_path(db_path)) as conn:
            if not _table_exists(conn, "marketing_campaigns"):
                return fallback

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT channel, ROUND(AVG(roi), 2) AS avg_roi, ROUND(AVG(budget) / 1000000.0, 0) AS avg_budget_million
                FROM marketing_campaigns
                GROUP BY channel
                ORDER BY avg_roi DESC
                """
            )
            rows = cursor.fetchall()

        if not rows:
            return fallback

        return ", ".join(
            f"{channel}={avg_roi} (budget {int(avg_budget)}tr)"
            for channel, avg_roi, avg_budget in rows
        )
    except Exception as exc:
        logger.warning("Cannot build ROI reference from DB: %s", exc)
        return fallback


def fetch_learning_signals(
    limit: int = 5,
    lookback_days: int = 30,
    db_path: str | Path | None = None,
) -> list[dict]:
    try:
        with sqlite3.connect(_database_path(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "learning_signals"):
                return []

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, insight_type, learning_content
                FROM learning_signals
                WHERE timestamp >= datetime('now', ?)
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (f"-{lookback_days} days", limit),
            )
            return [dict(row) for row in cursor.fetchall()]
    except Exception as exc:
        logger.warning("Cannot read learning signals: %s", exc)
        return []


def build_learning_signal_context(
    limit: int = 5,
    lookback_days: int = 30,
    db_path: str | Path | None = None,
) -> str:
    signals = fetch_learning_signals(limit=limit, lookback_days=lookback_days, db_path=db_path)
    if not signals:
        return (
            "CHU KY TRUOC chua co learning signal duoc xac nhan. "
            "Hay van tuan thu day du data grounding va tu tao them signal moi sau khi bao cao ket thuc."
        )

    bullets = []
    for item in signals:
        content = re.sub(r"\s+", " ", item["learning_content"]).strip()
        if len(content) > 180:
            content = content[:177] + "..."
        bullets.append(f"- [{item['timestamp']}] {item['insight_type']}: {content}")

    return "LEARNING SIGNALS GAN DAY can duoc dung de tranh lap lai sai sot va uu tien co hoi:\n" + "\n".join(bullets)


def build_signal_fallback_entries(
    report_content: str,
    db_path: str | Path | None = None,
) -> list[dict]:
    entries = []
    report_size = len(report_content)
    resolved_db_path = _database_path(db_path)

    try:
        with sqlite3.connect(resolved_db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT model_name, SUM(units_sold) AS total_units
                FROM sales
                GROUP BY model_name
                ORDER BY total_units ASC, model_name ASC
                LIMIT 1
                """
            )
            low_model = cursor.fetchone()

            cursor.execute(
                """
                SELECT channel, ROUND(AVG(roi), 2) AS avg_roi, ROUND(AVG(budget), 0) AS avg_budget
                FROM marketing_campaigns
                GROUP BY channel
                ORDER BY avg_roi DESC
                """
            )
            channel_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT keyword, top_complaint, total_mentions, trending_platform
                FROM social_sentiment
                ORDER BY total_mentions DESC, negative_score DESC
                LIMIT 1
                """
            )
            trend = cursor.fetchone()
    except Exception as exc:
        logger.warning("Cannot derive fallback signals from DB: %s", exc)
        low_model = None
        channel_rows = []
        trend = None

    if low_model:
        entries.append(
            {
                "insight_type": "low_performer",
                "learning_content": (
                    f"[Auto-extracted] {low_model[0]} dang la model co san luong thap nhat "
                    f"voi {low_model[1]} units trong dataset hien tai. Can kiem tra lai dinh vi, "
                    f"uu dai va kenh tiep can trong chu ky tiep theo. Report size: {report_size} chars."
                ),
            }
        )

    if channel_rows:
        best = channel_rows[0]
        worst = channel_rows[-1]
        entries.append(
            {
                "insight_type": "budget_realloc",
                "learning_content": (
                    f"[Auto-extracted] {best[0]} dang co ROI trung binh {best[1]} voi ngan sach trung binh "
                    f"{int(best[2]):,} VND, trong khi {worst[0]} chi dat ROI {worst[1]}. "
                    f"Can uu tien tai phan bo ngan sach tu {worst[0]} sang {best[0]} neu muc tieu la toi uu hoa ROI."
                ),
            }
        )

    if trend:
        entries.append(
            {
                "insight_type": "trend_alert",
                "learning_content": (
                    f"[Auto-extracted] Chu de '{trend[0]}' dang co {trend[2]:,} luot de cap tren {trend[3]} "
                    f"va complaint noi bat la '{trend[1]}'. Can dua insight nay vao phan research va noi dung "
                    f"chu ky tiep theo de giam rui ro context drift."
                ),
            }
        )

    if len(entries) < 3:
        fallback_entries = [
            {
                "insight_type": "low_performer",
                "learning_content": (
                    f"[Auto-extracted] Bao cao co do dai {report_size} chars. Can ra soat nhung model hoac kenh "
                    "hieu suat thap duoc neu trong bao cao va bien thanh hanh dong cu the o chu ky sau."
                ),
            },
            {
                "insight_type": "budget_realloc",
                "learning_content": (
                    "[Auto-extracted] Can kiem tra lai ma tran ROI x Budget cua toan bo campaign de uu tien kenh co ROI cao nhung chua duoc dau tu."
                ),
            },
            {
                "insight_type": "trend_alert",
                "learning_content": (
                    "[Auto-extracted] Can theo doi lien tuc social sentiment va xu huong tim kiem de dua vao prompt research o chu ky tiep theo."
                ),
            },
        ]
        existing_types = {entry["insight_type"] for entry in entries}
        for fallback in fallback_entries:
            if fallback["insight_type"] not in existing_types:
                entries.append(fallback)

    return entries[:3]


def build_social_posts(
    limit: int = 5,
    db_path: str | Path | None = None,
) -> list[dict]:
    try:
        with sqlite3.connect(_database_path(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "social_sentiment"):
                return []

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT keyword, top_complaint, total_mentions, trending_platform, positive_score, negative_score, top_emotion
                FROM social_sentiment
                ORDER BY total_mentions DESC, negative_score DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
    except Exception as exc:
        logger.warning("Cannot build social posts from DB: %s", exc)
        return []

    posts = []
    for row in rows:
        posts.append(
            {
                "keyword": row["keyword"],
                "platform": row["trending_platform"],
                "mentions": row["total_mentions"],
                "sentiment": {
                    "positive": row["positive_score"],
                    "negative": row["negative_score"],
                    "emotion": row["top_emotion"],
                },
                "summary": (
                    f"{row['keyword']} dang duoc nhac den nhieu tren {row['trending_platform']}; "
                    f"complaint noi bat la {row['top_complaint']}."
                ),
            }
        )
    return posts


def get_dashboard_model_info(settings: dict | None = None) -> dict:
    return get_runtime_model_info(settings=settings)
