# Reporte de calidad

Control operativo generado por el pipeline. Resume el volumen de cada etapa y los problemas de calidad que deben quedar resueltos antes del analisis.

- Clientes limpios: 29,978 filas.
- Restaurantes Yelp limpios: 186 filas.

| dataset | step | rows | columns | missing_total | duplicate_rows | duplicate_ids | duplicate_yelp_ids | negative_frequency | missing_spend | invalid_age | rating_outside_0_5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| customers | raw | 30000 | 17 | 31887 | 0 | 0.0 |  | 1547.0 | 145.0 | 308.0 |  |
| customers | clean | 29978 | 18 | 0 | 0 | 0.0 |  | 0.0 | 0.0 | 0.0 |  |
| customers | final_miami | 3183 | 18 | 0 | 0 | 0.0 |  | 0.0 | 0.0 | 0.0 |  |
| yelp | raw | 240 | 15 | 137 | 0 |  |  |  |  |  | 0.0 |
| yelp | clean | 186 | 25 | 0 | 0 | 0.0 | 0.0 |  |  |  | 0.0 |
| customer_value | final | 6 | 9 | 0 | 0 |  |  |  |  |  |  |
| preference_opportunity | final | 6 | 19 | 0 | 0 |  |  |  |  |  |  |
