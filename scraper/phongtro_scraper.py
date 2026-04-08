import time 
import re
import logging
import requests
from bs4 import BeautifulSoup
import pyodbc
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# __file__                          = đường dẫn file hiện tại
#                                     vd: E:/Project/.../scraper/phongtro_scraper.py
# os.path.abspath(__file__)         = đường dẫn tuyệt đối đầy đủ
# os.path.dirname(...)              = lấy thư mục chứa file → scraper/
# os.path.dirname(dirname(...))     = lên 1 tầng nữa → saigon_proptech/
# sys.path.append(...)              = thêm saigon_proptech/ vào nơi Python tìm module
# → Nhờ vậy dòng dưới mới import được config và database
from config import SCRAPER_DELAY, MAX_PAGES, RAW_DATA_PATH
from database.db_connection import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",

    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/scraper.log"), # ghi ra file - xem lại lịch sử khi container đã tắt
    ]
)

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),

    "Accept-Language": "vi-VN,vi;q=0.9, en;q=0.8",

    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
} 

BASE_URL = "https://phongtro123.com/tinh-thanh/ho-chi-minh?orderby=moi-nhat"

DISTRICT_MAP = {
    "quận 1": 1,  "quan 1": 1,  "q1": 1,  "q. 1": 1,
    "quận 2": 2,  "quan 2": 2,  "q2": 2,  "q. 2": 2,
    "quận 3": 3,  "quan 3": 3,  "q3": 3,  "q. 3": 3,
    "quận 4": 4,  "quan 4": 4,  "q4": 4,  "q. 4": 4,
    "quận 5": 5,  "quan 5": 5,  "q5": 5,  "q. 5": 5,
    "quận 6": 6,  "quan 6": 6,  "q6": 6,  "q. 6": 6,
    "quận 7": 7,  "quan 7": 7,  "q7": 7,  "q. 7": 7,
    "quận 8": 8,  "quan 8": 8,  "q8": 8,  "q. 8": 8,
    "quận 9": 9,  "quan 9": 9,  "q9": 9,  "q. 9": 9,
    "quận 10": 10, "quan 10": 10, "q10": 10,
    "quận 11": 11, "quan 11": 11, "q11": 11,
    "quận 12": 12, "quan 12": 12, "q12": 12,
    "bình thạnh": 13, "binh thanh": 13,
    "bình tân":   14, "binh tan":   14,
    "gò vấp":     15, "go vap":     15,
    "phú nhuận":  16, "phu nhuan":  16,
    "tân bình":   17, "tan binh":   17,
    "tân phú":    18, "tan phu":    18,
    "thủ đức":    19, "thu duc":    19,
    "bình chánh": 20, "binh chanh": 20,
    "hóc môn":    21, "hoc mon":    21,
    "nhà bè":     22, "nha be":     22,
    "cần giờ":    23, "can gio":    23,
    "củ chi":     24, "cu chi":     24,
}

def parse_price(price_raw: str) -> int | None:
    if not price_raw:
        return None
    text = price_raw.lower().strip()

    if any(kw in text for kw in ["thoả thuận", "thoa thuan", "liên hệ"]):
        return None
    
    match = re.search(r"([\d,.]+)\s*triệu", text)
    #2.5 triệu/tháng -> match.group(1) = "2.5"
    if match:
        so = float(match.group(1).replace(",", "."))
        return int(so*1_000_000)

    match = re.search(r"[\d][.\d,]*[\d]", text)
    if match:
        so_str = match.group().replace(".", "").replace(",", "")
        try: 
            return int(so_str)
        except ValueError:
            return None
        
def parse_area(area_raw: str) -> float | None:
    if not area_raw:
        return None
    
    text = area_raw.lower().strip()

    match = re.search(r"([\d.]+)", text)
    if match:
        return float(match.group(1))
    
    return None

def parse_district(address_raw: str) -> int | None:
    if not address_raw:
        return None
    
    text = address_raw.lower().strip()

    text = re.sub(r"\s+", " ", text)
    text = text.replace(".", "")
    text = text.replace("-", " ") 
    for key in sorted(DISTRICT_MAP.keys(), key=len, reverse=True):
        # fix lỗi "bình" bị map trước "bình thạnh"
        if key in text:
            return DISTRICT_MAP[key]
    return None

