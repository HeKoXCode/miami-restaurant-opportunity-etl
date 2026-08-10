from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

# Las rutas viven en un solo lugar para que ningún módulo dependa
# de la carpeta desde la que se ejecuta el comando.
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
FINAL_DIR = DATA_DIR / "final"
REFERENCE_DIR = DATA_DIR / "reference"

DOCS_DIR = BASE_DIR / "docs"

CUSTOMERS_RAW = RAW_DIR / "customers_raw.csv"
CUSTOMERS_CLEAN = CLEAN_DIR / "customers_clean.csv"
CUSTOMERS_MIAMI = FINAL_DIR / "customers_miami.csv"
CUSTOMER_VALUE_MIAMI = FINAL_DIR / "customer_value_miami.csv"

YELP_RAW = RAW_DIR / "yelp_restaurants_raw.csv"
YELP_CLEAN = CLEAN_DIR / "yelp_restaurants_clean.csv"

CATEGORY_MAPPING = REFERENCE_DIR / "category_mapping.csv"
PREFERENCE_OPPORTUNITY_MIAMI = FINAL_DIR / "preference_opportunity_miami.csv"

DATA_QUALITY_REPORT_CSV = DOCS_DIR / "data_quality_report.csv"
DATA_QUALITY_REPORT_MD = DOCS_DIR / "data_quality_report.md"
YELP_EXTRACTION_METADATA = DOCS_DIR / "yelp_extraction_metadata.json"

TARGET_CITY = "Miami"
YELP_ALLOWED_CITIES = [TARGET_CITY]

# Reglas simples que el equipo puede revisar sin buscar dentro del ETL.
VALID_AGE_MIN = 18
VALID_AGE_MAX = 90
ESTRATOS = ["Bajo", "Medio", "Alto", "Muy Alto"]

TRANSACTION_ORDER = ["delivery", "pickup", "restaurant_reservation"]
QUALITY_SCORE_MIN_REVIEWS = 100

COVERAGE_GAP_THRESHOLD = 1.25
COVERAGE_WIDE_THRESHOLD = 0.75
PREFERENCE_LOW_CONFIDENCE_THRESHOLD = 0.20
PREFERENCE_MEDIUM_CONFIDENCE_THRESHOLD = 0.05

PREFERENCE_FILL_VALUE = "Otro"
MISSING_TEXT_VALUE = "Sin dato"
PII_COLUMNS = [
    "nombre",
    "apellido",
    "telefono_contacto",
    "correo_electronico",
]


def ensure_dirs() -> None:
    for path in [
        RAW_DIR,
        CLEAN_DIR,
        FINAL_DIR,
        REFERENCE_DIR,
        DOCS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)
