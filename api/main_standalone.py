# api/main_standalone.py — v3: LightGBM hoặc CatBoost
import os, sys, numpy as np, pandas as pd, joblib, requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="SaigonPropTech Price Predictor v3")

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")


def load_model():
    """
    Thử load theo thứ tự: v4 champion (Random Forest) -> v3 cbm (CatBoost) -> v2 pkl (fallback)
    """
    path_model_v4 = os.path.join(MODEL_DIR, "best_model_v4_champion.pkl")
    path_feat_v4  = os.path.join(MODEL_DIR, "feature_cols_v4.pkl")
    
    if os.path.exists(path_model_v4) and os.path.exists(path_feat_v4):
        model = joblib.load(path_model_v4)
        feat  = joblib.load(path_feat_v4)
        
        path_metrics_v4 = os.path.join(MODEL_DIR, "model_metrics_v4.pkl")
        if os.path.exists(path_metrics_v4):
            metrics = joblib.load(path_metrics_v4)
        else:
            metrics = {"algorithm": "Random Forest", "r2": 0.4889, "mae": 720000} 
            
        print(f"Loaded: best_model_v4_champion.pkl (R²={metrics.get('r2',0):.4f})")
        return model, feat, metrics, "sklearn"

    path_cbm = os.path.join(MODEL_DIR, "best_model_v3.cbm")
    if os.path.exists(path_cbm):
        from catboost import CatBoostRegressor
        model = CatBoostRegressor()
        model.load_model(path_cbm)
        feat    = joblib.load(os.path.join(MODEL_DIR, "feature_cols_v3.pkl"))
        metrics = joblib.load(os.path.join(MODEL_DIR, "model_metrics_v3.pkl"))
        print(f"Loaded: best_model_v3.cbm (R²={metrics.get('r2',0):.4f})")
        return model, feat, metrics, "catboost"

    model   = joblib.load(os.path.join(MODEL_DIR, "best_model_v2.pkl"))
    feat    = joblib.load(os.path.join(MODEL_DIR, "feature_cols_v2.pkl"))
    metrics = joblib.load(os.path.join(MODEL_DIR, "model_metrics_v2.pkl"))
    print(f"Loaded: best_model_v2.pkl (fallback, R²={metrics.get('r2',0):.4f})")
    return model, feat, metrics, "sklearn"


model, feat_cols, metrics, model_type = load_model()

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

DISTRICT_TIER = {
    **{i: 2 for i in [1,2,3,4,7,16]},
    **{i: 1 for i in [5,6,8,10,13,17,18]},
    **{i: 0 for i in [14,15,19,20,21,22,23,24]},
}


def geocode(address: str, district_id: int) -> tuple[float,float]:
    import unicodedata
    def rm(t):
        return "".join(c for c in unicodedata.normalize("NFD",t)
                       if not unicodedata.combining(c))
    for q in [f"{address}, TP. Ho Chi Minh, Viet Nam",
              rm(f"{address}, TP. Ho Chi Minh, Viet Nam")]:
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q":q,"format":"json","limit":1,"countrycodes":"vn"},
                headers={"User-Agent":"SaigonPropTech/1.0"},
                timeout=5,
            )
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            pass
    return DISTRICT_COORDS.get(district_id, (10.7769,106.7009))


class PredictRequest(BaseModel):
    address:      str
    district_id:  int
    area_m2:      float
    room_type:    int = 0
    is_furnished: int = 0
    has_elevator: int = 0
    has_basement: int = 0
    no_owner:     int = 0
    free_hours:   int = 0


def build_input(req: PredictRequest, lat: float, lng: float) -> pd.DataFrame:
    row = {col: 0 for col in feat_cols}
    row["area_m2"]        = req.area_m2
    row["log_area"]       = np.log1p(req.area_m2)
    row["lat"]            = lat
    row["lng"]            = lng
    row["room_type_enc"]  = req.room_type
    row["district_tier"]  = DISTRICT_TIER.get(req.district_id, 1)
    row["has_furniture"]  = req.is_furnished
    row["has_elevator"]   = req.has_elevator
    row["has_basement"]   = req.has_basement
    row["no_owner"]       = req.no_owner
    row["free_hours"]     = req.free_hours
    row["amenity_count"]  = sum([req.is_furnished, req.has_elevator,
                                 req.has_basement, req.no_owner, req.free_hours])
    q_col = f"q_{req.district_id}"
    if q_col in row:
        row[q_col] = 1
    return pd.DataFrame([row])[feat_cols]


@app.post("/predict")
def predict(req: PredictRequest):
    lat, lng = geocode(req.address, req.district_id)
    X        = build_input(req, lat, lng)
    price    = np.expm1(model.predict(X)[0])

    return {
        "price_vnd":     int(price),
        "price_million": round(price/1e6, 2),
        "price_range": {
            "low":  round(price*0.85/1e6, 2),
            "high": round(price*1.15/1e6, 2),
        },
        "district_name": DISTRICT_MAP.get(req.district_id,""),
        "geocoded":      {"lat": round(lat,6), "lng": round(lng,6)},
        "model":         metrics.get("algorithm","GBR"),
        "note":          f"Khoảng giá ±15% · R²={metrics.get('r2',0):.2f}",
    }


@app.get("/health")
def health():
    return {
        "status":      "ok",
        "algorithm":   metrics.get("algorithm","unknown"),
        "model_type":  model_type,
        "r2":          round(metrics.get("r2",0), 4),
        "mae_million": round(metrics.get("mae",0)/1e6, 2),
        "n_features":  len(feat_cols),
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return open(
        os.path.join(os.path.dirname(__file__), "index.html"),
        encoding="utf-8"
    ).read()