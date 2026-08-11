# Revisión de consistencia de publicación

Estado: **aprobada el 10/08/2026**.

## Evidencia verificada

- Suite local: 12 pruebas aprobadas.
- Pipeline completo local: 29.978 clientes limpios, 3.183 clientes de Miami y 186 restaurantes limpios.
- Notebook: 22 celdas, 8 de código ejecutadas, 0 errores y 4 gráficos.
- Renderizado en Windows: 0 advertencias relevantes.
- Determinismo: dos renderizados consecutivos produjeron el mismo SHA-256 del notebook.
- README: métricas ejecutivas reconciliadas contra los CSV finales.
- Privacidad: los outputs de clientes no contienen columnas de nombre, apellido, teléfono o correo.
- Publicación: el raw privado y `.env` permanecen ignorados; no se encontraron rutas sensibles en archivos versionados ni en el historial local.
- Navegación: todos los enlaces locales de la documentación resuelven a archivos existentes.
- Dependencias: instalación bloqueada con versiones exactas y hashes para Windows.

Estas comprobaciones quedan automatizadas, cuando aplica, mediante `scripts/validate_publication.py` y el workflow `Public verification`.

## Alcance deliberadamente pendiente

El workflow público ejecuta tests, notebook y validaciones de publicación en Python 3.12–3.14. No reconstruye el ETL completo porque `customers_raw.csv` contiene campos con apariencia de PII y no se publica.

Para alcanzar reproducibilidad pública end-to-end todavía se debe completar la fuente demo sintética descrita como ETL-I1. Después podrá ampliarse el CI con pipeline demo, lint, control de archivos inesperados y artifacts, sin confundir esa mejora intermedia con la verificación pública incorporada ahora.
