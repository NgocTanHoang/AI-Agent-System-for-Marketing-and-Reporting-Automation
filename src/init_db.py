"""
Khởi tạo database marketing_intelligence.db với dữ liệu synthetic cho demo/portfolio.
Chỉ chạy trực tiếp: python src/init_db.py
"""
import sqlite3
import os
import random
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# 1. CẤU HÌNH
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "marketing_intelligence.db")

BRAND_MODELS = {
    "Apple":   ["iPhone 17 Pro", "iPhone 17", "iPhone 16"],
    "Samsung": ["Galaxy S26 Ultra", "Galaxy A56", "Galaxy Z Fold 7"],
    "Xiaomi":  ["Mi 16 Pro", "Redmi Note 14", "POCO F7"],
    "Google":  ["Pixel 10 Pro", "Pixel 10"],
    "Oppo":    ["Find X9 Pro", "Reno 13"],
}

CHANNELS    = ["TikTok", "Facebook", "Google Search", "YouTube", "Instagram", "KOL Partnership"]
PLATFORMS   = ["TikTok", "Facebook", "YouTube", "Instagram", "Twitter/X"]
STATUSES    = ["Completed", "Active", "Planned"]
REGIONS     = ["North", "South", "Central", "Highlands"]
AGE_GROUPS  = ["Gen Z", "Millennials", "Gen X", "Boomers"]
PAYMENTS    = ["Credit Card", "E-Wallet", "Cash", "Installment"]
EMOTIONS    = ["Happy", "Excited", "Relieved", "Skeptical", "Frustrated"]


# ---------------------------------------------------------------------------
# 2. HÀM TẠO DỮ LIỆU
# ---------------------------------------------------------------------------

def _build_competitors() -> list[tuple]:
    return [
        (1, "Apple",   "iPhone 17 Pro",    "AI 2.0, A19",          "Flagship",       32_000_000, 2025, "Ecosystem",  "Slow charging"),
        (2, "Samsung", "Galaxy S26 Ultra", "100x Zoom, S-Pen",     "Flagship",       30_000_000, 2026, "Display",    "Bulky"),
        (3, "Xiaomi",  "Mi 16 Pro",        "120W Charge, Leica",   "High",           19_000_000, 2026, "Charging",   "UI bugs"),
        (4, "Oppo",    "Find X9 Pro",      "Hasselblad Cam",       "Flagship",       26_000_000, 2026, "Camera",     "Limited availability"),
        (5, "Google",  "Pixel 10 Pro",     "Tensor G5, Pure AI",   "Flagship",       28_000_000, 2025, "Software",   "Weak hardware"),
        (6, "Vivo",    "X200 Ultra",       "Zeiss Gimbal",         "Flagship",       24_000_000, 2026, "Video",      "Brand awareness"),
        (7, "Realme",  "GT 7 Pro",         "Snapdragon 8 Gen 5",   "Budget Flagship",14_000_000, 2026, "Value",      "Camera quality"),
        (8, "Sony",    "Xperia 1 VII",     "4K Display",           "Niche",          35_000_000, 2026, "Screen",     "High price"),
    ]


