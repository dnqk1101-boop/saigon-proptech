import sys, os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.phongtro_scraper import scrape_page
import json

print("=== TEST scrape trang 1 ===")
listings = scrape_page(1)

if not listings:
    print("\033[91m[FAIL] Khong scrape duoc gi")
    print("Kiem tra lai cac CSS Selector\033[0m")

else:
    print(f"\033[92mOK Scrape được {len(listings)} listings\n\033[0m")

    for i, item in enumerate(listings[:2], 1):
        print(f"--- Listing #{i} ---")
        for key, val in item.items():
            print(f"    {key:15} = {val}")
        print()

    print("=== THỐNG KÊ CHẤT LƯỢNG ===")
    total = len(listings)
    has_price    = sum(1 for x in listings if x.get("price_vnd"))
    has_area     = sum(1 for x in listings if x.get("area_m2"))
    has_district = sum(1 for x in listings if x.get("district_id"))
    has_url      = sum(1 for x in listings if x.get("source_url"))

    print(f"  Tổng listings    : {total}")
    print(f"  Có price_vnd     : {has_price}/{total} ({has_price/total*100:.0f}%)")
    print(f"  Có area_m2       : {has_area}/{total} ({has_area/total*100:.0f}%)")
    print(f"  Có district_id   : {has_district}/{total} ({has_district/total*100:.0f}%)")
    print(f"  Có source_url    : {has_url}/{total} ({has_url/total*100:.0f}%)")

    if has_price / total < 0.5:
        print("\n[!] price_vnd thấp → kiểm tra lại selector .price")
    if has_district / total < 0.5:
        print("[!] district_id thấp → địa chỉ parse không được, kiểm tra selector .address")
