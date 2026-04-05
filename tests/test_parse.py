import sys , os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.phongtro_scraper import parse_price, parse_area, parse_district

print("---TEST parse_price---")

cases_price = [
    ("2.5 triệu/tháng", 2_500_000),
    ("2,5 triệu/tháng",   2_500_000),
    ("1.500.000đ/tháng",  1_500_000),
    ("Thỏa thuận",        None),
    ("",                  None),
    ("3 triệu",           3_000_000),
]
for input_val, expected in cases_price:
    result = parse_price(input_val)
    status = f"\033[92mOK\033[0m" if result == expected else f"\033[91mFAIL\033[0m (got {result})"
    print (f"   [{status} '{input_val}' -> {result}]")

print("\n=== TEST parse_area ===")
cases_area = [
    ("25 m²",        25.0),
    ("30m2",         30.0),
    ("25m²",      25.0),
    ("khoảng 18m2",  18.0),
    ("",             None),
]
for input_val, expected in cases_area:
    result = parse_area(input_val)
    status = "\033[92mOK\033[0m" if result == expected else f"\033[91mFAIL\033[0m (got {result})"
    print(f"  [{status}]  '{input_val}' → {result}")

print("\n=== TEST parse_district ===")
cases_district = [
    ("123 Nguyễn Trãi, Quận 5, TP.HCM",  5),
    ("Phòng trọ Bình Thạnh giá rẻ",       13),
    ("Q7, đường Huỳnh Tấn Phát",         7),
    ("không có quận nào",                 None),
]
for input_val, expected in cases_district:
    result = parse_district(input_val)
    status = "\033[92mOK\033[0m" if result == expected else f"\033[91mFAIL\033[0m (got {result})"
    print(f"  [{status}]  '{input_val}' → {result}")