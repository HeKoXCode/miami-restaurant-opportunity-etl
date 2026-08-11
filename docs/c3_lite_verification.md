# Verificación C3-Lite

Estado: **APROBADO**.
Fecha: 2026-08-10.

Esta puerta reúne las comprobaciones técnicas finales del proyecto sin afirmar que la demo sintética reproduce la distribución comercial del raw educativo.

| Control | Estado | Evidencia |
|---|---|---|
| Ruff | APROBADO | All checks passed! |
| Pytest | APROBADO | 24 passed in 4.03s |
| Demo determinista e incremental | APROBADO | 14 archivos estables; run_id=b54910e8618997e4; tercera ejecución unchanged |
| Presupuesto de rendimiento | APROBADO | máximo 0.89s y 2.97 MiB; presupuesto 10s/256 MiB |
| Publicación demo | APROBADO | Validación demo consistente: métricas, outputs, privacidad y enlaces verificados. |
| Pipeline full local | APROBADO | run_id=1aa6a2953069e064; 3,183 clientes Miami |
| Notebook ejecutado | APROBADO | Notebook ejecutado y guardado: .\notebooks\01_miami_business_case.ipynb |
| Publicación full | APROBADO | Validación full consistente: métricas, outputs, privacidad y enlaces verificados. |

## Rendimiento observado

- Reconstrucción demo más lenta: 0.8881 segundos.
- Pico máximo de memoria: 2.97 MiB.
- Ejecución incremental: 0.2602 segundos y 1.43 MiB.
- Archivos deterministas comparados: 14.

## Alcance

- Pipeline full local incluido: sí.
- Pipeline demo público reconstruido dos veces y luego validado en modo incremental.
- La CI repite esta puerta en Python 3.12, 3.13 y 3.14 sobre Windows.
- Los presupuestos son guardrails de regresión técnica, no benchmarks universales entre equipos.
