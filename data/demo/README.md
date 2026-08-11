# Fuente y outputs demo

Esta carpeta demuestra el ETL completo sin utilizar el raw educativo privado.

- `raw/customers_demo_raw.csv` contiene 750 clientes totalmente sintéticos.
- La semilla fija es `20260713` y el generador vive en `src/demo_data.py`.
- Los nombres usan el patrón `Cliente Demo`, los correos terminan en `example.invalid` y los teléfonos pertenecen al rango ficticio 555-01xx.
- `clean/`, `final/` y `docs/` se regeneran sin modificar los resultados privados publicados en las carpetas principales.
- El snapshot público de Yelp y el mapping de categorías son las otras dos entradas del pipeline.

~~~powershell
python -m src.pipeline --mode demo
python scripts/validate_publication.py --mode demo
~~~

La demo incluye problemas controlados de frecuencia, gasto, edad y preferencia. Así prueba imputaciones, rechazos, privacidad, contratos y tablas de negocio en lugar de recorrer únicamente el caso ideal.
