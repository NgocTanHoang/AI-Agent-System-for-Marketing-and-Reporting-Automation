import sqlite3
import os

db_path = r"d:\cv\project\01_AI Agent System for Marketing and Reporting Automation\data\raw\marketing_intelligence.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def check_table(table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"Table {table_name}: {', '.join(cols)}")

check_table("social_sentiment")
check_table("marketing_campaigns")
check_table("sales")
check_table("competitor_products")
conn.close()
