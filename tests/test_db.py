import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_connection import get_connection

print("===TEST connection SQL Server")

try: 
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]

    print("\033[92mKet noi thanh cong\033[0m")
    print(f"     SQL Server version: {version[:50]}...")

    cursor.execute("SELECT DB_NAME()")
    db = cursor.fetchone()[0]

    print(f"\033[92m[OK Database hiện tại: {db}\033[0m")

    cursor.execute(
        """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    tables = [row[0] for row in cursor.fetchall()]
    expected_tables  = ["districts", "listing_features", "listings", "scrape_logs"]
    for t in expected_tables:
        status = "\033[92mOK\033[0m" if t in tables else f"\033[91mFAIL\033[0m - chưa chạy schema.sql"
        print(f"    [{status}] Bảng '{t}'")


    cursor.execute("SELECT COUNT(*) FROM districts")
    count = cursor.fetchone()[0]
    status = "\033[92mOK\033[0m" if count  == 24 else f"\033[91mFAIL\033[0m - chỉ có {count} quận"
    print(f"    [{status}] Bảng districts có {count} quận ")

    conn.close()

except Exception as e:
    print(f"[FAIL] Lỗi: {e}")
    print("\nKiểm tra lại:")
    print("  1. docker-compose up đang chạy không?")
    print("  2. File .env có DB_PASSWORD chưa?")
    print("  3. Đã chạy schema.sql chưa?")
