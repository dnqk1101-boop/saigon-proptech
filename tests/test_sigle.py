import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.detail_scraper import parse_detail_page 


def test_one(url: str):
    print(f"Testing: {url}\n")
    
    result = parse_detail_page(0, url) 
    
    if result:
        result_display = {k: v for k, v in result.items() if k != "features"}
        
        print("=== THÔNG TIN CHÍNH ===")
        for k, v in result_display.items():
            print(f"  {k:20} = {v}")
            
        print("\n=== TIỆN ÍCH ===")
        # In riêng phần features cho dễ nhìn
        if "features" in result:
            for k, v in result["features"].items():
                status = "CÓ" if v else "---"
                print(f"  {k:20} = {status}")
    else:
        print("FAIL: không parse được")


if __name__ == "__main__":
    test_link = "https://phongtro123.com/phong-gan-cho-thu-duc-full-noi-that-moi-xay-ngay-duong-pham-van-dong-pr672616.html"
    
    print("🚀 Đang khởi động bộ test độc lập...")
    test_one(test_link)