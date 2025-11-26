# Capítulo 11: Futuras Analíticas

[← Anterior: Utilidades](10_Utilidades.md) | [Siguiente: AI ChatBot →](12_AI_ChatBot.md)

## 11.1. Visión General

La arquitectura de base de datos relacional implementada en el sistema permite realizar análisis profundos y detección de patrones que transforman el sistema de un simple gestor de casos en una herramienta de inteligencia de negocio. Este capítulo describe las capacidades analíticas futuras que la estructura de datos habilita.

## 11.2. Ventajas de la Estructura Relacional

### 11.2.1. Relaciones Explícitas

La base de datos relaciona:
- **Personas** con **Casos** (vía `persona_id`)
- **Suministros** con **Casos** (vía `suministro_id`)
- **EDNs** con **Casos** (vía `case_id`)
- **Documentos** con **Casos** (vía `case_id`)

**Capacidades Habilitadas:**
- Análisis histórico por cliente: Ver todos los reclamos de una persona a lo largo del tiempo
- Análisis por suministro: Identificar patrones en un NIS específico
- Análisis cruzado: Relacionar tipos de reclamos con empresas, comunas, períodos, etc.

### 11.2.2. Normalización de Datos

La separación de datos en archivos especializados:
- **Reduce redundancia**: La información de una persona se almacena una vez y se referencia
- **Facilita actualizaciones**: Cambios en datos de personas se reflejan automáticamente en todos sus casos
- **Mejora la integridad**: Los datos están centralizados y son consistentes

## 11.3. Análisis por Empresa

### 11.3.1. Volumen de Reclamos por Empresa

**Capacidad:** Contar cuántos reclamos recibe cada empresa distribuidora.

**Métricas:**
- Total de reclamos por empresa
- Reclamos pendientes vs. resueltos
- Tasa de resolución por empresa

**Beneficio:**
- Identificar empresas con mayor volumen de reclamos
- Detectar empresas problemáticas que requieren atención especial
- Comparar tasas de resolución entre empresas

### 11.3.2. Tipos de Reclamos por Empresa

**Capacidad:** Analizar qué tipos de reclamos (CNR, Corte de Suministro, etc.) son más comunes para cada empresa.

**Beneficio:**
- Identificar patrones: "La empresa X tiene muchos casos CNR"
- Priorizar recursos: Asignar más tiempo a empresas con casos más complejos
- Detectar problemas sistémicos: Si una empresa tiene muchos casos del mismo tipo, puede haber un problema operacional

### 11.3.3. Tiempo Promedio de Resolución por Empresa

**Capacidad:** Calcular el tiempo promedio que tarda cada empresa en resolver reclamos.

**Beneficio:**
- Identificar empresas eficientes vs. ineficientes
- Establecer benchmarks de rendimiento
- Detectar empresas que requieren seguimiento más cercano

## 11.4. Análisis por Tipo de Caso

### 11.4.1. Distribución de Tipos de Reclamos

**Capacidad:** Contar cuántos casos hay de cada tipo (CNR, Corte de Suministro, Daño de Equipos, etc.).

**Beneficio:**
- Entender qué tipos de reclamos son más frecuentes
- Asignar recursos según la complejidad de cada tipo
- Identificar tendencias: "Este mes hay más casos CNR que el anterior"

### 11.4.2. Tasa de Éxito por Tipo de Caso

**Capacidad:** Calcular qué porcentaje de cada tipo de reclamo se resuelve a favor del cliente.

**Beneficio:**
- Identificar tipos de reclamos donde las empresas suelen tener razón
- Detectar tipos de reclamos problemáticos que requieren más análisis
- Mejorar la eficiencia: Si un tipo de caso siempre se resuelve igual, se puede automatizar más

## 11.5. Análisis Geográfico

### 11.5.1. Mapa de Calor por Comuna

**Capacidad:** Visualizar en un mapa de Chile qué comunas tienen más reclamos.

**Implementación Futura:**
- Agrupar casos por `suministro.comuna`
- Generar mapa de calor (heatmap) con intensidad basada en cantidad de reclamos
- Permitir zoom y filtrado por tipo de caso, empresa, período

