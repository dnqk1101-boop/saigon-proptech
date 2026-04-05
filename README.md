# SaigonPropTech ML — Dự đoán giá thuê phòng trọ TP.HCM

Dự án Machine Learning xây dựng mô hình hồi quy (Regression) để dự đoán giá thuê phòng trọ tại TP.HCM dựa trên diện tích, vị trí và tiện ích.

---

## Mục tiêu

- Thu thập dữ liệu phòng trọ từ [phongtro123.com](https://phongtro123.com) bằng Web Scraping
- Lưu trữ và quản lý dữ liệu bằng SQL Server
- Phân tích khám phá dữ liệu (EDA) để hiểu phân phối giá theo quận, diện tích, tiện ích
- Xây dựng mô hình ML dự đoán giá thuê
- Triển khai API dự đoán bằng FastAPI

---

## Tech Stack

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python 3.11 |
| Web Scraping | `requests`, `BeautifulSoup4` |
| Database | SQL Server 2022 |
| DB Driver | `pyodbc`, ODBC Driver 18 |
| EDA & ML | `pandas`, `matplotlib`, `seaborn`, `scikit-learn` |
| Containerization | Docker, Docker Compose |
| Version Control | Git, GitHub |

---

## Cấu trúc dự án

```
saigon_proptech/
├── scraper/
│   ├── __init__.py
│   └── phongtro_scraper.py     # Web scraper chính
├── database/
│   ├── __init__.py
│   ├── db_connection.py        # Kết nối SQL Server
│   └── schema.sql              # Schema database
├── models/
│   ├── train.py                # Train mô hình ML
│   └── predict.py              # Dự đoán giá
├── notebooks/
│   ├── 01_eda.ipynb            # Phân tích khám phá dữ liệu
│   └── 02_model.ipynb          # Xây dựng và đánh giá model
├── tests/
│   ├── test_parse.py           # Test hàm parse
│   ├── test_db.py              # Test kết nối database
│   └── test_scrape.py          # Test scraper
├── data/
│   ├── raw/                    # Dữ liệu thô (gitignore)
│   └── processed/              # Dữ liệu đã xử lý (gitignore)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.py                   # Cấu hình chung
├── .env                        # Biến môi trường (gitignore)
├── .gitignore
└── README.md
```

---

## Yêu cầu hệ thống

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) >= 4.0
- [Git](https://git-scm.com/)
- Không cần cài Python hay SQL Server trực tiếp — Docker lo hết

---

## Hướng dẫn chạy

### 1. Clone dự án

```bash
git clone https://github.com/your-username/saigon-proptech.git
cd saigon-proptech
```

### 2. Tạo file `.env`

```bash
cp .env.example .env
```

Chỉnh sửa `.env`:

```env
DB_SERVER=sqlserver
DB_NAME=saigon_proptech
DB_USER=sa
DB_PASSWORD=YourStrongPassword123
```

> Lưu ý: `DB_PASSWORD` phải có ít nhất 8 ký tự, gồm chữ hoa, chữ thường và số — yêu cầu của SQL Server.

### 3. Build và khởi động

```bash
docker-compose build
docker-compose up -d sqlserver   # Khởi động SQL Server trước
```

### 4. Tạo database và chạy schema

```bash
# Đợi SQL Server sẵn sàng (~15 giây) rồi chạy
docker exec -it saigon_proptech-sqlserver-1 \
  /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "YourStrongPassword123" -C \
  -Q "CREATE DATABASE saigon_proptech;"

docker cp database/schema.sql saigon_proptech-sqlserver-1:/schema.sql

docker exec -it saigon_proptech-sqlserver-1 \
  /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "YourStrongPassword123" -C \
  -i /schema.sql
```

### 5. Chạy scraper

```bash
# Chạy thật (50 trang)
docker-compose up scraper

# Chạy thử nhanh (3 trang)
docker-compose run --rm -e TEST_MODE=1 scraper python scraper/phongtro_scraper.py
```

### 6. Mở Jupyter để phân tích

```bash
docker-compose up jupyter
# Mở trình duyệt: http://localhost:8888
```

### 7. Xem log scraper

```bash
docker-compose logs -f scraper
```

---

## Kiểm tra dữ liệu đã thu thập

```bash
docker exec -it saigon_proptech-sqlserver-1 \
  /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "YourStrongPassword123" -C \
  -Q "
    SELECT COUNT(*) AS tong_listings FROM saigon_proptech.dbo.listings;
    SELECT TOP 5 title, price_vnd, area_m2, district_id
    FROM saigon_proptech.dbo.listings
    ORDER BY scraped_at DESC;
  "
```

---

## Schema Database

```
listings          — Bảng tin đăng chính
listing_features  — Tiện ích (điều hòa, bếp, bảo vệ...)
districts         — Danh sách quận/huyện TP.HCM (24 quận)
scrape_logs       — Lịch sử mỗi lần chạy scraper
ml_features       — VIEW tổng hợp sẵn sàng cho ML
```

---

## Biến môi trường

| Biến | Mô tả | Mặc định |
|---|---|---|
| `DB_SERVER` | Hostname SQL Server | `sqlserver` |
| `DB_NAME` | Tên database | `saigon_proptech` |
| `DB_USER` | Username | `sa` |
| `DB_PASSWORD` | Mật khẩu SA | _(bắt buộc)_ |
| `TEST_MODE` | Chạy nhanh 3 trang | `0` |

---

## Roadmap

- [x] Phase 1 — Thu thập dữ liệu (Web Scraping)
- [x] Phase 1 — Lưu trữ SQL Server
- [x] Phase 1 — Docker & GitHub setup
- [ ] Phase 2 — EDA (Exploratory Data Analysis)
- [ ] Phase 3 — Feature Engineering
- [ ] Phase 4 — Xây dựng mô hình Regression
- [ ] Phase 5 — Deploy API dự đoán giá

---

## Lưu ý pháp lý

Dự án này chỉ dùng cho mục đích học tập và nghiên cứu. Dữ liệu được thu thập tuân thủ `robots.txt` của website và có delay giữa các request để không ảnh hưởng đến server.

---

## Tác giả

Dự án thực hành Data Engineering & Machine Learning — SaigonPropTech
