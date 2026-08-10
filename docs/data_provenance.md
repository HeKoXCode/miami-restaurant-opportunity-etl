# Procedencia, privacidad y uso de datos

## Clientes

El archivo de clientes proviene de una entrega educativa. El proyecto recibido no incluye una fuente pública, licencia, metodología de muestreo ni confirmación de que los registros sean sintéticos.

El raw contiene nombres, apellidos, teléfonos y correos con apariencia de datos personales. Por ese motivo:

- data/raw/customers_raw.csv está ignorado por Git;
- los outputs clean y final eliminan esas columnas;
- el raw no debe publicarse hasta confirmar origen y permiso de uso;
- el análisis no afirma representar a la población de Miami.

## Yelp

Los restaurantes se obtienen mediante la API de búsqueda de Yelp con término restaurants y ubicación Miami. La consulta está limitada y ordenada por la API, por lo que no constituye un censo ni una muestra aleatoria.

El snapshot incluido tiene 240 filas raw. Después de deduplicación y recorte estricto de ciudad quedan 186 restaurantes.

La extracción existente es anterior al registro de metadata y su fecha exacta no está disponible. Las nuevas ejecuciones de src/extract_yelp.py generan docs/yelp_extraction_metadata.json con fecha UTC, ciudad, límite solicitado y filas obtenidas.

## Publicación responsable

El código y los resultados agregados pueden mostrarse como ejercicio educativo. Antes de publicar datos de detalle se debe confirmar licencia, privacidad y términos de uso de cada fuente.
