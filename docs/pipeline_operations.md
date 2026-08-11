# Operación incremental y manifiestos

Versión del pipeline: **2.0.0**.

## Capas

1. `raw`: fuente recibida o generada.
2. `staging`: snapshot validado sin transformaciones de negocio.
3. `clean`: entidades depuradas y trazables.
4. `final`: marts, calidad, rechazos y manifiesto.

El staging full puede contener campos de contacto y permanece ignorado. El staging demo es publicable porque sus identidades son totalmente sintéticas.

## Identidad de una ejecución

El `run_id` se deriva de:

- hash SHA-256 de clientes, Yelp y mapping;
- hash del código de `src/` y del lockfile;
- versiones del pipeline y del esquema;
- modo `full` o `demo`.

No incluye hora ni duración, por lo que entradas y código idénticos producen el mismo identificador. `pipeline_manifest.json` guarda filas y hashes de las tres fuentes y de los doce outputs estables.

## Incrementalidad

La ejecución normal compara el manifiesto con fuentes, código y outputs existentes. Si todo coincide:

- devuelve estado `unchanged`;
- vuelve a validar los contratos publicados;
- evita limpieza, marts y escrituras analíticas;
- conserva el mismo `run_id`.

`--force` obliga una reconstrucción completa. `run_demo.bat` lo usa para demostrar el recorrido end-to-end desde un clon.

## Publicación y rollback lógico

Todos los CSV, el reporte Markdown y el manifiesto se serializan antes de modificar outputs. Cada destino obtiene un temporal y un backup en su propio volumen. Si falla cualquier reemplazo, los archivos ya reemplazados recuperan su versión anterior y los nuevos se retiran.

La suite simula un fallo en el segundo archivo y comprueba que el bundle completo conserva su estado previo.

## Historial operativo

Cada intento registra fecha UTC, `run_id`, modo, estado, causa de cache, duración y memoria pico bajo `.pipeline_state/`. Esta carpeta no se versiona porque sus tiempos y timestamps son propios de cada equipo.

La evidencia estable vive en:

- `data/*/final/pipeline_manifest.json`;
- `docs/performance_baseline.json`;
- `docs/c3_lite_verification.md`.

## Benchmarks

~~~powershell
.\.venv\Scripts\python.exe scripts\benchmark_pipeline.py --runs 5
~~~

El baseline no promete el mismo tiempo en cualquier hardware. C3-Lite usa presupuestos amplios de 10 segundos y 256 MiB para detectar regresiones graves en la demo de 750 filas.
