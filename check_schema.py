import sqlite3
import os

db_path = r"d:\cv\project\01_AI Agent System for Marketing and Reporting Automation\data\raw\marketing_intelligence.db"

if not os.path.exists(db_path):
    print("Database not found!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(social_sentiment)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columns in social_sentiment: {columns}")
    
    cursor.execute("PRAGMA table_info(marketing_campaigns)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columns in marketing_campaigns: {columns}")
    
    conn.close()
