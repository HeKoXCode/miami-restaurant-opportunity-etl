# Contratos de datos

Versión vigente: **1.0.0**.

Los contratos viven en `src/contracts.py` y se ejecutan en dos límites del pipeline:

1. **Antes de transformar:** comprueban columnas, valores coercibles, claves y cobertura del mapping.
2. **Antes de escribir:** comprueban esquema exacto, tipos, nulabilidad, rangos, unicidad y ausencia de PII.

Un incumplimiento genera `DataContractError` con nombre del contrato, versión, etapa y detalle accionable. El pipeline no escribe outputs parciales después de un contrato fallido.

## Inputs versionados

- `customers_raw`: 17 columnas, `id_persona` obligatorio y único, campos numéricos coercibles y dominios conocidos para estrato y preferencia.
- `yelp_raw`: campos mínimos de identidad, calidad, categorías y ubicación; acepta campos adicionales de la API para tolerar extensiones no utilizadas.
- `category_mapping`: par preferencia/categoría único y cobertura obligatoria de las seis preferencias analíticas.

Los contratos de input permiten los nulos y valores fuera de rango que las reglas de limpieza tratan explícitamente. No convierten un problema de calidad conocido en un falso error de esquema.

## Outputs versionados

- clientes limpios y recorte Miami;
- restaurantes Yelp limpios;
- resumen de valor del cliente;
- oportunidad por preferencia;
- reporte de calidad;
- reporte de filas rechazadas.

Los outputs exigen columnas exactas, claves únicas, rangos válidos, nulabilidad explícita y dominios de negocio. Las columnas de contacto están prohibidas en las tablas de clientes publicables.

## Filas rechazadas

`data_rejections.csv` registra dataset, etapa, causa y cantidad. La suma por dataset debe reconciliar exactamente la diferencia entre raw y clean. Las causas actuales son:

- frecuencia negativa sin gasto disponible;
- frecuencia faltante sin gasto positivo;
- edad inválida sin actividad suficiente para imputar;
- Yelp ID duplicado;
- ciudad fuera del recorte permitido;
- nombre y dirección duplicados.

## Política de versiones

- **PATCH:** aclaración o validación equivalente sin cambiar columnas aceptadas.
- **MINOR:** nueva columna compatible o dominio ampliado.
- **MAJOR:** columna eliminada/renombrada, tipo incompatible o cambio de semántica.

Todo cambio debe actualizar `SCHEMA_VERSION`, contratos, tests, diccionario y outputs versionados en el mismo pull request.