def parse_features(soup_item) -> dict:
    text = soup_item.get_text(" ", strip=True).lower()

    return {
        "has_wc": 1 if any(k in text for k in ["wc", "toilet", "nhà vệ sinh", "tolet"]) else 0,
        "has_ac": 1 if any(k in text for k in ["điều hoà", "máy lạnh", "air condition"]) else 0,
        "has_parking": 1 if any(k in text for k in ["để xe", "parking", "chỗ để xe", "nhà xe"]) else 0,
        "has_kitchen": 1 if any(k in text for k in ["bếp", "nấu ăn", "kitchen"]) else 0,
        "has_balcony": 1 if any(k in text for k in ["ban công", "balcony"]) else 0,
        "has_security": 1 if any(k in text for k in ["bảo vệ", "camera", "vân tay", "an ninh", "security"]) else 0,
    }

def fetch_page(url: str, retries: int = 3) -> BeautifulSoup | None:
    """
    Tải 1 trang web, retry tối đa 3 lần nếu có lỗi, trả về BeautifulSoup hoặc None nếu thất bại.
    """

    for attempt in range(1, retries + 1):
        try: 
            resp = requests.get(url, headers=HEADERS, timeout= 20)
            resp.raise_for_status()

            resp.encoding = "utf-8"
            return BeautifulSoup(resp.text, "html.parser")
        except requests.exceptions.Timeout:
            log.warning(f"Time out lần {attempt}/{retries}: {url}")
        except requests.exceptions.HTTPError as e:
            log.warning(f"HTTP {e.response.status_code} lần {attempt}: {url}")
        except requests.exceptions.RequestException as e:
            log.warning(f"Lỗi mạng lần {attempt}: {e}")

        time.sleep(SCRAPER_DELAY * attempt)

    log.error(f"Bỏ qua URL sau {retries} lần thất bại: {url}")
    return None

def parse_listing_item(item) -> dict | None:
    """
    Nhận 1 thẻ HTML của 1 bài đăng, trả về dict dữ liệu
    Trả None nếu thiếu tin quan trọng/
    s
    """

    try: 
        title_tag = item.select_one("h3.fs-6 a")
        title = title_tag.get_text(strip=True) if title_tag else None
        if not title:
            return None
        
        price_tag = item.select_one("span.text-green.fw-semibold")
        price_raw = price_tag.get_text(strip=True) if price_tag else None
        price_vnd = parse_price(price_raw)

        area_tag = item.select_one("div.mb-2.line-clamp-1 span:last-child")
        area_raw = area_tag.get_text(strip=True) if area_tag else None
        area_m2 = parse_area(area_raw)

        address_tag = item.select_one("div.mb-2.d-flex a.text-body")
        address_raw = address_tag.get_text(strip=True) if address_tag else None
        district_id = parse_district(address_raw or title)

        source_url = None
        if title_tag and title_tag.has_attr("href"):
            href = title_tag["href"]
            source_url = href if href.startswith("http") else f"https://phongtro123.com{href}"

        
        features = parse_features(item)

        return {
            "title":       title,
            "price_raw":   price_raw,
            "price_vnd":   price_vnd,
            "area_raw":    area_raw,
            "area_m2":     area_m2,
            "address_raw": address_raw,
            "district_id": district_id,
            "source_url":  source_url,
            **features,
        }
    except Exception as e:
        log.warning(f"Lỗi parse item: {e}")
        return None
    
def scrape_page(page_num:int) -> list[dict]:
    """
    Scrape 1 trang danh sách, trả về list các listing đã parse
    """

    url = f"{BASE_URL}&page={page_num}"
    log.info(f"Đang crawl trang {page_num}: {url}")

    soup = fetch_page(url)
    if not soup:
        return []
    
    items = soup.select("ul.post__listing > li")

    if not items: 
        log.warning(f"Trang {page_num}: Không tìm thấy item nào")
        return []
    
    results = []
    for item in items:
        parsed = parse_listing_item(item)
        if parsed:
            results.append(parsed)

    log.info(f"Trang {page_num}: parse được {len(results)}/{len(items)} items")
    return results