def _build_campaigns() -> list[tuple]:
    rows = []
    for i in range(1, 15):
        budget  = random.randint(20, 200) * 1_000_000
        reach   = random.randint(100_000, 5_000_000)
        conv    = int(reach * random.uniform(0.001, 0.02))
        roi     = round((conv * 2_000_000) / budget, 2)
        start   = (datetime.now() - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d")
        end     = (datetime.now() + timedelta(days=random.randint(0,  60))).strftime("%Y-%m-%d")
        rows.append((
            i, f"Campaign {i}",
            random.choice(CHANNELS), budget, reach, conv, roi,
            random.choice(STATUSES), start, end,
        ))
    return rows


def _build_sentiments() -> list[tuple]:
    keywords = [
        "AI Phone", "Foldable Screen", "Fast Charging", "Battery Life",
        "Camera Zoom", "Dynamic Island", "Screen Durability", "Heat Management",
    ]
    rows = []
    for i, kw in enumerate(keywords, 1):
        pos      = round(random.uniform(0.4, 0.95), 2)
        neg      = round(max(0.0, 1.0 - pos - random.uniform(0.0, 0.1)), 2)
        mentions = random.randint(5_000, 100_000)
        complaint = "Noise in quiet rooms" if neg > 0.3 else "Price too high"
        rows.append((
            i, kw, pos, neg, mentions,
            complaint,
            random.choice(PLATFORMS),
            random.choice(EMOTIONS),
        ))
    return rows


def _build_sales() -> list[tuple]:
    rows = []
    brands = list(BRAND_MODELS.keys())
    for i in range(1, 101):
        brand = random.choice(brands)
        model = random.choice(BRAND_MODELS[brand])
        price = random.randint(15, 35) * 1_000_000
        qty   = random.randint(10, 100)
        campaign_id = random.choice([None, *range(1, 15)])
        
        # Auto price_bin
        if price < 5_000_000:
            price_bin = "Dưới 5 triệu"
        elif price < 10_000_000:
            price_bin = "5-10 triệu"
        elif price < 20_000_000:
            price_bin = "10-20 triệu"
        else:
            price_bin = "Trên 20 triệu"
        
        rows.append((
            i, brand, model, "256GB/8GB", qty, price,
            random.choice(REGIONS),
            random.choice(AGE_GROUPS),
            random.choice(PAYMENTS),
            "2026-01-01",
            campaign_id,
            price_bin,
        ))
    return rows


def _build_performance() -> list[tuple]:
    return [
        (1,  "iPhone 17 Pro",    1_500, 48_000_000_000, "2026-03"),
        (2,  "Galaxy S26 Ultra", 1_200, 36_000_000_000, "2026-03"),
        (3,  "Mi 16 Pro",        1_800, 34_200_000_000, "2026-03"),
        (4,  "Find X9 Pro",        900, 23_400_000_000, "2026-03"),
        (5,  "Pixel 10 Pro",       750, 21_000_000_000, "2026-03"),
        (6,  "Galaxy A56",         620, 10_500_000_000, "2026-03"),
        (7,  "Reno 13",            480,  7_200_000_000, "2026-03"),
        (8,  "Redmi Note 14",    2_200,  6_600_000_000, "2026-03"),
        (9,  "POCO F7",            310,  4_340_000_000, "2026-03"),
        (10, "Galaxy Z Fold 7",     180,  6_300_000_000, "2026-03"),
    ]


# ---------------------------------------------------------------------------
# 3. KHỞI TẠO DATABASE
# ---------------------------------------------------------------------------

def init_db(db_path: str = DB_PATH) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑  Đã xóa database cũ: {db_path}")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE competitor_products (
                id            INTEGER PRIMARY KEY,
                brand         TEXT,
                model_name    TEXT,
                key_features  TEXT,
                price_segment TEXT,
                current_price REAL,
                release_year  INTEGER,
                strengths     TEXT,
                weaknesses    TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE marketing_campaigns (
                id            INTEGER PRIMARY KEY,
                campaign_name TEXT,
                channel       TEXT,
                budget        REAL,
                reach         INTEGER,
                conversions   INTEGER,
                roi           REAL,
                status        TEXT,
                start_date    DATE,
                end_date      DATE
            )
        """)

        cursor.execute("""
            CREATE TABLE social_sentiment (
                id                 INTEGER PRIMARY KEY,
                keyword            TEXT,
                positive_score     REAL,
                negative_score     REAL,
                total_mentions     INTEGER,
                top_complaint      TEXT,
                trending_platform  TEXT,
                top_emotion        TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE sales (
                id                 INTEGER PRIMARY KEY,
                brand              TEXT,
                model_name         TEXT,
                spec_variant       TEXT,
                units_sold         INTEGER,
                unit_price         REAL,
                region             TEXT,
                customer_age_group TEXT,
                payment_method     TEXT,
                launch_date        DATE,
                campaign_id        INTEGER,
                price_bin          TEXT,
                FOREIGN KEY (campaign_id) REFERENCES marketing_campaigns(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE sales_performance (
                id           INTEGER PRIMARY KEY,
                model_name   TEXT,
                units_sold   INTEGER,
                revenue      REAL,
                month_period TEXT
            )
        """)

        competitors  = _build_competitors()
        campaigns    = _build_campaigns()
        sentiments   = _build_sentiments()
        sales        = _build_sales()
        performance  = _build_performance()

        cursor.executemany("INSERT INTO competitor_products  VALUES (?,?,?,?,?,?,?,?,?)",  competitors)
        cursor.executemany("INSERT INTO marketing_campaigns  VALUES (?,?,?,?,?,?,?,?,?,?)", campaigns)
        cursor.executemany("INSERT INTO social_sentiment     VALUES (?,?,?,?,?,?,?,?)",     sentiments)
        cursor.executemany("INSERT INTO sales                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", sales)
        cursor.executemany("INSERT INTO sales_performance    VALUES (?,?,?,?,?)",           performance)

        conn.commit()

    print(
        f"✅ Database đã sẵn sàng tại: {os.path.abspath(db_path)}\n"
        f"   - competitor_products : {len(competitors)} records\n"
        f"   - marketing_campaigns : {len(campaigns)} records\n"
        f"   - social_sentiment    : {len(sentiments)} records\n"
        f"   - sales               : {len(sales)} records\n"
        f"   - sales_performance   : {len(performance)} records"
    )


# ---------------------------------------------------------------------------
# 4. ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()