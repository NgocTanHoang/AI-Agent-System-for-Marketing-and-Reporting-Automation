import sqlite3
import os

db_path = "data/raw/marketing_intelligence.db"
if not os.path.exists(db_path):
    print("DB not found")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("--- TOTAL REVENUE ---")
    cur.execute("SELECT SUM(revenue) FROM sales_performance")
    print(cur.fetchone()[0])
    
    print("\n--- SALES PERFORMANCE SAMPLE ---")
    cur.execute("SELECT product_name, revenue, units_sold FROM sales_performance LIMIT 5")
    for row in cur.fetchall():
        print(row)
        
    print("\n--- CAMPAIGNS BUDGET ---")
    cur.execute("SELECT SUM(budget) FROM marketing_campaigns")
    print(cur.fetchone()[0])
    
    conn.close()
