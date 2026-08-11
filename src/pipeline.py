import argparse
import json
import time
import tracemalloc

import pandas as pd

from .business import (
    build_customer_value_summary,
    build_preference_opportunity,
    build_preference_sensitivity,
    build_restaurant_competition,
    load_category_mapping,
)
from .config import (
    DEMO_DEFAULT_ROWS,
    DEMO_DEFAULT_SEED,
    PipelinePaths,
    ensure_dirs,
    get_pipeline_paths,
)
from .contracts import (
    CATEGORY_MAPPING_CONTRACT,
    CUSTOMERS_RAW_CONTRACT,
    YELP_RAW_CONTRACT,
    validate_contract,
    validate_pipeline_contracts,
)
from .customers import build_city_customer_view, clean_customers, load_customers
from .demo_data import generate_demo_customers, save_generation_metadata
from .quality import (
    build_data_quality_report,
    build_rejection_report,
    data_quality_to_markdown,
    quality_row,
)
from .runtime import (
    atomic_publish,
    build_input_state,
    build_manifest,
    deterministic_run_id,
    manifest_is_current,
    pipeline_code_hash,
    record_runtime,
)
from .validation import validate_all, validate_rejection_counts
from .yelp import clean_yelp, load_yelp


def _csv_payload(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(index=False).encode("utf-8")


def _load_cached_outputs(paths: PipelinePaths) -> dict:
    return {
        "mode": paths.mode,
        "paths": paths,
        "customers_clean": pd.read_csv(paths.customers_clean),
        "customers_miami": pd.read_csv(paths.customers_miami),
        "yelp_clean": pd.read_csv(paths.yelp_clean),
        "customer_value": pd.read_csv(paths.customer_value_miami),
        "category_mapping": pd.read_csv(paths.category_mapping),
        "preference_opportunity": pd.read_csv(
            paths.preference_opportunity_miami
        ),
        "restaurant_competition": pd.read_csv(
            paths.restaurant_competition_miami
        ),
        "preference_sensitivity": pd.read_csv(
            paths.preference_sensitivity_miami
        ),
        "data_quality": pd.read_csv(paths.data_quality_report_csv),
        "rejections": pd.read_csv(paths.data_rejections_csv),
    }


def _runtime_metrics(started_at: float) -> tuple[float, float]:
    elapsed_seconds = time.perf_counter() - started_at
    _, peak_bytes = tracemalloc.get_traced_memory()
    return elapsed_seconds, peak_bytes / (1024 * 1024)


def run_pipeline(
    mode: str = "full",
    paths: PipelinePaths | None = None,
    demo_rows: int = DEMO_DEFAULT_ROWS,
    demo_seed: int = DEMO_DEFAULT_SEED,
    incremental: bool = True,
):
    started_at = time.perf_counter()
    owns_memory_trace = not tracemalloc.is_tracing()
    if owns_memory_trace:
        tracemalloc.start()
    paths = paths or get_pipeline_paths(mode)
    ensure_dirs(paths)
    run_id = "unavailable"
    cache_reason = "forced" if not incremental else None

    try:
        if paths.mode == "demo":
            generate_demo_customers(paths.customers_raw, demo_rows, demo_seed)
            save_generation_metadata(
                paths.generation_metadata,
                paths.customers_raw,
                demo_rows,
                demo_seed,
            )

        customers_raw = load_customers(paths.customers_raw)
        validate_contract(customers_raw, CUSTOMERS_RAW_CONTRACT, stage="input")
        yelp_raw = load_yelp(paths.yelp_raw)
        validate_contract(yelp_raw, YELP_RAW_CONTRACT, stage="input")
        category_mapping = load_category_mapping(paths.category_mapping)
        validate_contract(
            category_mapping,
            CATEGORY_MAPPING_CONTRACT,
            stage="input",
        )

        code_hash = pipeline_code_hash()
        inputs = build_input_state(
            paths.customers_raw,
            paths.yelp_raw,
            paths.category_mapping,
            len(customers_raw),
            len(yelp_raw),
            len(category_mapping),
        )
        run_id = deterministic_run_id(paths.mode, inputs, code_hash)

        if incremental:
            is_current, cache_reason = manifest_is_current(paths, inputs, code_hash)
            if is_current:
                outputs = _load_cached_outputs(paths)
                validate_pipeline_contracts(
                    outputs["customers_clean"],
                    outputs["customers_miami"],
                    outputs["yelp_clean"],
                    outputs["customer_value"],
                    outputs["preference_opportunity"],
                    outputs["restaurant_competition"],
                    outputs["preference_sensitivity"],
                    outputs["data_quality"],
                    outputs["rejections"],
                )
                elapsed, peak_memory = _runtime_metrics(started_at)
                runtime = record_runtime(
                    paths,
                    run_id,
                    "unchanged",
                    elapsed,
                    peak_memory,
                    None,
                )
                outputs.update({"status": "unchanged", "runtime": runtime})
                return outputs

        quality_rows = [quality_row("customers", "raw", customers_raw)]
        customer_rejections = {}
        yelp_rejections = {}

        customers_staging = customers_raw.copy()
        yelp_staging = yelp_raw.copy()
        quality_rows.append(quality_row("customers", "staging", customers_staging))
        quality_rows.append(quality_row("yelp", "raw", yelp_raw))
        quality_rows.append(quality_row("yelp", "staging", yelp_staging))

        customers_clean = clean_customers(
            customers_staging,
            customer_rejections,
        )
        customers_miami = build_city_customer_view(customers_clean)
        quality_rows.append(quality_row("customers", "clean", customers_clean))
        quality_rows.append(
            quality_row("customers", "final_miami", customers_miami)
        )

        yelp_clean = clean_yelp(yelp_staging, yelp_rejections)
        quality_rows.append(quality_row("yelp", "clean", yelp_clean))

        customer_value = build_customer_value_summary(customers_miami)
        preference_opportunity = build_preference_opportunity(
            customers_miami,
            yelp_clean,
            category_mapping,
        )
        restaurant_competition = build_restaurant_competition(
            yelp_clean,
            category_mapping,
        )
        preference_sensitivity = build_preference_sensitivity(
            preference_opportunity
        )
        quality_rows.extend(
            (
                quality_row("customer_value", "final", customer_value),
                quality_row(
                    "preference_opportunity",
                    "final",
                    preference_opportunity,
                ),
                quality_row(
                    "restaurant_competition",
                    "final",
                    restaurant_competition,
                ),
                quality_row(
                    "preference_sensitivity",
                    "final",
                    preference_sensitivity,
                ),
            )
        )

        validate_all(
            customers_clean,
            customers_miami,
            yelp_clean,
            preference_opportunity,
            customer_value,
            category_mapping,
        )
        validate_rejection_counts(
            customers_raw,
            customers_clean,
            customer_rejections,
            "customers",
        )
        validate_rejection_counts(yelp_raw, yelp_clean, yelp_rejections, "yelp")

        data_quality = build_data_quality_report(quality_rows)
        rejections = build_rejection_report(customer_rejections, yelp_rejections)
        validate_pipeline_contracts(
            customers_clean,
            customers_miami,
            yelp_clean,
            customer_value,
            preference_opportunity,
            restaurant_competition,
            preference_sensitivity,
            data_quality,
            rejections,
        )

        dataframes = {
            paths.customers_staging: customers_staging,
            paths.yelp_staging: yelp_staging,
            paths.customers_clean: customers_clean,
            paths.customers_miami: customers_miami,
            paths.yelp_clean: yelp_clean,
            paths.customer_value_miami: customer_value,
            paths.preference_opportunity_miami: preference_opportunity,
            paths.restaurant_competition_miami: restaurant_competition,
            paths.preference_sensitivity_miami: preference_sensitivity,
            paths.data_quality_report_csv: data_quality,
            paths.data_rejections_csv: rejections,
        }
        payloads = {path: _csv_payload(frame) for path, frame in dataframes.items()}
        quality_markdown = data_quality_to_markdown(
            data_quality,
            rejections,
            paths.mode,
        )
        payloads[paths.data_quality_report_md] = quality_markdown.encode("utf-8")
        row_counts = {path: len(frame) for path, frame in dataframes.items()}
        row_counts[paths.data_quality_report_md] = None
        manifest = build_manifest(paths, inputs, code_hash, payloads, row_counts)
        payloads[paths.pipeline_manifest] = (
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        atomic_publish(payloads)

        elapsed, peak_memory = _runtime_metrics(started_at)
        runtime = record_runtime(
            paths,
            run_id,
            "rebuilt",
            elapsed,
            peak_memory,
            cache_reason,
        )
        return {
            "mode": paths.mode,
            "paths": paths,
            "status": "rebuilt",
            "runtime": runtime,
            "customers_clean": customers_clean,
            "customers_miami": customers_miami,
            "yelp_clean": yelp_clean,
            "customer_value": customer_value,
            "category_mapping": category_mapping,
            "preference_opportunity": preference_opportunity,
            "restaurant_competition": restaurant_competition,
            "preference_sensitivity": preference_sensitivity,
            "data_quality": data_quality,
            "rejections": rejections,
        }
    except Exception:
        elapsed, peak_memory = _runtime_metrics(started_at)
        record_runtime(
            paths,
            run_id,
            "failed",
            elapsed,
            peak_memory,
            cache_reason,
        )
        raise
    finally:
        if owns_memory_trace:
            tracemalloc.stop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ejecuta el ETL de Miami.")
    parser.add_argument(
        "--mode",
        choices=["full", "demo"],
        default="full",
        help="full usa el raw privado local; demo genera una fuente sintética.",
    )
    parser.add_argument("--demo-rows", type=int, default=DEMO_DEFAULT_ROWS)
    parser.add_argument("--demo-seed", type=int, default=DEMO_DEFAULT_SEED)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reconstruye aunque el manifiesto indique que nada cambió.",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    outputs = run_pipeline(
        mode=args.mode,
        demo_rows=args.demo_rows,
        demo_seed=args.demo_seed,
        incremental=not args.force,
    )
    paths = outputs["paths"]

    print(f"Pipeline {outputs['mode']} {outputs['status']}.")
    print(f"Run ID: {outputs['runtime']['run_id']}")
    print(f"Clientes limpios: {len(outputs['customers_clean']):,}")
    print(f"Clientes Miami: {len(outputs['customers_miami']):,}")
    print(f"Restaurantes Yelp limpios: {len(outputs['yelp_clean']):,}")
    print(f"Resumen de valor de clientes: {len(outputs['customer_value']):,} filas")
    print(
        "Tabla de oportunidades por preferencia: "
        f"{len(outputs['preference_opportunity']):,} filas"
    )
    print(
        "Competencia por precio: "
        f"{len(outputs['restaurant_competition']):,} filas"
    )
    print(
        "Sensibilidad de umbrales: "
        f"{len(outputs['preference_sensitivity']):,} filas"
    )
    print(f"Filas rechazadas: {int(outputs['rejections']['rows_rejected'].sum()):,}")
    print(
        "Rendimiento: "
        f"{outputs['runtime']['elapsed_seconds']:.4f}s, "
        f"{outputs['runtime']['peak_memory_mb']:.2f} MiB pico"
    )
    print(f"Reporte de calidad: {paths.data_quality_report_md}")


if __name__ == "__main__":
    main()