**Beneficio:**
- Identificar zonas geográficas problemáticas
- Detectar patrones regionales: "La comuna X tiene muchos casos CNR"
- Asignar recursos según la carga geográfica
- Detectar problemas de infraestructura: Si una comuna tiene muchos casos, puede haber un problema con la red eléctrica

### 11.5.2. Análisis por Región

**Capacidad:** Agrupar comunas por región y analizar patrones.

**Beneficio:**
- Comparar rendimiento entre regiones
- Identificar problemas regionales que requieren atención de la SEC central
- Detectar correlaciones: "Las regiones del sur tienen más casos en invierno"

## 11.6. Análisis Temporal

### 11.6.1. Tendencias Temporales

**Capacidad:** Analizar cómo varían los reclamos a lo largo del tiempo (días, semanas, meses, años).

**Beneficio:**
- Identificar estacionalidad: "Hay más casos CNR en verano"
- Detectar picos: "Esta semana hubo un aumento del 50% en reclamos"
- Planificar recursos: Saber cuándo se necesitará más personal

### 11.6.2. Análisis de Plazos

**Capacidad:** Analizar cuánto tiempo tardan las empresas en responder y cuánto tiempo tarda la SEC en resolver.

**Beneficio:**
- Identificar empresas que no cumplen plazos
- Mejorar la eficiencia interna: Reducir el tiempo de resolución
- Detectar cuellos de botella en el proceso

## 11.7. Detección de Patrones y Casos Similares

### 11.7.1. Casos Similares

**Capacidad:** Cuando un funcionario abre un caso, el sistema puede mostrar casos similares y sus resoluciones.

**Factores de Similitud:**
- Mismo tipo de caso (CNR, etc.)
- Misma empresa
- Misma comuna
- Documentos similares
- Montos similares

**Beneficio:**
- **Acelerar la resolución**: Ver cómo se resolvieron casos similares
- **Consistencia**: Asegurar que casos similares se resuelvan de forma similar
- **Aprendizaje**: Aprender de casos pasados
- **Reducir errores**: Evitar decisiones inconsistentes

### 11.7.2. Detección de Patrones Anómalos

**Capacidad:** Identificar casos que se desvían de patrones normales.

**Ejemplos:**
- Un cliente que tiene muchos reclamos en poco tiempo
- Una empresa que tiene un aumento súbito en reclamos
- Un tipo de caso que aparece en una comuna donde nunca había aparecido

**Beneficio:**
- **Priorización**: Casos anómalos pueden requerir atención especial
- **Detección temprana**: Identificar problemas antes de que se agraven
- **Investigación**: Casos anómalos pueden revelar problemas sistémicos

## 11.8. Análisis de Clientes Recurrentes

### 11.8.1. Historial de Reclamos por Cliente

**Capacidad:** Ver todos los reclamos de un cliente (persona) a lo largo del tiempo.

**Beneficio:**
- **Contexto completo**: Entender el historial completo del cliente
- **Detectar abusos**: Identificar clientes que hacen reclamos fraudulentos o repetitivos
- **Mejor servicio**: Entender mejor las necesidades del cliente

### 11.8.2. Análisis de Recurrencia

**Capacidad:** Identificar clientes que tienen múltiples reclamos del mismo tipo.

**Beneficio:**
- **Priorización**: Clientes con múltiples reclamos pueden tener problemas reales
- **Eficiencia**: Si un cliente tiene muchos reclamos similares, se puede crear un proceso más eficiente
- **Detección de problemas**: Múltiples reclamos pueden indicar un problema con el suministro

## 11.9. Análisis de Documentos

### 11.9.1. Tipos de Documentos por Tipo de Caso

**Capacidad:** Analizar qué documentos son más comunes en cada tipo de caso.

**Beneficio:**
- **Optimización**: Saber qué documentos buscar primero
- **Detección de faltantes**: Identificar qué documentos faltan más frecuentemente
- **Mejora del proceso**: Optimizar qué documentos se requieren para cada tipo

### 11.9.2. Calidad de Documentos

**Capacidad:** Analizar la calidad de los documentos enviados por las empresas.

**Beneficio:**
- **Identificar empresas problemáticas**: Empresas que envían documentos de baja calidad
- **Mejorar estándares**: Establecer requisitos más claros para documentos
- **Eficiencia**: Reducir tiempo perdido en documentos ilegibles o incompletos

