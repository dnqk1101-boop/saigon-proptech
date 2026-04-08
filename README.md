# SaigonPropTech ML — Dự đoán giá thuê phòng trọ TP.HCM

Dự án Machine Learning xây dựng mô hình hồi quy (Regression) để dự đoán giá thuê phòng trọ tại TP.HCM. Dữ liệu được thu thập tự động từ phongtro123.com, lưu trữ SQL Server, phân tích bằng pandas và triển khai API dự đoán bằng FastAPI.

---

## Kết quả mô hình

| Metric | Giá trị | Ý nghĩa |
|--------|---------|---------|
| R² Score | 0.41 | Giải thích được 41% sự biến động giá |
| MAE | 0.69 triệu | Sai số trung bình ~690,000 VNĐ |
| RMSE | 0.99 triệu | Sai số căn bình phương ~990,000 VNĐ |
| Thuật toán | Gradient Boosting | Tốt nhất trong 4 model thử nghiệm |

> Khoảng dự đoán thực tế: giá dự đoán ± 15%

---

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.11 |
| Web Scraping | `requests`, `BeautifulSoup4` |
| Database | SQL Server 2022 |
| DB Driver | `pyodbc`, ODBC Driver 18 |
| Geocoding | Nominatim (OpenStreetMap) |
| EDA & ML | `pandas`, `matplotlib`, `seaborn`, `scikit-learn` |
| API | FastAPI + uvicorn |
| Containerization | Docker, Docker Compose |
| Deploy | Railway (link sống 24/7) |
| Version Control | Git, GitHub |

---

## Cấu trúc dự án

```
saigon_proptech/
├── scraper/
│   ├── phongtro_scraper.py      # Scrape danh sách tin đăng
│   └── detail_scraper.py        # Scrape chi tiết + geocoding
├── database/
│   ├── db_connection.py         # Kết nối SQL Server
│   ├── schema.sql               # Schema v1
│   └── schema_v2.sql            # Schema v2: thêm cột mới
├── models/
│   ├── best_model_v2.pkl        # Model đã train
│   ├── feature_cols_v2.pkl      # Danh sách feature
│   └── model_metrics_v2.pkl     # Metrics đánh giá
├── api/
│   ├── main.py                  # API với DB (local)
│   ├── main_standalone.py       # API standalone (Railway deploy)
│   └── index.html               # Giao diện HR
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model.ipynb
│   ├── 04_feature_selection.ipynb
│   └── 05_report.ipynb
├── tests/
│   ├── test_parse.py
│   ├── test_db.py
│   ├── test_scrape.py
│   └── test_single.py
├── data/
│   ├── raw/                     # Dữ liệu thô (gitignore)
│   ├── processed/               # Dữ liệu đã xử lý (gitignore)
│   └── reports/                 # HTML report
├── Dockerfile
├── Procfile                     # Railway deploy config
├── runtime.txt                  # Python version cho Railway
├── docker-compose.yml
├── requirements.txt             # Dev + training dependencies
├── requirements_deploy.txt      # Production API only
├── config.py
├── .env                         # Biến môi trường (gitignore)
└── README.md
```

---

## Tại sao chọn những feature này?

### Feature quan trọng nhất (từ Gradient Boosting importance)

**1. lat / lng — Tọa độ địa lý**
Vị trí là yếu tố quyết định nhất trong bất động sản. Cùng diện tích nhưng Quận 1 có thể đắt gấp 2-3 lần Bình Chánh. Tọa độ liên tục (float) tốt hơn district_id (integer) vì nắm bắt được sự chênh lệch ngay cả trong cùng một quận — ví dụ mặt tiền vs hẻm sâu trong Quận 7.

**2. area_m2 + log_area — Diện tích**
Diện tích tương quan trực tiếp với giá. Dùng `log_area` thay vì `area_m2` thô vì giá không tăng tuyến tính theo diện tích — phòng 50m² không đắt gấp đôi phòng 25m².

**3. district_id (one-hot) — Quận/Huyện**
Bổ sung cho lat/lng: phân biệt rõ ranh giới hành chính ảnh hưởng đến hạ tầng, tiện ích xung quanh, an ninh. One-hot encoding thay vì integer vì các quận không có thứ tự tuyến tính.

