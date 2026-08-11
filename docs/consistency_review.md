# Revisión de consistencia de publicación

Estado: **aprobada el 10/08/2026**.

## Evidencia verificada

- Suite local: 24 pruebas aprobadas.
- Pipeline completo local: 29.978 clientes limpios, 3.183 clientes de Miami y 186 restaurantes limpios.
- Pipeline demo: 750 clientes raw totalmente sintéticos, outputs aislados y validación end-to-end.
- Notebook: 27 celdas, 10 de código ejecutadas, 0 errores y 6 gráficos; consume únicamente tablas finales.
- Renderizado en Windows: 0 advertencias relevantes.
- Determinismo: dos renderizados consecutivos produjeron el mismo SHA-256 del notebook.
- Determinismo demo: dos ejecuciones con la misma semilla produjeron los mismos hashes.
- Incrementalidad: una tercera ejecución sin cambios devuelve `unchanged`, conserva el `run_id` y revalida contratos.
- Atomicidad: un fallo simulado durante el segundo reemplazo restaura el bundle anterior completo.
- Lineage: manifiestos 2.0.0 registran hashes, filas, código y doce productos estables.
- Rendimiento: cinco benchmarks demo quedan bajo el presupuesto de 10 segundos y 256 MiB.
- Contratos: inputs y outputs validados antes de transformar o escribir bajo esquema 1.1.0.
- Rechazos: raw menos clean reconciliado por causa para clientes y Yelp.
- README: métricas ejecutivas reconciliadas contra los CSV finales.
- Privacidad: los outputs de clientes no contienen columnas de nombre, apellido, teléfono o correo.
- Publicación: el raw privado y `.env` permanecen ignorados; no se encontraron rutas sensibles en archivos versionados ni en el historial local.
- Navegación: todos los enlaces locales de la documentación resuelven a archivos existentes.
- Dependencias: instalación bloqueada con versiones exactas y hashes para Windows; Ruff incluido.

Estas comprobaciones quedan automatizadas mediante `scripts/validate_publication.py`, `scripts/verify_c3_lite.py` y el workflow `Public verification`.

## Alcance después de C1, C2 y C3-Lite

El workflow público ejecuta lint, tests, pipeline demo, controles de privacidad/determinismo, notebook, C3-Lite y artifacts en Python 3.12–3.14. La demo cubre el recorrido público completo sin afirmar que reproduce la distribución del raw educativo.

La reconstrucción exacta del caso educativo sigue requiriendo `customers_raw.csv` autorizado. C2 amplía competencia por precio y sensibilidad, pero no incorpora ubicación del cliente, costos, temporalidad o disposición a pagar: esas variables requieren nuevas fuentes reales.
