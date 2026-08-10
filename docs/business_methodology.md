# Metodología de negocio

## Pregunta de decisión

El proyecto busca reducir una decisión de expansión: qué segmentos y preferencias gastronómicas justifican investigación adicional en Miami.

El destinatario es una dirección de expansión o un equipo que evalúa nuevos conceptos gastronómicos.

No estima rentabilidad ni recomienda una apertura automática. La salida es una priorización de hipótesis.

## Valor del cliente

El gasto estimado combina frecuencia y ticket:

~~~text
gasto_periodo_estimado = frecuencia_visita * promedio_gasto_comida
~~~

Se analizan customer_share y spend_share por membresía y estrato. La diferencia entre ambas permite detectar concentración de valor.

## Tamaño de demanda por preferencia

Para cada preferencia se calculan:

- cantidad y participación de clientes;
- gasto estimado promedio;
- gasto estimado total;
- participación en el gasto;
- porcentaje de preferencias imputadas.

El gasto total tiene más peso narrativo que el promedio porque combina escala y comportamiento.

## Cobertura observada

category_mapping.csv relaciona cada preferencia con categorías Yelp. Un restaurante se considera cobertura cuando al menos una de sus categorías coincide.

~~~text
observed_restaurant_coverage = restaurant_count / total_restaurants
demand_coverage_index = customer_share / observed_restaurant_coverage
~~~

Interpretación:

- Índice igual o superior a 1,25: brecha de cobertura observada.
- Índice entre 0,75 y 1,25: cobertura observada equilibrada.
- Índice igual o inferior a 0,75: oferta observada amplia.
- Preferencia con 20% o más de imputación: resultado no concluyente.

Los umbrales son reglas exploratorias, no parámetros universales. Se mantienen en src/config.py para que sean visibles y testeables.

## Por qué no hay un score único

No se construye una puntuación compuesta de oportunidad. Mezclar gasto, calidad, cobertura e imputación en un solo número introduciría pesos arbitrarios y una falsa precisión.

La tabla final conserva las dimensiones por separado y propone una acción de validación según la señal observada.

## Resultado y recomendación

- Mariscos concentra el mayor gasto estimado por preferencia: 178.967 unidades.
- Vegetariano tiene la mayor brecha de cobertura observada: índice 1,42.
- Ambos segmentos pasan a una primera ronda de validación de concepto, ubicación y disposición a pagar.
- Carnes muestra oferta observada amplia; una propuesta nueva debería competir por diferenciación.
- Otro queda fuera de la priorización hasta separar respuestas reales de valores imputados.

El siguiente paso recomendado es comparar zonas de Miami, precios y competidores directos para Vegetariano y Mariscos. Después corresponde validar interés y ticket con clientes del segmento premium y de estratos altos.

## Limitaciones

- Yelp es una muestra limitada y no aleatoria.
- Las categorías se superponen y las coberturas no suman 100%.
- La ubicación dentro de Miami no se incorpora al índice.
- No hay costos, márgenes, alquileres ni elasticidad de precio.
- No se conoce la unidad temporal de frecuencia_visita.
- El análisis es descriptivo y no causal.
