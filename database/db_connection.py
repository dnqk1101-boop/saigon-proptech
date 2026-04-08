import pyodbc
import pandas as pd
from config import DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD

def get_connection():
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"TrustServerCertificate=yes;"
        f"Encoding=utf-8;"
        f"AutoTranslate=No;"
    )
    conn = pyodbc.connect(conn_str)
    conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
    conn.setencoding(encoding='utf-8')
    max_retries = 10
    for i in range(max_retries):
        try:
            return pyodbc.connect(conn_str)
        except pyodbc.Error:
            if i < max_retries - 1:
                print(f"--- [Thử lại {i+1}/{max_retries}] Đợi SQL Server khởi động... ---")
                time.sleep(5)  # Đợi 5 giây rồi thử lại
            else:
                print("--- [LỖI] Đã thử nhiều lần nhưng không thể kết nối SQL Server! ---")
                raise

def insert_listing(conn, listing: dict) -> int:
    sql = """
        INSERT INTO listings
            (title, price_raw, price_vnd, area_raw, area_m2, address_raw, district_id, source_url)
        OUTPUT INSERTED.listing_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    cursor = conn.cursor()
    cursor.execute(sql, (
        listing.get("title"),
        listing.get("price_raw"),
        listing.get("price_vnd"),
        listing.get("area_raw"),
        listing.get("area_m2"),
        listing.get("address_raw"),
        listing.get("district_id"),
        listing.get("source_url"),
    ))
    listing_id = cursor.fetchone()[0]
    conn.commit()
    return listing_id

def load_ml_features() -> pd.DataFrame:
    """Đọc VIEW ml_features thẳng vào DataFrame cho ML."""
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM ml_features", conn)
    