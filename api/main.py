from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import joblib, numpy as np, requests, time, os, sys

sys.path.append('/app')

app = FastAPI(title="SaigonPropTech Price Predictor")

# Load model khi khởi động
model    = joblib.load("/app/models/best_model_v2.pkl")
feat_cols = joblib.load("/app/models/feature_cols_v2.pkl")

DISTRICT_MAP = {
    1:"Quận 1", 2:"Quận 2", 3:"Quận 3", 4:"Quận 4",
    5:"Quận 5", 6:"Quận 6", 7:"Quận 7", 8:"Quận 8",
    9:"Quận 9", 10:"Quận 10", 11:"Quận 11", 12:"Quận 12",
    13:"Bình Thạnh", 14:"Bình Tân", 15:"Gò Vấp",
    16:"Phú Nhuận", 17:"Tân Bình", 18:"Tân Phú",
    19:"Thủ Đức", 20:"Bình Chánh", 21:"Hóc Môn",
    22:"Nhà Bè", 23:"Cần Giờ", 24:"Củ Chi",
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
            params={"q": f"{address}, Việt Nam",
                    "format": "json", "limit": 1, "countrycodes": "vn"},
            headers={"User-Agent": "SaigonPropTech/1.0"},
            timeout=5,
        )
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    # Fallback về tọa độ quận
    return DISTRICT_COORDS.get(district_id, (10.7769, 106.7009))


class PredictRequest(BaseModel):
    address:      str
    district_id:  int
    area_m2:      float
    has_ac:       int = 0
    has_wc:       int = 0
    has_furniture:int = 0
    has_kitchen:  int = 0
    has_washer:   int = 0
    has_fridge:   int = 0
    has_elevator: int = 0
    has_basement: int = 0
    has_balcony:  int = 0
    has_security: int = 0
    has_parking:  int = 0
    no_owner:     int = 0
    free_hours:   int = 0


@app.post("/predict")
def predict(req: PredictRequest):
    lat, lng = geocode(req.address, req.district_id)

    input_df = {col: 0 for col in feat_cols}

    input_df["area_m2"]       = req.area_m2
    input_df["log_area"]      = np.log1p(req.area_m2)
    input_df["lat"]           = lat
    input_df["lng"]           = lng
    input_df["has_ac"]        = req.has_ac
    input_df["has_wc"]        = req.has_wc
    input_df["has_furniture"] = req.has_furniture
    input_df["has_kitchen"]   = req.has_kitchen
    input_df["has_washer"]    = req.has_washer
    input_df["has_fridge"]    = req.has_fridge
    input_df["has_elevator"]  = req.has_elevator
    input_df["has_basement"]  = req.has_basement
    input_df["has_balcony"]   = req.has_balcony
    input_df["has_security"]  = req.has_security
    input_df["has_parking"]   = req.has_parking
    input_df["no_owner"]      = req.no_owner
    input_df["free_hours"]    = req.free_hours
    input_df["amenity_count"] = sum([
        req.has_ac, req.has_wc, req.has_furniture, req.has_kitchen,
        req.has_washer, req.has_fridge, req.has_elevator, req.has_basement,
        req.has_balcony, req.has_security, req.has_parking,
    ])

    # One-hot quận
    q_col = f"q_{req.district_id}"
    if q_col in input_df:
        input_df[q_col] = 1

    import pandas as pd
    X = pd.DataFrame([input_df])[feat_cols]
    log_pred = model.predict(X)[0]
    price    = np.expm1(log_pred)

    return {
        "price_vnd":      int(price),
        "price_million":  round(price / 1e6, 2),
        "price_range": {
            "low":  round((price * 0.85) / 1e6, 2),
            "high": round((price * 1.15) / 1e6, 2),
        },
        "district_name": DISTRICT_MAP.get(req.district_id, "Không rõ"),
        "geocoded":      {"lat": lat, "lng": lng},
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return open("/app/api/index.html", encoding="utf-8").read()