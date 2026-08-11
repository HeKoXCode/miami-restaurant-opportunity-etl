from dataclasses import dataclass
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

DATA_QUALITY_REPORT_CSV = FINAL_DIR / "data_quality_report.csv"
DATA_REJECTIONS_CSV = FINAL_DIR / "data_rejections.csv"
DATA_QUALITY_REPORT_MD = DOCS_DIR / "data_quality_report.md"
YELP_EXTRACTION_METADATA = DOCS_DIR / "yelp_extraction_metadata.json"

DEMO_DIR = DATA_DIR / "demo"
DEMO_DEFAULT_ROWS = 750
DEMO_DEFAULT_SEED = 20260713
SCHEMA_VERSION = "1.0.0"

TARGET_CITY = "Miami"
YELP_ALLOWED_CITIES = [TARGET_CITY]

# Reglas simples que el equipo puede revisar sin buscar dentro del ETL.
VALID_AGE_MIN = 18
VALID_AGE_MAX = 90
ESTRATOS = ["Bajo", "Medio", "Alto", "Muy Alto"]
CUSTOMER_PREFERENCES = [
    "Mariscos",
    "Pescado",
    "Carnes",
    "Vegetariano",
    "Vegano",
    "Otro",
]

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


@dataclass(frozen=True)
class PipelinePaths:
    mode: str
    customers_raw: Path
    yelp_raw: Path
    category_mapping: Path
    customers_clean: Path
    customers_miami: Path
    customer_value_miami: Path
    yelp_clean: Path
    preference_opportunity_miami: Path
    data_quality_report_csv: Path
    data_rejections_csv: Path
    data_quality_report_md: Path
    generation_metadata: Path | None = None

    def output_files(self) -> tuple[Path, ...]:
        files = (
            self.customers_clean,
            self.customers_miami,
            self.customer_value_miami,
            self.yelp_clean,
            self.preference_opportunity_miami,
            self.data_quality_report_csv,
            self.data_rejections_csv,
            self.data_quality_report_md,
        )
        if self.generation_metadata is not None:
            return files + (self.generation_metadata,)
        return files


FULL_PIPELINE_PATHS = PipelinePaths(
    mode="full",
    customers_raw=CUSTOMERS_RAW,
    yelp_raw=YELP_RAW,
    category_mapping=CATEGORY_MAPPING,
    customers_clean=CUSTOMERS_CLEAN,
    customers_miami=CUSTOMERS_MIAMI,
    customer_value_miami=CUSTOMER_VALUE_MIAMI,
    yelp_clean=YELP_CLEAN,
    preference_opportunity_miami=PREFERENCE_OPPORTUNITY_MIAMI,
    data_quality_report_csv=DATA_QUALITY_REPORT_CSV,
    data_rejections_csv=DATA_REJECTIONS_CSV,
    data_quality_report_md=DATA_QUALITY_REPORT_MD,
)


def build_demo_paths(root: Path = DEMO_DIR) -> PipelinePaths:
    return PipelinePaths(
        mode="demo",
        customers_raw=root / "raw" / "customers_demo_raw.csv",
        yelp_raw=YELP_RAW,
        category_mapping=CATEGORY_MAPPING,
        customers_clean=root / "clean" / "customers_clean.csv",
        customers_miami=root / "final" / "customers_miami.csv",
        customer_value_miami=root / "final" / "customer_value_miami.csv",
        yelp_clean=root / "clean" / "yelp_restaurants_clean.csv",
        preference_opportunity_miami=(
            root / "final" / "preference_opportunity_miami.csv"
        ),
        data_quality_report_csv=root / "final" / "data_quality_report.csv",
        data_rejections_csv=root / "final" / "data_rejections.csv",
        data_quality_report_md=root / "docs" / "data_quality_report.md",
        generation_metadata=root / "docs" / "generation_metadata.json",
    )


def get_pipeline_paths(mode: str = "full") -> PipelinePaths:
    normalized_mode = "full" if mode == "private" else mode
    if normalized_mode == "full":
        return FULL_PIPELINE_PATHS
    if normalized_mode == "demo":
        return build_demo_paths()
    raise ValueError(f"Modo desconocido: {mode}. Usa 'full' o 'demo'.")


def ensure_dirs(paths: PipelinePaths = FULL_PIPELINE_PATHS) -> None:
    directories = {
        paths.customers_raw.parent,
        paths.customers_clean.parent,
        paths.customers_miami.parent,
        paths.yelp_clean.parent,
        paths.data_quality_report_md.parent,
        REFERENCE_DIR,
    }
    for path in directories:
        path.mkdir(parents=True, exist_ok=True)
