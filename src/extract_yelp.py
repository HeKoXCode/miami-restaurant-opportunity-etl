import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from .config import RAW_DIR, YELP_EXTRACTION_METADATA, ensure_dirs

API_URL = "https://api.yelp.com/v3/businesses/search"


def load_env_file(path):
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def fetch_yelp_restaurants(city, limit_total=240):
    load_env_file(Path(__file__).resolve().parents[1] / ".env")
    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        raise RuntimeError("Falta YELP_API_KEY. Copia .env.example a .env y agrega tu key.")

    headers = {"Authorization": f"Bearer {api_key}"}
    businesses = []

    for offset in range(0, limit_total, 50):
        limit = min(50, limit_total - offset)
        params = {
            "term": "restaurants",
            "location": city,
            "limit": limit,
            "offset": offset,
        }

        response = requests.get(API_URL, params=params, headers=headers, timeout=30)
        if response.status_code == 429:
            time.sleep(3)
            response = requests.get(API_URL, params=params, headers=headers, timeout=30)

        response.raise_for_status()
        data = response.json()
        page = data.get("businesses", [])
        if not page:
            break

        businesses.extend(page)

    return pd.DataFrame(businesses)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrae restaurantes desde Yelp.")
    parser.add_argument("--city", default="Miami", help="Ciudad a buscar. Ejemplo: Miami")
    parser.add_argument("--limit", type=int, default=240, help="Maximo de resultados")
    parser.add_argument(
        "--output",
        default="yelp_restaurants_raw.csv",
        help="Nombre del CSV dentro de data/raw",
    )
    args = parser.parse_args()

    ensure_dirs()
    df = fetch_yelp_restaurants(args.city, args.limit)
    output_path = RAW_DIR / args.output
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    metadata = {
        "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_city": args.city,
        "requested_limit": args.limit,
        "raw_rows": len(df),
        "output_file": str(output_path.relative_to(output_path.parents[2])),
    }
    YELP_EXTRACTION_METADATA.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Extraidos {len(df):,} restaurantes de Yelp.")
    print(f"Guardado: {output_path}")
    print(f"Metadata: {YELP_EXTRACTION_METADATA}")


if __name__ == "__main__":
    main()
