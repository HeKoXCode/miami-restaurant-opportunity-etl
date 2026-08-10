from .business import (
    build_customer_value_summary,
    build_preference_opportunity,
    load_category_mapping,
)
from .config import (
    CUSTOMER_VALUE_MIAMI,
    CUSTOMERS_CLEAN,
    CUSTOMERS_MIAMI,
    DATA_QUALITY_REPORT_CSV,
    DATA_QUALITY_REPORT_MD,
    PREFERENCE_OPPORTUNITY_MIAMI,
    YELP_CLEAN,
    ensure_dirs,
)
from .customers import build_city_customer_view, clean_customers, load_customers
from .quality import build_data_quality_report, quality_row, save_data_quality_reports
from .validation import validate_all
from .yelp import clean_yelp, load_yelp


def run_pipeline():
    ensure_dirs()

    quality_rows = []

    # 1. Limpiamos clientes y nos quedamos con la vista de Miami.
    customers_raw = load_customers()
    quality_rows.append(quality_row("customers", "raw", customers_raw))

    customers_clean = clean_customers(customers_raw)
    customers_miami = build_city_customer_view(customers_clean)
    quality_rows.append(quality_row("customers", "clean", customers_clean))
    quality_rows.append(quality_row("customers", "final_miami", customers_miami))

    # 2. Yelp se limpia por separado porque llega con campos anidados.
    yelp_raw = load_yelp()
    quality_rows.append(quality_row("yelp", "raw", yelp_raw))

    yelp_clean = clean_yelp(yelp_raw)
    quality_rows.append(quality_row("yelp", "clean", yelp_clean))

    # 3. Con las dos fuentes listas construimos las tablas que usa el notebook.
    category_mapping = load_category_mapping()
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

    # 4. Antes de guardar, frenamos el proceso si algo importante quedó mal.
    validate_all(
        customers_clean,
        customers_miami,
        yelp_clean,
        preference_opportunity,
        customer_value,
        category_mapping,
    )

    # 5. Guardamos solo outputs reproducibles. El notebook no modifica estos CSV.
    data_quality = build_data_quality_report(quality_rows)

    customers_clean.to_csv(CUSTOMERS_CLEAN, index=False, encoding="utf-8")
    customers_miami.to_csv(CUSTOMERS_MIAMI, index=False, encoding="utf-8")
    yelp_clean.to_csv(YELP_CLEAN, index=False, encoding="utf-8")
    customer_value.to_csv(CUSTOMER_VALUE_MIAMI, index=False, encoding="utf-8")
    preference_opportunity.to_csv(
        PREFERENCE_OPPORTUNITY_MIAMI,
        index=False,
        encoding="utf-8",
    )
    save_data_quality_reports(
        data_quality,
        DATA_QUALITY_REPORT_CSV,
        DATA_QUALITY_REPORT_MD,
    )

    return {
        "customers_clean": customers_clean,
        "customers_miami": customers_miami,
        "yelp_clean": yelp_clean,
        "customer_value": customer_value,
        "category_mapping": category_mapping,
        "preference_opportunity": preference_opportunity,
        "data_quality": data_quality,
    }


def main():
    outputs = run_pipeline()

    print("Pipeline completo.")
    print(f"Clientes limpios: {len(outputs['customers_clean']):,}")
    print(f"Clientes Miami: {len(outputs['customers_miami']):,}")
    print(f"Restaurantes Yelp limpios: {len(outputs['yelp_clean']):,}")
    print(f"Resumen de valor de clientes: {len(outputs['customer_value']):,} filas")
    print(
        "Tabla de oportunidades por preferencia: "
        f"{len(outputs['preference_opportunity']):,} filas"
    )
    print(f"Reporte de calidad: {DATA_QUALITY_REPORT_MD}")


if __name__ == "__main__":
    main()
