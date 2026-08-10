# Estrategia de pruebas

Los tests revisan dos cosas: que los archivos generados sean válidos y que las reglas de negocio respondan como se espera.

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

## Ejecución

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q
~~~

La suite actual contiene 12 pruebas.
