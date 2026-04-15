# SaigonPropTech ML — Dự đoán giá thuê phòng trọ TP.HCM

Dự án Machine Learning end-to-end: thu thập dữ liệu tự động từ phongtro123.com → lưu SQL Server → phân tích EDA → train model hồi quy → deploy API dự đoán giá thuê → MLOps tự động cập nhật hàng tuần.

**Demo:** `https://saigon-proptech-production.up.railway.app`

---

## Kết quả mô hình

| Metric | Giá trị | Ý nghĩa |
|---|---|---|
| R² Score | 0.49 | Giải thích ~49% biến động giá |
| MAE | 0.72 triệu | Sai số trung bình ~720k VNĐ  |
| RMSE | 1 triệu | Sai số căn bình phương ~1000k |
| Thuật toán | Random Forest | Vượt qua CatBoost và LightGBM |
| Khoảng tin cậy | ±15% | Dùng làm tham khảo |

---

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Scraping | Python, requests, BeautifulSoup4 |
| Database | SQL Server 2022 (Docker) |
| Geocoding | Nominatim / OpenStreetMap |
| ML | scikit-learn, LightGBM, CatBoost |
| API | FastAPI + uvicorn |
| Frontend | HTML/CSS/JS thuần |
| Deploy | Railway (auto-deploy từ GitHub) |
| MLOps | GitHub Actions (weekly retrain) |
| Container | Docker, Docker Compose |

---

## Cấu trúc dự án

```
saigon_proptech/
├── scraper/
│   ├── phongtro_scraper.py      # Scrape danh sách tin
│   └── detail_scraper.py        # Scrape chi tiết + geocoding
├── database/
│   ├── db_connection.py
│   ├── schema.sql               # Schema v1
│   └── schema_v2.sql            # Schema v2: lat/lng, tiện ích mới
├── models/
│   ├── best_model_v2.pkl        # Model production
│   ├── feature_cols_v2.pkl      # Feature list
│   └── model_metrics_v2.pkl     # Metrics để so sánh
├── api/
│   ├── main_standalone.py       # FastAPI standalone (Railway)
│   └── index.html               # Giao diện HR
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model.ipynb
│   ├── 04_feature_selection.ipynb
│   └── 05_report.ipynb
├── mlops/
│   ├── retrain.py               # Script retrain tự động
│   └── evaluate_and_swap.py     # So sánh model cũ/mới
├── tests/
│   ├── test_parse.py
│   ├── test_db.py
│   └── test_single.py
├── .github/workflows/
│   └── weekly_retrain.yml       # GitHub Actions MLOps
├── Dockerfile
├── Procfile
├── runtime.txt
├── railway.json
├── docker-compose.yml
├── requirements.txt
├── requirements_deploy.txt
└── README.md
```

---

## Feature được chọn và lý do

### Tại sao chỉ dùng 5 tiện ích thay vì 14?

Sau khi phân tích Feature Importance và correlation matrix, nhiều tiện ích bị loại vì:

**Overlap (đã bao gồm trong feature khác):**
- `has_ac`, `has_washer`, `has_fridge` → đã bị capture bởi `is_furnished` (phòng full nội thất = có đủ các thiết bị này). Giữ cả hai gây multicollinearity, nhiễu model.
- `has_wc`, `has_kitchen`, `has_balcony` → importance < 0.01, phần lớn phòng trọ TP.HCM đều có hoặc không đề cập → signal yếu.

**5 feature tiện ích được giữ lại:**

| Feature | Lý do giữ |
|---|---|
| `is_furnished` | Tác động giá rõ nhất (+500k-1tr), ít overlap |
| `has_elevator` | Signal phân khúc cao cấp, ít phòng có |
| `has_basement` | Signal chung cư, tương quan với giá cao |
| `no_owner` | Sự riêng tư → khách chất lượng cao → giá cao |
| `free_hours` | Tương tự no_owner, bổ sung không overlap |

