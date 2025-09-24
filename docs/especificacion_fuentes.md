# Especificación de Funetes de Datos

## Tabla 1 – Fuentes institucionales

| Fuente              | Campo / Variable           | Uso en ficha / regla | Calidad esperada              | Evidencia / Documento                  |
|---------------------|----------------------------|----------------------|--------------------------------|---------------------------------------|
| STAR (SEC)          | Tipología reclamo, estado, resoluciones | Clasificación y trazabilidad de casos | Consistencia normativa y temporalidad | Registro STAR exportado / Resolución SEC |
| Empadronamiento SEC | Potencia contratada, ID cliente, dirección, empalme | Identificación del suministro en ficha | Exactitud, actualización permanente   | Certificado de empadronamiento |
| PESEC               | Lecturas de medidor, facturación, notas de crédito | Historial de consumos y cobros | ≥ 24 meses, lecturas continuas y verificables | Reporte PESEC, facturas, cartolas |
| OLCA                | Informe de verificación de medidor | Evidencia probatoria en reclamos CNR y excesivos | Exactitud medida, trazabilidad a laboratorio acreditado | Informe OLCA (terreno/laboratorio) |
| CEM                 | Tipo de empalme, medidor, potencia instalada | Validación de conexión y coherencia de consumo | Consistencia con empadronamiento y cartolas | Certificado de empalme y medidor |

---

## Tabla 2 – Matriz de riesgos por fuente

| Fuente              | Riesgos principales | Impacto en proyecto | Probabilidad | Nivel de riesgo | Mitigación |
|---------------------|---------------------|---------------------|--------------|-----------------|------------|
| STAR (SEC)          | Acceso restringido a datos históricos; formatos exportables limitados | Alto: sin reclamos no se valida trazabilidad | Media | *Alto* | Solicitar ejemplos anonimizados a SEC; usar datasets simulados en Hito 1 |
| Empadronamiento SEC | Posibles inconsistencias con CEM; no siempre digitalizado | Medio: afecta identificación de suministro | Media | *Medio* | Validar contra cartolas y PESEC; exigir actualización oficial |
| PESEC               | Variabilidad en formatos; acceso interno SEC/distribuidoras | Alto: sin datos de consumo/facturación no se puede generar ficha | Alta | *Alto* | Pedir extractos de ejemplo; definir JSON de staging estándar |
| OLCA                | Informes no digitalizados o en PDF; tiempos de entrega largos | Muy alto: sin probatorios no se valida CNR | Media | *Alto* | Definir campos mínimos (metadatos); usar informes simulados en Hito 1 |
| CEM                 | Acceso limitado; posibles discrepancias con empadronamiento | Medio: afecta coherencia en ficha, pero se puede suplir | Baja | *Medio-Bajo* | Usar como evidencia secundaria; cruzar con empadronamiento y cartolas |