## 11.10. Análisis Predictivo

### 11.10.1. Predicción de Resolución

**Capacidad:** Predecir cómo se resolverá un caso basado en casos históricos similares.

**Beneficio:**
- **Priorización**: Casos con alta probabilidad de resolución a favor del cliente pueden priorizarse
- **Preparación**: Saber qué esperar ayuda a preparar mejor el análisis
- **Eficiencia**: Reducir tiempo en casos con resultado predecible

### 11.10.2. Predicción de Volumen

**Capacidad:** Predecir cuántos reclamos habrá en el futuro basado en tendencias históricas.

**Beneficio:**
- **Planificación de recursos**: Saber cuánto personal se necesitará
- **Preparación**: Anticipar picos de trabajo
- **Optimización**: Asignar recursos de forma más eficiente

## 11.11. Visualizaciones Futuras

### 11.11.1. Dashboard de Análisis

**Componentes:**
- Gráfico de barras: Reclamos por empresa
- Gráfico de líneas: Tendencias temporales
- Mapa de calor: Reclamos por comuna
- Gráfico de pastel: Distribución de tipos de casos
- Tabla: Top 10 empresas con más reclamos
- Gráfico de dispersión: Tiempo de resolución vs. complejidad

### 11.11.2. Reportes Automáticos

**Capacidad:** Generar reportes periódicos (diarios, semanales, mensuales) con estadísticas clave.

**Beneficio:**
- **Visión general**: Entender el estado general del sistema
- **Toma de decisiones**: Datos para decisiones estratégicas
- **Comunicación**: Compartir información con supervisores y otras áreas

## 11.12. Implementación Técnica Futura

### 11.12.1. APIs de Análisis

**Endpoints Futuros:**
- `GET /api/analytics/empresas` - Estadísticas por empresa
- `GET /api/analytics/tipos` - Estadísticas por tipo de caso
- `GET /api/analytics/geografia` - Estadísticas geográficas
- `GET /api/analytics/temporal` - Tendencias temporales
- `GET /api/analytics/similares/{case_id}` - Casos similares
- `GET /api/analytics/patrones` - Detección de patrones

### 11.12.2. Algoritmos de Similitud

**Para encontrar casos similares:**
- Similitud de texto: Comparar contenido de documentos
- Similitud estructural: Comparar estructura del EDN
- Similitud de contexto: Comparar unified_context
- Machine Learning: Entrenar modelos para detectar similitudes

## 11.13. Auditoría Espejo

### 11.13.1. Concepto

La **Auditoría Espejo** es una capacidad avanzada que permite al sistema descargar masivamente boletas oficiales desde portales PIP (Plataforma de Información Pública) para crear una base de datos paralela de fiscalización. Esto transforma el sistema de un revisor pasivo (que solo revisa lo que la empresa envía) a un auditor activo (que contrasta con datos oficiales).

### 11.13.2. Descarga Masiva de Boletas

**Proceso:**
1. El sistema identifica todos los casos con `service_nis` y `empresa` válidos
2. Para cada caso, invoca el scraper correspondiente (`ENELScraper`, `CGEScraper`, etc.)
3. Descarga boletas de los últimos 12-24 meses desde el portal PIP oficial
4. Almacena las boletas en una base de datos paralela (`audit_database`)

**Estructura de Base de Datos Paralela:**
```sql
CREATE TABLE boletas_oficiales (
    id SERIAL PRIMARY KEY,
    nis VARCHAR(50) NOT NULL,
    empresa VARCHAR(100) NOT NULL,
    periodo VARCHAR(7) NOT NULL,  -- "YYYY-MM"
    fecha_descarga TIMESTAMP DEFAULT NOW(),
    file_path TEXT NOT NULL,
    extracted_data JSONB,
    UNIQUE(nis, empresa, periodo)
);
```

### 11.13.3. Detección de Inconsistencias Masivas

**Capacidades:**
- **Comparación Automática**: El sistema compara los montos cobrados en boletas oficiales con los montos reportados en los casos
- **Detección de Discrepancias**: Identifica casos donde la empresa cobró un monto diferente al que aparece en la boleta oficial
- **Análisis Comparativo**: Genera reportes de diferencias empresa vs. oficial

