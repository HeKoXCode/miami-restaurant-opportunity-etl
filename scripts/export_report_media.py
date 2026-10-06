"""Regenerate native PNG, SVG and PDF from the committed educational outputs."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if __name__ == "__main__":
    import matplotlib

    matplotlib.use("Agg")
    from src.reporting import load_report_data
    from src.reporting_visuals import export_figures

    parser = argparse.ArgumentParser()
    parser.add_argument("--assets-dir", type=Path, default=ROOT / "docs/assets")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=ROOT / "docs/media/technical/miami_caso_educativo_figuras_hq.pdf",
    )
    args = parser.parse_args()
    export_figures(load_report_data(), args.assets_dir, args.pdf)
    print("Six native figures exported; no private raw customer data used")
