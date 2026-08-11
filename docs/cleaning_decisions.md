# Decisiones de limpieza

Este documento registra transformaciones que afectan la interpretación de los datos. Las decisiones comerciales del análisis se documentan por separado en business_methodology.md.

## Clientes

### Frecuencia y gasto

- Las frecuencias negativas con gasto positivo se imputan con la mediana del estrato socioeconómico.
- Los gastos faltantes con frecuencia positiva se imputan con la mediana del estrato.
- Las filas sin información suficiente de frecuencia y gasto se eliminan.
- Cada corrección conserva un flag de trazabilidad.
- Las filas que no pueden recuperarse se cuentan por causa en `data_rejections.csv`; la suma reconcilia raw menos clean para evitar descartes silenciosos.

La métrica derivada es:

~~~text
gasto_periodo_estimado = frecuencia_visita * promedio_gasto_comida
~~~

Se usa por período porque la fuente no documenta si la frecuencia es semanal, mensual u otra.

### Edad

Las edades nulas o fuera de 18 a 90 años se imputan solamente cuando existe actividad de consumo. Las filas restantes con edad inválida se eliminan.

### Preferencias

Las preferencias faltantes se asignan a Otro para conservar la regla original. El flag preferencia_original_nula permite separarlas. Como 33,3% de Otro en Miami proviene de imputaciones, el segmento recibe calidad de dato Baja y no se utiliza para priorizar oportunidades.

### Privacidad

Nombre, apellido, teléfono y correo se eliminan de customers_clean.csv y customers_miami.csv. Esas columnas no son necesarias y no deben aparecer en outputs analíticos.

## Yelp

- Se eliminan duplicados por yelp_id y por nombre más dirección.
- Categorías, coordenadas y ubicación se normalizan desde estructuras anidadas.
- Precio se imputa por ciudad y categoría, después por categoría y finalmente por moda general.
- Transacciones se ordenan como delivery, pickup y restaurant_reservation.
- El análisis final conserva únicamente restaurantes cuya ciudad es Miami.
- quality_score ajusta rating por volumen de reseñas para reducir el peso de ratings con pocas observaciones.

## Reglas de negocio

category_mapping.csv traduce preferencias de clientes a categorías de Yelp. Es una tabla de referencia porque la relación es discutible y debe poder revisarse sin modificar código.

Un restaurante puede coincidir con varias preferencias. Por ese motivo, restaurant_count se interpreta como cobertura observada y no como una partición exclusiva del mercado.