**Ejemplo de Análisis:**
```python
# Para cada caso CNR
monto_caso = caso.monto_disputa
boleta_oficial = get_boleta_oficial(caso.service_nis, caso.empresa, caso.periodo)
monto_oficial = boleta_oficial.monto_cnr

if abs(monto_caso - monto_oficial) > threshold:
    flag_inconsistencia(caso.id, monto_caso, monto_oficial)
```

### 11.13.4. Análisis Comparativo Empresa vs. Oficial

**Métricas Generadas:**
- **Tasa de Inconsistencias**: Porcentaje de casos donde hay diferencias significativas
- **Magnitud de Discrepancias**: Promedio y desviación estándar de las diferencias
- **Patrones por Empresa**: Identificar empresas con mayor tasa de inconsistencias
- **Patrones Temporales**: Detectar períodos donde hay más inconsistencias

**Reporte Automático:**
```json
{
  "periodo": "2024-01",
  "empresa": "ENEL",
  "total_casos": 150,
  "casos_con_inconsistencias": 23,
  "tasa_inconsistencias": 15.3,
  "diferencia_promedio": 8500.0,
  "diferencia_maxima": 45000.0,
  "casos_críticos": [
    {
      "case_id": "240101-000123",
      "monto_empresa": 120000,
      "monto_oficial": 75000,
      "diferencia": 45000,
      "diferencia_porcentual": 60.0
    }
  ]
}
```

### 11.13.5. Beneficios de la Auditoría Espejo

**Para la SEC:**
- **Fiscalización Proactiva**: No espera a que el cliente reclame, detecta inconsistencias automáticamente
- **Detección Temprana**: Identifica problemas antes de que se conviertan en reclamos formales
- **Evidencia Sólida**: Tiene acceso a datos oficiales para contrastar con lo reportado por la empresa
- **Escalabilidad**: Puede auditar miles de casos simultáneamente

**Para el Cliente:**
- **Protección Automática**: El sistema detecta inconsistencias sin que el cliente tenga que reclamar
- **Resolución Rápida**: Casos con evidencia clara se resuelven más rápido
- **Transparencia**: Acceso a datos oficiales para validar cobros

**Para las Empresas:**
- **Incentivo a la Precisión**: Saber que serán auditadas automáticamente incentiva a reportar datos correctos
- **Detección de Errores Propios**: Puede identificar errores en sus propios sistemas

### 11.13.6. Implementación Técnica

**Componentes:**
- **Scraper Scheduler**: Programa que ejecuta descargas masivas periódicamente (diario, semanal)
- **Audit Database**: Base de datos separada para almacenar boletas oficiales
- **Comparison Engine**: Motor que compara datos de casos con boletas oficiales
- **Alert System**: Sistema de alertas para inconsistencias críticas

**Flujo:**
1. Scheduler ejecuta descarga masiva (noche, baja carga)
2. Scrapers descargan boletas para todos los NIS activos
3. Boletas se procesan y almacenan en `audit_database`
4. Comparison Engine compara con casos existentes
5. Alertas se generan para inconsistencias significativas
6. Reportes se generan automáticamente

### 11.13.7. Consideraciones de Privacidad y Seguridad

- **Datos Sensibles**: Las boletas contienen información personal, deben protegerse
- **Acceso Restringido**: Solo funcionarios autorizados pueden acceder a la base de datos de auditoría
- **Retención**: Políticas claras de retención de datos descargados
- **Compliance**: Cumplir con regulaciones de protección de datos

## 11.14. Conclusión

La estructura de base de datos relacional implementada en el sistema habilita un amplio rango de análisis que pueden mejorar la eficiencia del funcionario, acelerar la resolución de casos, detectar problemas antes de que se agraven, proporcionar insights para decisiones estratégicas, mejorar la consistencia en las resoluciones y reducir errores mediante el aprendizaje de casos pasados. Estos análisis transforman el sistema de un simple gestor de casos en una herramienta de inteligencia de negocio que ayuda al funcionario a tomar decisiones más informadas y eficientes.

---

[← Anterior: Utilidades](10_Utilidades.md) | [Siguiente: AI ChatBot →](12_AI_ChatBot.md)

