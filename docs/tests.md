# Estrategia de pruebas

Los tests revisan outputs, contratos, reproducibilidad demo, preparación del reporte y reglas de negocio.

## Clientes

- IDs únicos, edades válidas, frecuencias y gastos no negativos.
- Preferencias sin nulos y conservación explícita de Otro.
- Recorte final exclusivo de Miami.
- Reproducción exacta de gasto_periodo_estimado.
- Ausencia de nombre, apellido, teléfono y correo en outputs analíticos.
- Participaciones de clientes y gasto que suman aproximadamente 100% por dimensión.

## Yelp

- restaurant_id y yelp_id únicos.
- Ratings entre 0 y 5 y reseñas no negativas.
- Cero nulos en el output limpio.
- Ciudades dentro del recorte permitido.
- Transacciones en orden canónico.

## Oportunidad por preferencia

- Coberturas e índices dentro de rangos válidos.
- Participaciones de clientes y gasto que suman aproximadamente 100%.
- Cobertura completa del mapping de categorías.
- Presencia de calidad de evidencia, señal y acción recomendada.
- Caso directo que comprueba que una preferencia con mucha imputación se marca como No concluyente.
- Casos directos para brecha, equilibrio y oferta amplia.

## Ampliación analítica

- Seis preferencias por cinco niveles de precio, sin cruces faltantes.
- Participaciones e imputación de precio dentro de 0–100%.
- Tres escenarios de sensibilidad por preferencia.
- El escenario Base reconcilia exactamente con la señal publicada.

## Contratos y demo

- Mensajes accionables ante columnas faltantes y rangos inválidos.
- Cumplimiento de la versión de esquema publicada.
- Pipeline demo completo dentro de rutas temporales aisladas.
- Mismos hashes al repetir la demo con igual semilla.
- Ausencia de PII en outputs sintéticos.
- Segunda ejecución sin cambios devuelve `unchanged` y conserva `run_id`.
- Un fallo simulado durante la publicación restaura todos los archivos previos.

## Reporte

- Métricas ejecutivas calculadas desde outputs finales.
- Preparación reusable de segmentos, preferencias, prioridades y calidad fuera del notebook.

## Ejecución

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q
~~~

La suite actual contiene 24 pruebas.

## Verificación de publicación

`scripts/validate_publication.py` tiene dos modos. `full` reconcilia las métricas del README y comprueba el notebook. `demo` verifica origen sintético, archivos esperados y datos de contacto reservados. Ambos revisan privacidad y enlaces.

~~~powershell
.\.venv\Scripts\python.exe scripts\validate_publication.py --mode full
.\.venv\Scripts\python.exe -m src.pipeline --mode demo
.\.venv\Scripts\python.exe scripts\validate_publication.py --mode demo
.\.venv\Scripts\python.exe scripts\verify_c3_lite.py
~~~

El workflow ejecuta Ruff, 24 tests, pipeline demo forzado, control de determinismo/archivos, render del notebook, ambas validaciones y C3-Lite en Python 3.12, 3.13 y 3.14. Los outputs demo se publican como artifact temporal por versión.
