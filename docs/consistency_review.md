# Revisión de consistencia de publicación

Estado: **aprobada el 10/08/2026**.

## Evidencia verificada

- Suite local: 19 pruebas aprobadas.
- Pipeline completo local: 29.978 clientes limpios, 3.183 clientes de Miami y 186 restaurantes limpios.
- Pipeline demo: 750 clientes raw totalmente sintéticos, outputs aislados y validación end-to-end.
- Notebook: 23 celdas, 8 de código ejecutadas, 0 errores y 4 gráficos; consume únicamente tablas finales.
- Renderizado en Windows: 0 advertencias relevantes.
- Determinismo: dos renderizados consecutivos produjeron el mismo SHA-256 del notebook.
- Determinismo demo: dos ejecuciones con la misma semilla produjeron los mismos hashes.
- Contratos: inputs y outputs validados antes de transformar o escribir bajo esquema 1.0.0.
- Rechazos: raw menos clean reconciliado por causa para clientes y Yelp.
- README: métricas ejecutivas reconciliadas contra los CSV finales.
- Privacidad: los outputs de clientes no contienen columnas de nombre, apellido, teléfono o correo.
- Publicación: el raw privado y `.env` permanecen ignorados; no se encontraron rutas sensibles en archivos versionados ni en el historial local.
- Navegación: todos los enlaces locales de la documentación resuelven a archivos existentes.
- Dependencias: instalación bloqueada con versiones exactas y hashes para Windows; Ruff incluido.

Estas comprobaciones quedan automatizadas, cuando aplica, mediante `scripts/validate_publication.py` y el workflow `Public verification`.

## Alcance después de los intermedios

El workflow público ejecuta lint, tests, pipeline demo, controles de privacidad/determinismo, notebook y validaciones en Python 3.12–3.14. La demo cubre el recorrido público completo sin afirmar que reproduce la distribución del raw educativo.

La reconstrucción del caso completo sigue requiriendo `customers_raw.csv` autorizado. Las mejoras restantes pertenecen a la fase compleja: incrementalidad, manifiestos históricos/benchmarks y ampliación analítica.
