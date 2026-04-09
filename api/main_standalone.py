# api/main_standalone.py
# Version standalone cho Railway deploy — không cần SQL Server
import os, sys
import numpy as np
import pandas as pd
import joblib
import requests
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="SaigonPropTech Price Predictor")

# Load model từ thư mục models/
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

model     = joblib.load(os.path.join(MODEL_DIR, "best_model_v2.pkl"))
feat_cols = joblib.load(os.path.join(MODEL_DIR, "feature_cols_v2.pkl"))
metrics   = joblib.load(os.path.join(MODEL_DIR, "model_metrics_v2.pkl"))

DISTRICT_MAP = {
    1:"Quận 1",    2:"Quận 2",    3:"Quận 3",    4:"Quận 4",
    5:"Quận 5",    6:"Quận 6",    7:"Quận 7",    8:"Quận 8",
    9:"Quận 9",    10:"Quận 10",  11:"Quận 11",  12:"Quận 12",
    13:"Bình Thạnh",14:"Bình Tân",15:"Gò Vấp",   16:"Phú Nhuận",
    17:"Tân Bình", 18:"Tân Phú",  19:"Thủ Đức",  20:"Bình Chánh",
    21:"Hóc Môn",  22:"Nhà Bè",   23:"Cần Giờ",  24:"Củ Chi",
}

DISTRICT_COORDS = {
    1:(10.7769,106.7009), 2:(10.7872,106.7519), 3:(10.7794,106.6880),
    4:(10.7580,106.7040), 5:(10.7540,106.6650), 6:(10.7456,106.6342),
    7:(10.7324,106.7218), 8:(10.7239,106.6282), 9:(10.8414,106.7897),
    10:(10.7728,106.6667),11:(10.7634,106.6489),12:(10.8682,106.6447),
    13:(10.8121,106.7125),14:(10.7641,106.6086),15:(10.8385,106.6659),
    16:(10.7995,106.6799),17:(10.8013,106.6525),18:(10.7901,106.6281),
    19:(10.8588,106.7594),20:(10.6880,106.6100),21:(10.8911,106.5958),
    22:(10.6997,106.7370),23:(10.4113,106.9531),24:(10.9767,106.4956),
}


def geocode(address: str, district_id: int) -> tuple[float, float]:
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{address}, TP. Ho Chi Minh, Viet Nam",
                    "format": "json", "limit": 1, "countrycodes": "vn"},
            headers={"User-Agent": "SaigonPropTech/1.0"},
            timeout=5,
        )
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return DISTRICT_COORDS.get(district_id, (10.7769, 106.7009))


class PredictRequest(BaseModel):
    address:       str
    district_id:   int
    area_m2:       float
    room_type:     int = 0
    has_ac:        int = 0
    has_wc:        int = 0
    has_furniture: int = 0
    has_kitchen:   int = 0
    has_washer:    int = 0
    has_fridge:    int = 0
    has_elevator:  int = 0
    has_basement:  int = 0
    has_balcony:   int = 0
    has_security:  int = 0
    has_parking:   int = 0
    no_owner:      int = 0
    free_hours:    int = 0


@app.post("/predict")
def predict(req: PredictRequest):
    lat, lng = geocode(req.address, req.district_id)

    row = {col: 0 for col in feat_cols}
    row["area_m2"]       = req.area_m2
    row["log_area"]      = np.log1p(req.area_m2)
    row["lat"]           = lat
    row["lng"]           = lng
    row["room_type_enc"] = req.room_type
    row["has_ac"]        = req.has_ac
    row["has_wc"]        = req.has_wc
    row["has_furniture"] = req.has_furniture
    row["has_kitchen"]   = req.has_kitchen
    row["has_washer"]    = req.has_washer
    row["has_fridge"]    = req.has_fridge
    row["has_elevator"]  = req.has_elevator
    row["has_basement"]  = req.has_basement
    row["has_balcony"]   = req.has_balcony
    row["has_security"]  = req.has_security
    row["has_parking"]   = req.has_parking
    row["no_owner"]      = req.no_owner
    row["free_hours"]    = req.free_hours
    row["amenity_count"] = sum([
        req.has_ac, req.has_wc, req.has_furniture, req.has_kitchen,
        req.has_washer, req.has_fridge, req.has_elevator,
        req.has_basement, req.has_balcony, req.has_security, req.has_parking,
    ])
    q_col = f"q_{req.district_id}"
    if q_col in row:
        row[q_col] = 1

    X        = pd.DataFrame([row])[feat_cols]
    price    = np.expm1(model.predict(X)[0])

    return {
        "price_vnd":     int(price),
        "price_million": round(price / 1e6, 2),
        "price_range": {
            "low":  round(price * 0.85 / 1e6, 2),
            "high": round(price * 1.15 / 1e6, 2),
        },
        "district_name": DISTRICT_MAP.get(req.district_id, ""),
        "geocoded": {"lat": round(lat, 6), "lng": round(lng, 6)},
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model":  "GradientBoostingRegressor v2",
        "r2":     round(metrics["r2"], 4),
        "mae_million": round(metrics["mae"] / 1e6, 2),
    }


@app.get("/", response_class=HTMLResponse)
def index():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    return open(html_path, encoding="utf-8").read()