**4. has_furniture — Nội thất đầy đủ**
Phòng có nội thất thường cao hơn 500k-1tr/tháng so với phòng trống. Đây là feature boolean có tác động lớn và rõ ràng nhất trong nhóm tiện ích.

**5. has_ac — Máy lạnh**
Tại TP.HCM khí hậu nóng ẩm, máy lạnh là tiện ích được định giá cao. Phòng có máy lạnh thường đắt hơn 300-500k/tháng.

**6. room_type_enc — Loại phòng**
Phân biệt phòng trọ đơn giản, căn hộ dịch vụ, và nhà nguyên căn — ba phân khúc giá khác nhau rõ rệt. Encode thứ tự vì có tương quan tuyến tính nhất định với giá.

**7. amenity_count — Tổng số tiện ích**
Feature tổng hợp đếm số tiện ích có của mỗi phòng. Phòng có càng nhiều tiện ích thường giá càng cao — capture được tác động tích lũy khi kết hợp nhiều tiện ích.

**8. has_elevator, has_basement — Thang máy, hầm xe**
Hai tiện ích này thường chỉ có ở chung cư cao cấp hoặc nhà mặt phố — signal mạnh cho phân khúc giá cao.

**9. no_owner — Không chung chủ**
Phòng không chung chủ thường có giá cao hơn vì sự riêng tư, tự do và tiện nghi tốt hơn. Feature này capture được sự khác biệt giữa nhà trọ truyền thống và căn hộ độc lập.

**10. free_hours — Giờ giấc tự do**
Tương tự no_owner, signal cho phòng chất lượng cao hơn nhắm vào nhóm khách thuê có thu nhập ổn định.

### Feature bị loại và lý do

| Feature | Lý do loại |
|---|---|
| `floor_number` | 100% null — không có dữ liệu |
| `price_per_m2` | Data leakage — chứa thông tin giá |
| `scraped_at` | Không ảnh hưởng đến giá |
| `has_loft` | Importance < 0.01, ít tin có gác |

---

## Hướng dẫn chạy local

### Yêu cầu
- Docker Desktop >= 4.0
- Git

### 1. Clone và setup

```bash
git clone https://github.com/your-username/saigon-proptech.git
cd saigon-proptech
cp .env.example .env
# Chỉnh DB_PASSWORD trong .env
```

### 2. Khởi động

```bash
docker-compose build
docker-compose up -d sqlserver
# Đợi 15 giây rồi chạy schema
docker cp database/schema.sql saigon_proptech-sqlserver-1:/schema.sql
docker exec -it saigon_proptech-sqlserver-1 \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourPass" -C \
  -Q "CREATE DATABASE saigon_proptech;"
docker exec -it saigon_proptech-sqlserver-1 \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "YourPass" \
  -C -d saigon_proptech -i /schema.sql
```

### 3. Scrape dữ liệu

```bash
# Scrape danh sách
docker-compose up scraper

# Scrape chi tiết (địa chỉ đầy đủ, tiện ích, ngày đăng)
docker-compose up detail_scraper
```

### 4. Phân tích và train model

```bash
docker-compose up jupyter
# Mở http://localhost:8888
# Chạy lần lượt: 01_eda → 02_feature_engineering → 03_model → 04_feature_selection → 05_report
```

### 5. Chạy API local

```bash
docker-compose up api
# Mở http://localhost:8000
```

---

## Deploy lên Railway (link công khai)

### 1. Chuẩn bị

```bash
# Đảm bảo file này tồn tại
ls models/best_model_v2.pkl
ls models/feature_cols_v2.pkl
ls models/model_metrics_v2.pkl
ls Procfile
ls runtime.txt
ls requirements_deploy.txt
```

### 2. Deploy

