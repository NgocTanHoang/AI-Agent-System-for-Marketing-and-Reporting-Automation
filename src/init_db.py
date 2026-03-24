import sqlite3
import os

# Thiết lập đường dẫn
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'data', 'raw', 'marketing_intelligence.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Làm sạch hệ thống
tables = ['competitor_products', 'marketing_campaigns', 'social_sentiment', 'sales_performance', 'sales']
for table in tables:
    cursor.execute(f'DROP TABLE IF EXISTS {table}')

# --- BẢNG 1: ĐỐI THỦ & THÔNG SỐ (Để Agent so sánh Specs) ---
cursor.execute('''
    CREATE TABLE competitor_products (
        id INTEGER PRIMARY KEY,
        brand TEXT,
        model_name TEXT,
        key_features TEXT, -- Ví dụ: "Chip AI, Camera 200MP"
        price_segment TEXT, -- Flagship, Mid-range
        current_price REAL,
        strengths TEXT,
        weaknesses TEXT
    )
''')

# --- BẢNG 2: CHIẾN DỊCH MARKETING (Để Agent phân tích hiệu quả - ROI) ---
cursor.execute('''
    CREATE TABLE marketing_campaigns (
        id INTEGER PRIMARY KEY,
        campaign_name TEXT,
        channel TEXT, -- Facebook, Google, TikTok, KOL
        budget REAL,
        reach INTEGER, -- Lượt tiếp cận
        conversions INTEGER, -- Số đơn hàng từ quảng cáo
        start_date DATE,
        end_date DATE
    )
''')

# --- BẢNG 3: SENTIMENT & TRENDS (Dữ liệu từ Social Listening) ---
cursor.execute('''
    CREATE TABLE social_sentiment (
        id INTEGER PRIMARY KEY,
        keyword TEXT, -- ví dụ: "iPhone 17", "Màn hình gập"
        positive_score REAL, -- 0.0 đến 1.0
        negative_score REAL,
        top_complaint TEXT,
        trending_platform TEXT
    )
''')

# --- BẢNG 4: DOANH SỐ SMARTPHONE CHI TIẾT (Để Business Reporter phân tích) ---
cursor.execute('''
    CREATE TABLE sales (
        id INTEGER PRIMARY KEY,
        brand TEXT,
        model_name TEXT,
        spec_variant TEXT, -- RAM/Storage variant
        units_sold INTEGER,
        unit_price REAL,
        region TEXT,
        launch_date DATE
    )
''')

# --- BẢNG 5: HIỆU SUẤT DOANH SỐ (Kết quả cuối cùng để báo cáo) ---
cursor.execute('''
    CREATE TABLE sales_performance (
        id INTEGER PRIMARY KEY,
        product_name TEXT,
        units_sold INTEGER,
        revenue REAL,
        month_period TEXT -- ví dụ: "2026-03"
    )
''')

# --- 🚀 CHÈN DỮ LIỆU GIẢ (FAKE DATA) PHỤC VỤ MARKETING ---

# 1. Dữ liệu đối thủ (Để Agent viết bài so sánh)
competitors = [
    (1, 'Apple', 'iPhone 17 Pro', 'Apple Intelligence 2.0, A19 Chip', 'Flagship', 32000000, 'Brand loyalty, OS ecosystem', 'Slow charging'),
    (2, 'Samsung', 'Galaxy S26 Ultra', 'S-Pen, 100x Zoom AI', 'Flagship', 30000000, 'Best display, Zoom camera', 'Bulky design'),
    (3, 'Xiaomi', 'Mi 16 Pro', 'Leica Lens, 120W Charging', 'Mid-High', 18000000, 'Price/Performance, Charging speed', 'Software bugs')
]

# 2. Hiệu quả quảng cáo (Để Agent đề xuất phân bổ ngân sách)
campaigns = [
    (1, 'Tet Tech Festival', 'TikTok', 50000000, 1000000, 1200, '2026-01-01', '2026-02-10'),
    (2, 'Back to School', 'Facebook', 30000000, 500000, 450, '2026-08-15', '2026-09-30'),
    (3, 'AI Phone Launch', 'Google Search', 100000000, 2000000, 3500, '2026-03-01', '2026-03-31')
]

# 3. Phản hồi mạng xã hội (Để Agent điều chỉnh nội dung content)
sentiment = [
    (1, 'Foldable Screen', 0.85, 0.15, 'Crease visibility', 'TikTok'),
    (2, 'Fast Charging', 0.90, 0.10, 'Battery health concern', 'YouTube'),
    (3, 'AI Photo Editing', 0.70, 0.30, 'Unnatural results', 'Facebook')
]

# 4. Doanh số chi tiết smartphone (Để Business Reporter phân tích specs và phân khúc)
sales_data = [
    (1, 'Apple', 'iPhone 17 Pro', '256GB', 15000, 32000000, 'Vietnam', '2026-01-15'),
    (2, 'Apple', 'iPhone 17', '128GB', 25000, 25000000, 'Vietnam', '2026-01-15'),
    (3, 'Samsung', 'Galaxy S26 Ultra', '512GB', 12000, 30000000, 'Vietnam', '2026-02-01'),
    (4, 'Samsung', 'Galaxy S26', '256GB', 18000, 22000000, 'Vietnam', '2026-02-01'),
    (5, 'Xiaomi', 'Mi 16 Pro', '256GB', 22000, 18000000, 'Vietnam', '2026-02-15'),
    (6, 'Xiaomi', 'Mi 16', '128GB', 30000, 12000000, 'Vietnam', '2026-02-15'),
    (7, 'Google', 'Pixel 9 Pro', '256GB', 8000, 28000000, 'Vietnam', '2026-03-01'),
    (8, 'Google', 'Pixel 9', '128GB', 15000, 20000000, 'Vietnam', '2026-03-01'),
    (9, 'OnePlus', '12 Pro', '256GB', 10000, 25000000, 'Vietnam', '2026-03-15'),
    (10, 'OnePlus', '12', '128GB', 18000, 18000000, 'Vietnam', '2026-03-15')
]

# 5. Doanh số thực tế (Để Business Reporter chốt số)
sales_performance_data = [
    (1, 'iPhone 17 Pro', 5000, 160000000000, '2026-03'),
    (2, 'Galaxy S26 Ultra', 4200, 126000000000, '2026-03')
]

cursor.executemany('INSERT INTO competitor_products VALUES (?,?,?,?,?,?,?,?)', competitors)
cursor.executemany('INSERT INTO marketing_campaigns VALUES (?,?,?,?,?,?,?,?)', campaigns)
cursor.executemany('INSERT INTO social_sentiment VALUES (?,?,?,?,?,?)', sentiment)
cursor.executemany('INSERT INTO sales VALUES (?,?,?,?,?,?,?,?)', sales_data)
cursor.executemany('INSERT INTO sales_performance VALUES (?,?,?,?,?)', sales_performance_data)

conn.commit()
conn.close()
print("📈 Database Marketing Intelligence đã sẵn sàng cho Agent phân tích!")