import argparse

from .business import (
    build_customer_value_summary,
    build_preference_opportunity,
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
    quality_row,
    save_data_quality_reports,
)
from .validation import validate_all, validate_rejection_counts
from .yelp import clean_yelp, load_yelp


def run_pipeline(
    mode: str = "full",
    paths: PipelinePaths | None = None,
    demo_rows: int = DEMO_DEFAULT_ROWS,
    demo_seed: int = DEMO_DEFAULT_SEED,
):
    paths = paths or get_pipeline_paths(mode)
    ensure_dirs(paths)

    if paths.mode == "demo":
        generate_demo_customers(paths.customers_raw, demo_rows, demo_seed)
        save_generation_metadata(
            paths.generation_metadata,
            paths.customers_raw,
            demo_rows,
            demo_seed,
        )

    quality_rows = []
    customer_rejections = {}
    yelp_rejections = {}

    customers_raw = load_customers(paths.customers_raw)
    validate_contract(customers_raw, CUSTOMERS_RAW_CONTRACT, stage="input")
    quality_rows.append(quality_row("customers", "raw", customers_raw))

    customers_clean = clean_customers(customers_raw, customer_rejections)
    customers_miami = build_city_customer_view(customers_clean)
    quality_rows.append(quality_row("customers", "clean", customers_clean))
    quality_rows.append(quality_row("customers", "final_miami", customers_miami))

    yelp_raw = load_yelp(paths.yelp_raw)
    validate_contract(yelp_raw, YELP_RAW_CONTRACT, stage="input")
    quality_rows.append(quality_row("yelp", "raw", yelp_raw))

    yelp_clean = clean_yelp(yelp_raw, yelp_rejections)
    quality_rows.append(quality_row("yelp", "clean", yelp_clean))

    category_mapping = load_category_mapping(paths.category_mapping)
    validate_contract(category_mapping, CATEGORY_MAPPING_CONTRACT, stage="input")
    customer_value = build_customer_value_summary(customers_miami)
    preference_opportunity = build_preference_opportunity(
        customers_miami,
        yelp_clean,
        category_mapping,
    )
    quality_rows.append(quality_row("customer_value", "final", customer_value))
    quality_rows.append(
        quality_row("preference_opportunity", "final", preference_opportunity)
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
        data_quality,
        rejections,
    )

    customers_clean.to_csv(paths.customers_clean, index=False, encoding="utf-8")
    customers_miami.to_csv(paths.customers_miami, index=False, encoding="utf-8")
    yelp_clean.to_csv(paths.yelp_clean, index=False, encoding="utf-8")
    customer_value.to_csv(
        paths.customer_value_miami,
        index=False,
        encoding="utf-8",
    )
    preference_opportunity.to_csv(
        paths.preference_opportunity_miami,
        index=False,
        encoding="utf-8",
    )
    save_data_quality_reports(
        data_quality,
        rejections,
        paths.data_quality_report_csv,
        paths.data_rejections_csv,
        paths.data_quality_report_md,
        paths.mode,
    )

    return {
        "mode": paths.mode,
        "paths": paths,
        "customers_clean": customers_clean,
        "customers_miami": customers_miami,
        "yelp_clean": yelp_clean,
        "customer_value": customer_value,
        "category_mapping": category_mapping,
        "preference_opportunity": preference_opportunity,
        "data_quality": data_quality,
        "rejections": rejections,
    }


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
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    outputs = run_pipeline(
        mode=args.mode,
        demo_rows=args.demo_rows,
        demo_seed=args.demo_seed,
    )
    paths = outputs["paths"]

    print(f"Pipeline {outputs['mode']} completo.")
    print(f"Clientes limpios: {len(outputs['customers_clean']):,}")
    print(f"Clientes Miami: {len(outputs['customers_miami']):,}")
    print(f"Restaurantes Yelp limpios: {len(outputs['yelp_clean']):,}")
    print(f"Resumen de valor de clientes: {len(outputs['customer_value']):,} filas")
    print(
        "Tabla de oportunidades por preferencia: "
        f"{len(outputs['preference_opportunity']):,} filas"
    )
    print(f"Filas rechazadas: {int(outputs['rejections']['rows_rejected'].sum()):,}")
    print(f"Reporte de calidad: {paths.data_quality_report_md}")


if __name__ == "__main__":
    main()
