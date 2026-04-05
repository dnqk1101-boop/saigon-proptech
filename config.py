import os
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER", "sqlserver")
DB_NAME = os.getenv("DB_NAME", "SaigonPropTech")
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "KienDo11@")

SCRAPER_DELAY = int(os.getenv("SCRAPER_DELAY", 5))
MAX_PAGES = int(os.getenv("MAX_PAGES", 50))

RAW_DATA_PATH = os.path.join("data", "raw", "listing.csv") 
