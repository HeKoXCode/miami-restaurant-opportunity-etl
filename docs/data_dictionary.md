# Diccionario de datos

## customers_clean.csv y customers_miami.csv

customers_clean.csv contiene todos los clientes limpios. customers_miami.csv aplica el recorte de ciudad usado en el caso de negocio. Ambos outputs excluyen PII.

- id_persona: identificador analítico.
- edad: edad corregida entre 18 y 90 años.
- genero: género informado.
- ciudad_residencia: ciudad del cliente.
- estrato_socioeconomico: Bajo, Medio, Alto o Muy Alto.
- frecuencia_visita: cantidad de visitas informada; la unidad temporal no está documentada.
- promedio_gasto_comida: ticket promedio informado.
- gasto_periodo_estimado: frecuencia por ticket promedio.
- preferencias_alimenticias: preferencia declarada o imputada como Otro.
- membresia_premium: indicador de membresía.
- tipo_de_pago_mas_usado: método de pago principal.
- ingresos_mensuales: ingreso informado en la fuente.
- frecuencia_imputada: identifica corrección de frecuencia.
- gasto_imputado: identifica imputación de gasto.
- edad_imputada: identifica imputación de edad.
- preferencia_original_nula: identifica preferencia faltante en raw.

## customer_value_miami.csv

Resume valor por membresía premium y estrato socioeconómico.

- dimension: variable usada para segmentar.
- segment: valor del segmento.
- customer_count: clientes del segmento.
- customer_share: participación dentro de Miami.
- avg_visit_frequency: frecuencia promedio.
- avg_ticket: ticket promedio.
- avg_estimated_period_spend: gasto estimado promedio por cliente.
- estimated_period_spend: gasto estimado total del segmento.
- spend_share: participación del segmento en el gasto estimado.

## yelp_restaurants_clean.csv

- restaurant_id: identificador interno.
- yelp_id: identificador original de Yelp.
- name: nombre comercial.
- rating: rating de Yelp.
- review_count: cantidad de reseñas.
- quality_score: rating ajustado por cantidad de reseñas.
- price y price_level: nivel de precio textual y numérico.
- price_was_missing: identifica precio imputado.
- categories y main_category: categorías normalizadas.
- transactions: servicios informados en orden canónico.
- has_delivery, has_pickup, has_reservation: flags de servicio.
- latitude, longitude y address: ubicación.
- city, state, zip_code y country: componentes geográficos.

## preference_opportunity_miami.csv

- customer_preference: preferencia alimenticia.
- mapped_yelp_categories: categorías Yelp relacionadas.
- customer_count y customer_share: tamaño de demanda.
- imputed_preference_count y imputed_preference_share: trazabilidad de preferencias imputadas.
- preference_data_quality: Alta, Media o Baja según imputación.
- avg_estimated_period_spend: gasto promedio del segmento.
- estimated_period_spend y estimated_period_spend_share: tamaño económico del segmento.
- restaurant_count: restaurantes de la muestra que cubren la preferencia.
- observed_restaurant_coverage: restaurant_count dividido por restaurantes limpios.
- avg_rating, median_review_count y avg_quality_score: contexto de calidad de oferta.
- demand_coverage_index: customer_share dividido por observed_restaurant_coverage.
- coverage_signal: lectura descriptiva del índice.
- recommended_action: siguiente validación sugerida, no decisión automática.

## category_mapping.csv

- customer_preference: preferencia del dataset de clientes.
- yelp_category: categoría Yelp considerada relacionada.

## data_quality_report.csv

Resume filas, columnas, nulos, duplicados e indicadores específicos en cada etapa del pipeline.

La versión machine-readable vive en `data/final/` para que el notebook consuma únicamente outputs finales. El reporte legible permanece en `docs/data_quality_report.md`.

## data_rejections.csv

- dataset: fuente afectada.
- step: etapa que descartó las filas.
- reason: causa estable y auditable.
- rows_rejected: cantidad descartada por esa causa.

La suma por dataset reconcilia la diferencia entre filas raw y clean.

## data/demo/

Replica las capas `raw`, `clean`, `final` y `docs` para el modo sintético. Conserva los mismos contratos analíticos sin reemplazar los outputs del caso completo.

## staging

Snapshot validado antes de aplicar reglas de limpieza. Conserva el esquema de entrada para separar ingestión de transformación. `data/staging/` no se publica porque el full contiene campos de contacto; `data/demo/staging/` sólo contiene identidades sintéticas.

## restaurant_competition_miami.csv

- city: ciudad analizada.
- customer_preference: preferencia relacionada mediante el mapping.
- price_level / price_segment: nivel Yelp normalizado 1–4.
- restaurant_count: restaurantes observados en el cruce.
- restaurant_share_within_preference: proporción de la cobertura de esa preferencia.
- imputed_price_count / imputed_price_share: cantidad y proporción de precios imputados.
- avg_rating / median_review_count / avg_quality_score: evidencia observable de Yelp.
- delivery_share / reservation_share: disponibilidad relativa de servicios.

Un restaurante puede aparecer en más de una preferencia. Los conteos no representan cuota de mercado.

## preference_sensitivity_miami.csv

- scenario: Conservador, Base o Exploratorio.
- gap_threshold / wide_threshold: umbrales aplicados.
- demand_coverage_index: índice original sin modificar.
- coverage_signal: clasificación resultante.
- stable_across_scenarios: verdadero cuando la preferencia conserva señal en los tres escenarios.

## pipeline_manifest.json

- pipeline_version / schema_version / manifest_version: versiones aplicables.
- mode: full o demo.
- run_id: identidad determinista de fuentes, código y versiones.
- code_sha256: hash del código transformador y lockfile.
- inputs: archivo, filas y SHA-256 por fuente.
- outputs: ruta relativa, filas y SHA-256 por producto estable.
