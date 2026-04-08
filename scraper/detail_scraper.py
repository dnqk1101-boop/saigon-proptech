import re
import time
import logging
import sys
import os
import requests as req_lib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.phongtro_scraper import fetch_page
from database.db_connection import get_connection
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
    encoding="utf-8"
)

import re
import time

def geocode_nominatim(address: str) -> tuple[float, float] | tuple[None, None]:
    if not address:
        return None, None
    
    address_base = address.replace("Hồ Chí Minh", "").strip().strip(",").strip()
    parts = [p.strip() for p in address_base.split(",") if p.strip()]

    processed_parts = []
    street_no_prefix = ""

    for i, part in enumerate(parts):
        if i == 0:
            street_raw = re.sub(r'(?i)^(số|hẻm|ngõ|ngách)?\s*\d+([a-z])?(\/\d+[a-z]*)*\s*', '', part).strip()
            processed_parts.append(street_raw)
            street_no_prefix = re.sub(r'(?i)\b(đường|đ\.)\s*', '', street_raw).strip()
        else:
            if re.search(r'\d+', part):
                processed_parts.append(part)
            else:
                cleaned = re.sub(r'(?i)\b(quận|q\.|huyện|phường|p\.|xã|thị trấn)\s*', '', part).strip()
                processed_parts.append(cleaned)

    queries = []


    queries.append(f"{', '.join(processed_parts)}, Hồ Chí Minh")

    if street_no_prefix and street_no_prefix != processed_parts[0]:
        variant_parts = [street_no_prefix] + processed_parts[1:]
        queries.append(f"{', '.join(variant_parts)}, Hồ Chí Minh")

    if len(processed_parts) >= 3:
        queries.append(f"{processed_parts[0]}, {processed_parts[-1]}, Hồ Chí Minh")
        if street_no_prefix and street_no_prefix != processed_parts[0]:
            queries.append(f"{street_no_prefix}, {processed_parts[-1]}, Hồ Chí Minh")

    if len(processed_parts) >= 2:
        queries.append(f"{processed_parts[-1]}, Hồ Chí Minh")

    unique_queries = list(dict.fromkeys(queries))


    for query in unique_queries:
        try:
            resp = req_lib.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1, "countrycodes": "vn"},
                headers={"User-Agent": "SaiGonPropTech-ML/2.0"},
                timeout=10,
            )
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            time.sleep(1.1) 
        except Exception as e:
            print(f"Nominatim lỗi: {e}")
            time.sleep(1.1)

    return None, None


def parse_address(soup) -> str | None:
    table = soup.select_one("table.table-borderless")
    if not table:
        return None
    
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        lable = cells[0].get_text(" ", strip=True).lower()

        if "địa chỉ" in lable:
            address_raw = cells[1].get_text(strip=True)
            return address_raw
        
    return None

def parse_posted_date(soup) -> str | None:
    rows = soup.select("table.table-borderless tr")
    for row in rows:
        cells = row.select("td")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True)
            if "ngày đăng" in label:
                match = re.search(r"(\d{2}/\d{2}/\d{4})", value)
                return match.group(1) if match else value
    return None


def parse_detail_features(soup) -> dict:

    features = {
        "has_furniture": 0, "has_loft":     0,
        "has_washer":    0, "has_fridge":   0,
        "has_elevator":  0, "has_basement":  0,
        "free_hours":    0, "no_owner":      0,
        "has_wc":        0, "has_ac":        0,
        "has_parking":   0, "has_kitchen":   0,
        "has_balcony":   0, "has_security":  0,
        "is_master_room": 0, "near_uni":     0
    }

    # Map text tiện ích → tên cột
    FEATURE_MAP = {
        "đầy đủ nội thất": "has_furniture",
        "full nội thất":   "has_furniture",
        "full nt":         "has_furniture",
        "nội thất":        "has_furniture",
        "có gác":          "has_loft",
        "có bếp":          "has_kitchen",
        "máy lạnh":        "has_ac",
        "điều hòa":        "has_ac",
        "máy giặt":        "has_washer",
        "tủ lạnh":         "has_fridge",
        "thang máy":       "has_elevator",
        "bảo vệ":          "has_security",
        "hầm để xe":       "has_basement",
        "chỗ để xe":       "has_parking",
        "để xe":           "has_parking",
        "giờ giấc tự do":  "free_hours",
        "không chung chủ": "no_owner",
        "nhà vệ sinh":     "has_wc",
        "wc riêng":        "has_wc",
        "ban công":        "has_balcony",
    }

    feature_divs = soup.select("div.text-body.d-flex")

    for div in feature_divs:
        text = div.get_text(strip=True).lower()
        icon = div.select_one("i")

        if icon:
            icon_class = icon.get("class", [])
            is_active = "green" in " ".join(icon_class)
        else:
            is_active = False

        if is_active:
            for keyword, col_name in FEATURE_MAP.items():
                if keyword in text:
                    features[col_name] = 1
                    break
    
    h2_tag = soup.find('h2', string=re.compile('Thông tin mô tả', re.I))
    if h2_tag:
        parent_div = h2_tag.find_parent('div')
        if parent_div:
            description = parent_div.get_text(" ", strip=True).lower()
            for keyword, col_name in FEATURE_MAP.items():
                if features[col_name] == 0 and keyword in description:
                    features[col_name] = 1
            if 'phòng master' in description:
                features['is_master_room'] = 1
            
            unis = ['rmit', 'tôn đức thắng', 'tđt', 'bách khoa', 'marketing', 'hutech', 'ute', 'spkt', 'uef', 'sư phạm', 'gtvt', 'us', 'nhân văn']
            if any(uni in description for uni in unis):
                features['near_uni'] = 1
    return features


