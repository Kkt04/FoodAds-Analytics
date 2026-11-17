"""Central place for paths and project-wide constants."""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "foodads.db"
SQL_DIR = ROOT / "sql"
MONGO_DIR = ROOT / "mongo"

OUT_DIR = ROOT / "outputs"
TABLE_DIR = OUT_DIR / "tables"
CHART_DIR = OUT_DIR / "charts"
REPORT_DIR = OUT_DIR / "reports"

DEFAULT_SEED = 42
DEFAULT_ADVERTISERS = 300

# MongoDB settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "foodads")

# Business thresholds used in queries / reports
FIX_THRESHOLD = 0.70    # segment ROAS < 70% of overall ROAS  -> "FIX"
GROW_THRESHOLD = 1.20   # segment ROAS > 120% of overall ROAS -> "GROW"


def ensure_dirs() -> None:
    for d in (DATA_DIR, TABLE_DIR, CHART_DIR, REPORT_DIR, MONGO_DIR):
        d.mkdir(parents=True, exist_ok=True)