1. Vào [railway.app](https://railway.app) → đăng nhập bằng GitHub
2. Chọn **New Project** → **Deploy from GitHub repo**
3. Chọn repo `saigon-proptech`
4. Railway tự detect `Procfile` và build
5. Vào **Settings** → **Networking** → **Generate Domain**
6. Link dạng: `https://saigon-proptech-production.up.railway.app`

### 3. Kiểm tra

```bash
# Health check
curl https://your-app.up.railway.app/health

# Test predict
curl -X POST https://your-app.up.railway.app/predict \
  -H "Content-Type: application/json" \
  -d '{"address":"123 Nguyen Trai","district_id":5,"area_m2":25,"has_ac":1,"has_wc":1}'
```

---

## API Reference

### `POST /predict`

**Request body:**

```json
{
  "address":       "123 Nguyễn Trãi, Phường 2",
  "district_id":   5,
  "area_m2":       25,
  "room_type":     0,
  "has_ac":        1,
  "has_wc":        1,
  "has_furniture": 0,
  "has_kitchen":   1,
  "has_washer":    0,
  "has_fridge":    0,
  "has_elevator":  0,
  "has_basement":  0,
  "has_balcony":   0,
  "has_security":  1,
  "has_parking":   1,
  "no_owner":      0,
  "free_hours":    1
}
```

**Response:**

```json
{
  "price_vnd":     3500000,
  "price_million": 3.5,
  "price_range":   {"low": 2.98, "high": 4.03},
  "district_name": "Quận 5",
  "geocoded":      {"lat": 10.754, "lng": 106.665}
}
```

### `GET /health`

```json
{
  "status":      "ok",
  "model":       "GradientBoostingRegressor v2",
  "r2":          0.4115,
  "mae_million": 0.69
}
```

---

## Schema Database

### Bảng chính

| Bảng | Mô tả |
|---|---|
| `listings` | Tin đăng chính — giá, diện tích, địa chỉ, tọa độ, loại phòng |
| `listing_features` | 14 tiện ích chi tiết của từng tin |
| `districts` | 24 quận/huyện TP.HCM với tọa độ trung tâm |
| `scrape_logs` | Lịch sử mỗi lần chạy scraper |
| `ml_features` | VIEW tổng hợp sẵn sàng cho ML |

### Thay đổi Schema v2

**Thêm vào `listings`:**
- `address_full` — địa chỉ đầy đủ đến phường (từ trang chi tiết)
- `lat`, `lng` — tọa độ từ Nominatim geocoding
- `room_type` — loại phòng chính xác
- `posted_at_raw` — ngày đăng tin

**Thêm vào `listing_features`:**
- `has_furniture` — nội thất đầy đủ
- `has_loft` — có gác
- `has_washer` — máy giặt
- `has_fridge` — tủ lạnh
- `has_elevator` — thang máy
- `has_basement` — hầm để xe
- `free_hours` — giờ giấc tự do
- `no_owner` — không chung chủ

---

## Roadmap

- [x] Phase 1 — Thu thập dữ liệu (Web Scraping danh sách)
- [x] Phase 1 — Lưu trữ SQL Server
- [x] Phase 1 — Docker & GitHub setup
- [x] Phase 2 — EDA (Exploratory Data Analysis)
- [x] Phase 2 — Scrape chi tiết: địa chỉ, tiện ích, ngày đăng
- [x] Phase 2 — Geocoding địa chỉ → tọa độ (Nominatim)
- [x] Phase 3 — Feature Engineering
- [x] Phase 4 — Xây dựng và so sánh 4 mô hình Regression
- [x] Phase 4 — Feature selection + train model v2
- [x] Phase 4 — Báo cáo HTML tự động
- [x] Phase 5 — FastAPI + giao diện HR
- [x] Phase 5 — Deploy Railway (link công khai)
- [ ] Phase 6 — Thu thập thêm data (mục tiêu 3,000+ dòng)
- [ ] Phase 6 — Cải thiện R² lên 0.60+

---

## Lưu ý

- Model dự đoán tốt nhất cho phòng trọ 6-80m², giá 500k-20tr/tháng tại TP.HCM
- Khoảng tin cậy ±15% do R² = 0.41
- Dữ liệu train: ~1100 tin đăng — độ chính xác sẽ tăng khi có thêm data
- Geocoding dùng Nominatim miễn phí — có thể chậm 1-2 giây khi predict

---

## Tác giả
KienDo