def parse_detail_page(listing_id: int, url: str) -> dict | None:
    soup = fetch_page(url)

    if not soup:
        return None
    
    result = {"listing_id": listing_id}

    address_full = parse_address(soup)
    result["address_full"] = address_full

    lat, lng = geocode_nominatim(address_full)
    result["lat"] = lat
    result["lng"] = lng
    time.sleep(1.1)

    result["posted_at_raw"] = parse_posted_date(soup)

    result["features"] = parse_detail_features(soup)

    log.info(
        f"[{listing_id}] "
        f"addr='{address_full[:40] if address_full else None}' "
        f"lat={lat} lng={lng} "
        f"date={result['posted_at_raw']} "
        f"features={sum(result['features'].values())}"
    )

    return result


def update_db(conn, detail:dict):
    cursor = conn.cursor()
    lid = detail["listing_id"]

    updates = []
    values = []

    if detail.get("lat") is not None:
        updates.append("lat = ?")
        values.append(detail["lat"])
        updates.append("lng = ?")
        values.append(detail["lng"])

    if detail.get("posted_at_raw"):
        updates.append("posted_at_raw = ?")
        values.append(detail["posted_at_raw"])

    if detail.get("address_full"):
        updates.append("address_full = ?")
        values.append(detail["address_full"])

    if updates:
        values.append(lid)
        cursor.execute(
            f"UPDATE listings SET {', '.join(updates)} WHERE listing_id = ?",
            values
        )

    f = detail.get("features", {})
    if f:
        cursor.execute(
            """
            UPDATE listing_features SET
                has_wc = ?, has_ac = ?,
                has_parking = ?, has_kitchen = ?,
                has_balcony   = ?, has_security  = ?,
                has_furniture = ?, has_loft      = ?,
                has_washer    = ?, has_fridge    = ?,
                has_elevator  = ?, has_basement  = ?,
                free_hours    = ?, no_owner      = ?,
                near_uni     = ?
            WHERE listing_id = ?
        """, (
            f.get("has_wc", 0),        f.get("has_ac", 0),
            f.get("has_parking", 0),   f.get("has_kitchen", 0),
            f.get("has_balcony", 0),   f.get("has_security", 0),
            f.get("has_furniture", 0), f.get("has_loft", 0),
            f.get("has_washer", 0),    f.get("has_fridge", 0),
            f.get("has_elevator", 0),  f.get("has_basement", 0),
            f.get("free_hours", 0),    f.get("no_owner", 0),
            f.get("near_uni", 0),
            lid,
        ))

        conn.commit()

def enrich_all():

    log.info("--------- SaigonPropTech Enricher bắt đầu! ---------")
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO scrape_logs (status) OUTPUT INSERTED.log_id VALUES ('running_enrich')"
    )
    log_id = cursor.fetchone()[0]
    conn.commit()
    log.info(f"Enrich session log_id = {log_id}")

    cursor.execute("""
        SELECT listing_id, source_url
        FROM listings
        WHERE source_url IS NOT NULL
          AND   (
                lat IS NULL
                OR address_full IS NULL
            )
        ORDER BY listing_id
    """)
    rows = cursor.fetchall()
    total = len(rows)
    
    if total == 0:
        log.info("Không có listing nào cần enrich nữa.")
        cursor.execute("UPDATE scrape_logs SET status = 'success_enrich' WHERE log_id = ?", (log_id,))
        conn.commit()
        conn.close()
        return

    log.info(f"Cần enrich: {total} listings (~{total * 1.5 / 60:.0f} phút)")

    ok = failed = 0
    start_time = time.time()

    try:
        for i, (listing_id, url) in enumerate(rows, 1):
            try:
                result = parse_detail_page(listing_id, url)
                if result:
                    update_db(conn, result)
                    ok += 1
                else:
                    failed += 1
            except Exception as e:
                log.error(f"[{listing_id}] Lỗi: {e}")
                failed += 1

            if i % 20 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining_mins = ((total - i) * avg_time) / 60
                log.info(f"[{i}/{total}] OK={ok} FAIL={failed} | Ước tính còn: ~{remaining_mins:.1f} phút")

            time.sleep(0.5)

        cursor.execute(
            """
            UPDATE scrape_logs
            SET status          = 'success_enrich',
                rows_inserted   = ?,  
                rows_skipped    = ?  
            WHERE log_id = ?
        """, (ok, failed, log_id))
        conn.commit()

    except KeyboardInterrupt:
        log.warning("Người dùng đã chủ động dừng chương trình (Ctrl+C).")
        cursor.execute(
            "UPDATE scrape_logs SET status = 'stopped_enrich' WHERE log_id = ?", 
            (log_id,)
        )
        conn.commit()

    except Exception as e:
        log.error(f"Enricher gặp lỗi hệ thống: {e}")
        cursor.execute("""
            UPDATE scrape_logs
            SET status = 'failed_enrich',
                error_msg = ?
            WHERE log_id = ?
        """, (str(e)[:500], log_id))
        conn.commit()
        raise

    finally:
        conn.close()
        log.info(f"---------- Kết thúc Enrich | OK = {ok} | FAIL = {failed} ----------")


def main():
    enrich_all()

if __name__ == "__main__":
    main()