def insert_to_db(conn, listing: dict, log_id: int) -> bool:
    """
    Insert 1 listing vào bảng listings + listing_features
    trả true nếu thành công, false nếu trùng lặp hoặc error
    """

    try: 
        cursor = conn.cursor()

        if listing.get("source_url"):
            cursor.execute(
                "SELECT 1 FROM listings WHERE source_url = ?",
                listing["source_url"]
            )
            if cursor.fetchone():
                return False
            
        cursor.execute(
            """
            INSERT INTO listings (title, price_raw, price_vnd, area_raw, area_m2, address_raw, district_id, source_url)
            OUTPUT INSERTED.listing_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing["title"],
            listing.get("price_raw"),
            listing.get("price_vnd"),
            listing.get("area_raw"),
            listing.get("area_m2"),
            listing.get("address_raw"),
            listing.get("district_id"),
            listing.get("source_url"),
        ))

        listing_id = cursor.fetchone()[0]
        cursor.execute(
            """
            INSERT INTO listing_features
                (listing_id, has_wc, has_ac, has_parking,
                 has_kitchen, has_balcony, has_security)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            listing_id,
            listing.get("has_wc", 0),
            listing.get("has_ac", 0),
            listing.get("has_parking", 0),
            listing.get("has_kitchen", 0),
            listing.get("has_balcony", 0),
            listing.get("has_security", 0),
        ))

        conn.commit()
        return True
    except pyodbc.Error as e:
        conn.rollback()
        log.error(f"Lỗi DB khi đang insert: {e}")
        return False
    
def main():
    log.info("---------SaigonPropTech Scaper bắt đầu! ---------")

    conn = get_connection()

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scrape_logs (status) OUTPUT INSERTED.log_id VALUES ('running')"
    )
    log_id = cursor.fetchone()[0]
    conn.commit()
    log.info(f"Scrape session log_id = {log_id}")

    total_inserted = 0
    total_skipped = 0

    try:
        for page_num in range(1, MAX_PAGES + 1):
            listings = scrape_page(page_num)

            if not listings:
                log.info(f"Không còn dữ liệu ở trang {page_num}")
                break
            inserted_this_page = 0
            skipped_this_page = 0
            for listing in listings:
                inserted = insert_to_db(conn, listing, log_id)
                if inserted:
                    total_inserted += 1
                    inserted_this_page += 1
                else:
                    total_skipped += 1
                    skipped_this_page += 1

            log.info(
                f"Trang {page_num} xong | "
                f"Mới: {inserted_this_page} | Trùng: {skipped_this_page} || "
                f"Tổng Mới: {total_inserted} | Tổng Trùng: {total_skipped}"
            )

            if skipped_this_page == len(listings) and len(listings) > 0:
                log.info("Phát hiện dữ liệu đã cũ toàn bộ")
                log.info(f"Trang {page_num} có {skipped_this_page}/{len(listings)} tin trùng lặp.")
                log.info(f"Kích hoạt Early Stopping")
                break

            time.sleep(SCRAPER_DELAY)

        cursor.execute(
            """
            UPDATE scrape_logs
            SET status          = 'success',
                rows_inserted    = ?,
                rows_skipped     = ?
            WHERE log_id = ?
        """, (total_inserted, total_skipped, log_id))
        conn.commit()

    except Exception as e:
        log.error(f"Scraper gặp lỗi: {e}")
        cursor.execute("""
            UPDATE scrape_logs
            SET status = 'failed',
                error_msg = ?
            WHERE log_id = ?
        """, (str(e)[:500], log_id))

        conn.commit()
        raise

    finally: 
        conn.close()
        log.info(
            f"----------Kết thúc | Inserted = {total_inserted} | Skipped = {total_skipped} ----------"
        )

if __name__ == "__main__":
    main()