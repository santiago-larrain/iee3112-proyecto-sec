# Identificación de Requisitos Técnicos y Jurídicos

## Matriz de requisitos técnicos y jurídicos

| Tipo de requisito | Requisito específico | Evidencia normativa | Caso de uso en ficha técnica |
|-------------------|----------------------|---------------------|------------------------------|
| *Funcional* | Generar ficha técnica automatizada con datos de cliente, suministro, consumos y facturación | Manual SEC 2025 – Preámbulo y principios de gestión de reclamos | Toda ficha asociada a un reclamo debe incluir identificación, historial de consumos y facturación |
| *Funcional* | Contraste automático de consumo con “mes espejo” (comparación con mismo mes del año anterior) | Manual SEC 2025, Anexo 1 – Facturación Excesiva | Reclamo por facturación excesiva (>2× mes espejo) |
| *Funcional* | Reporte de inconsistencias y alertas (excesiva, provisoria, indebidos, CNR) | Manual SEC 2025 – Catálogo de tipologías | Generar alerta cuando consumo supera umbral o hay lecturas provisorias reiteradas |
| *No funcional* | Latencia máxima de generación de ficha ≤ 5 segundos en prototipo | Estándares de calidad y buenas prácticas de la SEC | Ficha debe generarse de forma rápida para revisión interna |
| *No funcional* | Auditabilidad y trazabilidad de cada dato | Manual SEC 2025 – Consistencia de información y soporte documental | Todo dato mostrado en ficha debe trazarse a probatorio (cartola, certificado, OLCA) |
| *No funcional* | Versionado de datos y logs de validación | Manual SEC 2025 – Mejora continua y control documental | Revisión de reclamos en segunda instancia requiere trazabilidad histórica |
| *Jurídico* | Facturación excesiva: descarte previo de CNR, provisoria y error de lectura; umbral > 2× mes espejo | Manual SEC 2025 – Anexo 1 | Reclamos de cobros excesivos deben resolverse comparando consumo real vs mes espejo |
| *Jurídico* | Facturación provisoria: no más de 3 meses consecutivos; corrección inmediata si atribuible a empresa | Manual SEC 2025 – Anexo 2 | Reclamo por lecturas inventadas o imposibilidad de acceso al medidor |
| *Jurídico* | Cobros indebidos: separar ítems tarifarios de financieros; no capitalización de intereses | Manual SEC 2025 – Anexo 3 | Reclamos por cobros asociados a glosas indebidas |
| *Jurídico* | Consumos no registrados (CNR): cálculo por Consumo Índice Mensual (CIM), máximo 12 meses en conexiones irregulares y 3 en otros casos | Resolución Exenta N°1952, reglas a)–c) | Reclamos por CNR requieren expediente con CIM, historial de 24 meses y probatorios |
| *Jurídico* | CNR: cuotas sin interés para clientes no irregulares | Resolución Exenta N°1952, regla f) | Reclamo por refacturación debe dividirse en cuotas iguales sin interés |
| *Jurídico* | CNR: suspensión de corte mientras reclamo esté en trámite | Resolución Exenta N°1952, regla h) | Ficha debe marcar suspensión de corte hasta resolución SEC |
| *Jurídico* | CNR: expediente probatorio obligatorio (fotos, actas, OLCA, constancia notarial) | Resolución Exenta N°1952, procedimiento de comprobación | El motor de reglas solo valida reclamo si existen probatorios asociados |