**Feature vị trí và kích thước (quan trọng nhất):**

| Feature | Lý do |
|---|---|
| `lat`, `lng` | Vị trí là yếu tố #1 trong BĐS, liên tục tốt hơn district_id |
| `area_m2` + `log_area` | Quan hệ phi tuyến giữa diện tích và giá |
| `district_id` (one-hot) | Ranh giới hành chính ảnh hưởng hạ tầng |
| `district_tier` | Nhóm quận theo mức giá: cao/trung/bình dân |
| `room_type_enc` | 3 phân khúc giá khác nhau rõ rệt |
| `amenity_count` | Tổng tiện ích — tác động tích lũy |

---

## Hướng dẫn chạy local

### Yêu cầu: Docker Desktop, Git

```bash
git clone https://github.com/your-username/saigon-proptech.git
cd saigon-proptech
cp .env.example .env   # chỉnh DB_PASSWORD

docker-compose build
docker-compose up -d sqlserver
# Đợi 15 giây
docker cp database/schema_v2.sql saigon_proptech-sqlserver-1:/schema_v2.sql
docker exec -it saigon_proptech-sqlserver-1 \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourPass" -C \
  -Q "CREATE DATABASE saigon_proptech;"
docker exec -it saigon_proptech-sqlserver-1 \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourPass" \
  -C -d saigon_proptech -i /schema_v2.sql
```

```bash
# Scrape dữ liệu
docker-compose up scraper
docker-compose up detail_scraper

# Jupyter để train
docker-compose up jupyter   # http://localhost:8888

# API local
docker-compose up api       # http://localhost:8000
```

---
## API Reference

### POST /predict

```json
{
  "address":      "123 Nguyễn Trãi, Phường 2",
  "district_id":  5,
  "area_m2":      25,
  "room_type":    0,
  "is_furnished": 1,
  "has_elevator": 0,
  "has_basement": 0,
  "no_owner":     1,
  "free_hours":   1
}
```

Response:
```json
{
  "price_vnd":     3500000,
  "price_million": 3.5,
  "price_range":   {"low": 2.98, "high": 4.03},
  "district_name": "Quận 5",
  "geocoded":      {"lat": 10.754, "lng": 106.665},
  "note":          "Khoảng giá ±15% do R²=0.41, nên dùng làm tham khảo"
}
```

### GET /health
```json
{"status":"ok","model":"GradientBoostingRegressor v2","r2":0.41,"mae_million":0.69}
```

---

## MLOps — Tự động retrain hàng tuần

Mỗi Chủ Nhật 2:00 AM, GitHub Actions tự động:

1. Chạy `phongtro_scraper.py` → cào data mới
2. Chạy `detail_scraper.py` → enrich chi tiết  
3. Chạy `mlops/retrain.py` → train model mới
4. Chạy `mlops/evaluate_and_swap.py` → so sánh R²
5. Nếu model mới tốt hơn → commit `.pkl` mới → Railway tự deploy

Xem chi tiết: `.github/workflows/weekly_retrain.yml`

---

## Roadmap

- [x] Phase 1 — Scrape danh sách tin đăng
- [x] Phase 1 — SQL Server + Docker
- [x] Phase 2 — EDA + Feature Engineering
- [x] Phase 2 — Scrape chi tiết (address, date, amenities)
- [x] Phase 2 — Geocoding Nominatim
- [x] Phase 3 — Train 5 model, chọn best
- [x] Phase 3 — Feature selection tối ưu
- [x] Phase 4 — FastAPI + giao diện HR
- [x] Phase 4 — Deploy Railway (link 24/7)
- [x] Phase 5 — MLOps: GitHub Actions weekly retrain
- [ ] Phase 6 — Thu thêm data (mục tiêu 3,000+ dòng → R²≥0.60)
- [ ] Phase 6 — Thêm loại phòng chi tiết hơn