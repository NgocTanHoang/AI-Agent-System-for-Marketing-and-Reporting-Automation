import sqlite3
import os
import random
from datetime import datetime, timedelta

# --- CẤU HÌNH ĐƯỜNG DẪN DATABASE ---
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'marketing_intelligence.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# --- 1. BẢNG COMPETITOR_PRODUCTS (Mở rộng thêm RELEASE_YEAR) ---
cursor.execute('''
    CREATE TABLE competitor_products (
        id INTEGER PRIMARY KEY,
        brand TEXT,
        model_name TEXT,
        key_features TEXT,
        price_segment TEXT,
        current_price REAL,
        release_year INTEGER,
        strengths TEXT,
        weaknesses TEXT
    )
''')

# --- 2. BẢNG MARKETING_CAMPAIGNS (Mở rộng STATUS, ROI) ---
cursor.execute('''
    CREATE TABLE marketing_campaigns (
        id INTEGER PRIMARY KEY,
        campaign_name TEXT,
        channel TEXT,
        budget REAL,
        reach INTEGER,
        conversions INTEGER,
        roi REAL,
        status TEXT,
        start_date DATE,
        end_date DATE
    )
''')

# --- 3. BẢNG SOCIAL_SENTIMENT (Mở rộng TOTAL_MENTIONS, EMOTION) ---
cursor.execute('''
    CREATE TABLE social_sentiment (
        id INTEGER PRIMARY KEY,
        keyword TEXT,
        positive_score REAL,
        negative_score REAL,
        total_mentions INTEGER,
        top_complaint TEXT,
        trending_platform TEXT,
        top_emotion TEXT -- Happy, Angry, Excited, Neutral
    )
''')

# --- 4. BẢNG SALES (Mở rộng CUSTOMER_AGE, PAYMENT_METHOD) ---
cursor.execute('''
    CREATE TABLE sales (
        id INTEGER PRIMARY KEY,
        brand TEXT,
        model_name TEXT,
        spec_variant TEXT,
        units_sold INTEGER,
        unit_price REAL,
        region TEXT,
        customer_age_group TEXT,
        payment_method TEXT,
        launch_date DATE
    )
''')

# --- 5. BẢNG SALES_PERFORMANCE ---
cursor.execute('''
    CREATE TABLE sales_performance (
        id INTEGER PRIMARY KEY,
        product_name TEXT,
        units_sold INTEGER,
        revenue REAL,
        month_period TEXT
    )
''')

# --- 🚀 CHÈN DỮ LIỆU FAKE TRƯỞNG THÀNH (DENSE DATA) ---

# 1. Competitors
competitors = [
    (1, 'Apple', 'iPhone 17 Pro', 'AI 2.0, A19', 'Flagship', 32000000, 2025, 'Ecosystem', 'Charging'),
    (2, 'Samsung', 'Galaxy S26 Ultra', '100x Zoom, S-Pen', 'Flagship', 30000000, 2026, 'Display', 'Bulky'),
    (3, 'Xiaomi', 'Mi 16 Pro', '120W Charge, Leica', 'High', 19000000, 2026, 'Charging', 'UI Bug'),
    (4, 'Oppo', 'Find X9 Pro', 'Hasselblad Cam', 'Flagship', 26000000, 2026, 'Camera', 'Availability'),
    (5, 'Google', 'Pixel 10 Pro', 'Tensor G5, Pure AI', 'Flagship', 28000000, 2025, 'Software', 'Hardware'),
    (6, 'Vivo', 'X200 Ultra', 'Zeiss Gimbal', 'Flagship', 24000000, 2026, 'Video', 'Brand'),
    (7, 'Realme', 'GT 7 Pro', 'Snapdragon 8 Gen 5', 'Budget Flagship', 14000000, 2026, 'Value', 'Camera'),
    (8, 'Sony', 'Xperia 1 VII', '4K Display', 'Niche', 35000000, 2026, 'Screen', 'Price')
]

# 2. Campaigns
channels = ['TikTok', 'Facebook', 'Google Search', 'YouTube', 'Instagram', 'KOL Partnership']
statuses = ['Completed', 'Active', 'Planned']
campaigns = []
for i in range(1, 15):
    budget = random.randint(20, 200) * 1000000
    reach = random.randint(100000, 5000000)
    conv = int(reach * random.uniform(0.001, 0.02))
    roi = round((conv * 2000000) / budget, 2)
    start = (datetime.now() - timedelta(days=random.randint(30, 180))).strftime('%Y-%m-%d')
    end = (datetime.now() + timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
    campaigns.append((i, f"Campaign {i}", random.choice(channels), budget, reach, conv, roi, random.choice(statuses), start, end))

# 3. Sentiment
keywords = ['AI Phone', 'Foldable Screen', 'Fast Charging', 'Battery Life', 'Camera Zoom', 'Dynamic Island', 'Scree Durability', 'Heat Management']
emotions = ['Happy', 'Excited', 'Relieved', 'Skeptical', 'Frustrated']
sentiments = []
for i, kw in enumerate(keywords, 1):
    pos = round(random.uniform(0.4, 0.95), 2)
    neg = round(1.0 - pos - random.uniform(0.0, 0.1), 2)
    mentions = random.randint(5000, 100000)
    sentiments.append((i, kw, pos, neg, mentions, 'Noise in quiet rooms' if neg > 0.3 else 'Price', random.choice(channels), random.choice(emotions)))

# 4. Sales
brands = ['Apple', 'Samsung', 'Xiaomi', 'Google', 'Oppo']
regions = ['North', 'South', 'Central', 'Highlands']
age_groups = ['Gen Z', 'Millennials', 'Gen X', 'Boomers']
payments = ['Credit Card', 'E-Wallet', 'Cash', 'Installment']
sales = []
for i in range(1, 101):
    brand = random.choice(brands)
    model = f"{brand} Model {random.randint(1, 5)}"
    price = random.randint(10, 40) * 1000000
    qty = random.randint(500, 5000)
    sales.append((i, brand, model, '256GB/8GB', qty, price, random.choice(regions), random.choice(age_groups), random.choice(payments), '2026-01-01'))

# 5. Sales Performance
performance = [
    (1, 'iPhone 17 Pro', 15000, 480000000000, '2026-03'),
    (2, 'Galaxy S26 Ultra', 12000, 360000000000, '2026-03'),
    (3, 'Mi 16 Pro', 18000, 342000000000, '2026-03'),
    (4, 'Oppo Find X9', 9000, 234000000000, '2026-03'),
    (5, 'Pixel 10 Pro', 7500, 210000000000, '2026-03')
]

cursor.executemany('INSERT INTO competitor_products VALUES (?,?,?,?,?,?,?,?,?)', competitors)
cursor.executemany('INSERT INTO marketing_campaigns VALUES (?,?,?,?,?,?,?,?,?,?)', campaigns)
cursor.executemany('INSERT INTO social_sentiment VALUES (?,?,?,?,?,?,?,?)', sentiments)
cursor.executemany('INSERT INTO sales VALUES (?,?,?,?,?,?,?,?,?,?)', sales)
cursor.executemany('INSERT INTO sales_performance VALUES (?,?,?,?,?)', performance)

conn.commit()
conn.close()

print(f"✅ Database updated with {len(sales)} sales records, {len(campaigns)} campaigns and new columns!")