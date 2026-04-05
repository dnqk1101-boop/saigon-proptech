import os
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER", "KienDo")
DB_NAME = os.getenv("DB_NAME", "SaigonPropTech")
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD","123123")

SCRAPER_DELAY = 5
MAX_PAGES = 50
RAW_DATA_PATH = "data\raw\listing.csv"
