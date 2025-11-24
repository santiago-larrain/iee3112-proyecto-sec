# Análiticas Futuras: Potencial de la Base de Datos Relacional

## 1. Introducción

La arquitectura de base de datos relacional implementada en el sistema de reclamos SEC (con archivos JSON separados: `personas.json`, `suministros.json`, `casos.json`, `edn.json`, `documentos.json`) permite realizar análisis profundos y detección de patrones que serían imposibles con una estructura de datos aislada. Este documento describe las capacidades analíticas futuras que esta estructura habilita.

## 2. Ventajas de la Estructura Relacional

### 2.1. Relaciones Explícitas

La base de datos relaciona:
- **Personas** con **Casos** (vía `persona_id`)
- **Suministros** con **Casos** (vía `suministro_id`)
- **EDNs** con **Casos** (vía `case_id`)
- **Documentos** con **Casos** (vía `case_id` y `caso_id`)

Estas relaciones permiten:
- **Análisis histórico por cliente**: Ver todos los reclamos de una persona a lo largo del tiempo
- **Análisis por suministro**: Identificar patrones en un NIS específico
- **Análisis cruzado**: Relacionar tipos de reclamos con empresas, comunas, períodos, etc.

### 2.2. Normalización de Datos

La separación de datos en archivos especializados:
- **Reduce redundancia**: La información de una persona se almacena una vez y se referencia
- **Facilita actualizaciones**: Cambios en datos de personas se reflejan automáticamente en todos sus casos
- **Mejora la integridad**: Los datos están centralizados y son consistentes

## 3. Análisis por Empresa

### 3.1. Volumen de Reclamos por Empresa

**Capacidad**: Contar cuántos reclamos recibe cada empresa distribuidora.

**Implementación Futura**:
```python
# Pseudocódigo
empresas_stats = {}
for caso in casos:
    empresa = caso['empresa']
    if empresa not in empresas_stats:
        empresas_stats[empresa] = {
            'total': 0,
            'pendientes': 0,
            'resueltos': 0,
            'tipos': {}
        }
    empresas_stats[empresa]['total'] += 1
    empresas_stats[empresa]['estado'][caso['estado']] += 1
```

**Beneficio para el Funcionario**:
- Identificar empresas con mayor volumen de reclamos
- Detectar si hay empresas problemáticas que requieren atención especial
- Comparar tasas de resolución entre empresas

### 3.2. Tipos de Reclamos por Empresa

**Capacidad**: Analizar qué tipos de reclamos (CNR, Corte de Suministro, etc.) son más comunes para cada empresa.

**Beneficio para el Funcionario**:
- Identificar patrones: "La empresa X tiene muchos casos CNR"
- Priorizar recursos: Asignar más tiempo a empresas con casos más complejos
- Detectar problemas sistémicos: Si una empresa tiene muchos casos del mismo tipo, puede haber un problema operacional

### 3.3. Tiempo Promedio de Resolución por Empresa

**Capacidad**: Calcular el tiempo promedio que tarda cada empresa en resolver reclamos.

**Beneficio para el Funcionario**:
- Identificar empresas eficientes vs. ineficientes
- Establecer benchmarks de rendimiento
- Detectar empresas que requieren seguimiento más cercano

## 4. Análisis por Tipo de Caso

### 4.1. Distribución de Tipos de Reclamos

**Capacidad**: Contar cuántos casos hay de cada tipo (CNR, Corte de Suministro, Daño de Equipos, etc.).

**Beneficio para el Funcionario**:
- Entender qué tipos de reclamos son más frecuentes
- Asignar recursos según la complejidad de cada tipo
- Identificar tendencias: "Este mes hay más casos CNR que el anterior"

### 4.2. Tasa de Éxito por Tipo de Caso

**Capacidad**: Calcular qué porcentaje de cada tipo de reclamo se resuelve a favor del cliente.

**Beneficio para el Funcionario**:
- Identificar tipos de reclamos donde las empresas suelen tener razón
- Detectar tipos de reclamos problemáticos que requieren más análisis
- Mejorar la eficiencia: Si un tipo de caso siempre se resuelve igual, se puede automatizar más

## 5. Análisis Geográfico

### 5.1. Mapa de Calor por Comuna

**Capacidad**: Visualizar en un mapa de Chile qué comunas tienen más reclamos.

**Implementación Futura**:
- Agrupar casos por `suministro.comuna`
- Generar un mapa de calor (heatmap) con intensidad basada en cantidad de reclamos
- Permitir zoom y filtrado por tipo de caso, empresa, período

**Beneficio para el Funcionario**:
- Identificar zonas geográficas problemáticas
- Detectar patrones regionales: "La comuna X tiene muchos casos CNR"
- Asignar recursos según la carga geográfica
- Detectar problemas de infraestructura: Si una comuna tiene muchos casos, puede haber un problema con la red eléctrica

### 5.2. Análisis por Región

**Capacidad**: Agrupar comunas por región y analizar patrones.

**Beneficio para el Funcionario**:
- Comparar rendimiento entre regiones
- Identificar problemas regionales que requieren atención de la SEC central
- Detectar correlaciones: "Las regiones del sur tienen más casos en invierno"

## 6. Análisis Temporal

### 6.1. Tendencias Temporales

**Capacidad**: Analizar cómo varían los reclamos a lo largo del tiempo (días, semanas, meses, años).

**Beneficio para el Funcionario**:
- Identificar estacionalidad: "Hay más casos CNR en verano"
- Detectar picos: "Esta semana hubo un aumento del 50% en reclamos"
- Planificar recursos: Saber cuándo se necesitará más personal

### 6.2. Análisis de Plazos

**Capacidad**: Analizar cuánto tiempo tardan las empresas en responder y cuánto tiempo tarda la SEC en resolver.

**Beneficio para el Funcionario**:
- Identificar empresas que no cumplen plazos
- Mejorar la eficiencia interna: Reducir el tiempo de resolución
- Detectar cuellos de botella en el proceso

## 7. Detección de Patrones y Casos Similares

### 7.1. Casos Similares

**Capacidad**: Cuando un funcionario abre un caso, el sistema puede mostrar casos similares y sus resoluciones.

**Implementación Futura**:
```python
# Pseudocódigo
def encontrar_casos_similares(caso_actual):
    casos_similares = []
    for caso_historico in casos:
        similitud = calcular_similitud(caso_actual, caso_historico)
        # Factores de similitud:
        # - Mismo tipo de caso (CNR, etc.)
        # - Misma empresa
        # - Misma comuna
        # - Documentos similares
        # - Montos similares
        if similitud > umbral:
            casos_similares.append({
                'caso': caso_historico,
                'similitud': similitud,
                'resolucion': caso_historico.get('resolucion')
            })
    return sorted(casos_similares, key=lambda x: x['similitud'], reverse=True)
```

**Beneficio para el Funcionario**:
- **Acelerar la resolución**: Ver cómo se resolvieron casos similares
- **Consistencia**: Asegurar que casos similares se resuelvan de forma similar
- **Aprendizaje**: Aprender de casos pasados
- **Reducir errores**: Evitar decisiones inconsistentes

### 7.2. Detección de Patrones Anómalos

**Capacidad**: Identificar casos que se desvían de patrones normales.

**Ejemplos**:
- Un cliente que tiene muchos reclamos en poco tiempo
- Una empresa que tiene un aumento súbito en reclamos
- Un tipo de caso que aparece en una comuna donde nunca había aparecido

**Beneficio para el Funcionario**:
- **Priorización**: Casos anómalos pueden requerir atención especial
- **Detección temprana**: Identificar problemas antes de que se agraven
- **Investigación**: Casos anómalos pueden revelar problemas sistémicos

## 8. Análisis de Clientes Recurrentes

### 8.1. Historial de Reclamos por Cliente

**Capacidad**: Ver todos los reclamos de un cliente (persona) a lo largo del tiempo.

**Beneficio para el Funcionario**:
- **Contexto completo**: Entender el historial completo del cliente
- **Detectar abusos**: Identificar clientes que hacen reclamos fraudulentos o repetitivos
- **Mejor servicio**: Entender mejor las necesidades del cliente

### 8.2. Análisis de Recurrencia

**Capacidad**: Identificar clientes que tienen múltiples reclamos del mismo tipo.

**Beneficio para el Funcionario**:
- **Priorización**: Clientes con múltiples reclamos pueden tener problemas reales
- **Eficiencia**: Si un cliente tiene muchos reclamos similares, se puede crear un proceso más eficiente
- **Detección de problemas**: Múltiples reclamos pueden indicar un problema con el suministro

## 9. Análisis de Documentos

### 9.1. Tipos de Documentos por Tipo de Caso

**Capacidad**: Analizar qué documentos son más comunes en cada tipo de caso.

**Beneficio para el Funcionario**:
- **Optimización**: Saber qué documentos buscar primero
- **Detección de faltantes**: Identificar qué documentos faltan más frecuentemente
- **Mejora del proceso**: Optimizar qué documentos se requieren para cada tipo

### 9.2. Calidad de Documentos

**Capacidad**: Analizar la calidad de los documentos enviados por las empresas.

**Beneficio para el Funcionario**:
- **Identificar empresas problemáticas**: Empresas que envían documentos de baja calidad
- **Mejorar estándares**: Establecer requisitos más claros para documentos
- **Eficiencia**: Reducir tiempo perdido en documentos ilegibles o incompletos

## 10. Análisis Predictivo

### 10.1. Predicción de Resolución

**Capacidad**: Predecir cómo se resolverá un caso basado en casos históricos similares.

**Beneficio para el Funcionario**:
- **Priorización**: Casos con alta probabilidad de resolución a favor del cliente pueden priorizarse
- **Preparación**: Saber qué esperar ayuda a preparar mejor el análisis
- **Eficiencia**: Reducir tiempo en casos con resultado predecible

### 10.2. Predicción de Volumen

**Capacidad**: Predecir cuántos reclamos habrá en el futuro basado en tendencias históricas.

**Beneficio para el Funcionario**:
- **Planificación de recursos**: Saber cuánto personal se necesitará
- **Preparación**: Anticipar picos de trabajo
- **Optimización**: Asignar recursos de forma más eficiente

## 11. Visualizaciones Futuras

### 11.1. Dashboard de Análisis

**Componentes**:
- Gráfico de barras: Reclamos por empresa
- Gráfico de líneas: Tendencias temporales
- Mapa de calor: Reclamos por comuna
- Gráfico de pastel: Distribución de tipos de casos
- Tabla: Top 10 empresas con más reclamos
- Gráfico de dispersión: Tiempo de resolución vs. complejidad

### 11.2. Reportes Automáticos

**Capacidad**: Generar reportes periódicos (diarios, semanales, mensuales) con estadísticas clave.

**Beneficio para el Funcionario**:
- **Visión general**: Entender el estado general del sistema
- **Toma de decisiones**: Datos para decisiones estratégicas
- **Comunicación**: Compartir información con supervisores y otras áreas

## 12. Ejemplos Prácticos de Análisis

### Ejemplo 1: Detección de Empresa Problemática

**Escenario**: Un funcionario nota que "Empresa X" tiene muchos reclamos este mes.

**Análisis Habilitado**:
1. Ver todos los casos de "Empresa X" en los últimos 6 meses
2. Analizar qué tipos de casos son más comunes
3. Ver en qué comunas ocurren más
4. Comparar con otras empresas del mismo tamaño
5. Identificar si hay un patrón temporal (aumento súbito)

**Resultado**: El funcionario puede identificar si hay un problema sistémico con la empresa o si es una coincidencia.

### Ejemplo 2: Caso Similar

**Escenario**: Un funcionario está analizando un caso CNR en la comuna de Maipú.

**Análisis Habilitado**:
1. El sistema muestra los 5 casos CNR más similares en Maipú
2. Muestra cómo se resolvieron esos casos
3. Muestra qué documentos fueron clave en la resolución
4. Muestra si la misma empresa estuvo involucrada

**Resultado**: El funcionario puede resolver el caso más rápido y de forma más consistente.

### Ejemplo 3: Patrón Geográfico

**Escenario**: Un funcionario nota que hay muchos casos CNR en una comuna específica.

**Análisis Habilitado**:
1. Ver todos los casos CNR en esa comuna
2. Ver si hay una empresa específica involucrada
3. Ver si hay un período específico donde aumentaron
4. Ver si hay clientes recurrentes

**Resultado**: El funcionario puede identificar si hay un problema de infraestructura en esa comuna.

## 13. Implementación Técnica Futura

### 13.1. Almacenamiento de Análisis

Los análisis pueden almacenarse en:
- **Cache en memoria**: Para análisis frecuentes (top empresas, estadísticas diarias)
- **Archivos JSON de resumen**: Para análisis históricos (estadísticas mensuales)
- **Base de datos de análisis**: Para análisis complejos y búsquedas rápidas

### 13.2. APIs de Análisis

Endpoints futuros:
- `GET /api/analytics/empresas` - Estadísticas por empresa
- `GET /api/analytics/tipos` - Estadísticas por tipo de caso
- `GET /api/analytics/geografia` - Estadísticas geográficas
- `GET /api/analytics/temporal` - Tendencias temporales
- `GET /api/analytics/similares/{case_id}` - Casos similares
- `GET /api/analytics/patrones` - Detección de patrones

### 13.3. Algoritmos de Similitud

Para encontrar casos similares, se pueden usar:
- **Similitud de texto**: Comparar contenido de documentos
- **Similitud estructural**: Comparar estructura del EDN
- **Similitud de contexto**: Comparar unified_context
- **Machine Learning**: Entrenar modelos para detectar similitudes

## 14. Conclusión

La estructura de base de datos relacional implementada en el sistema SEC habilita un amplio rango de análisis que pueden:
- **Mejorar la eficiencia** del funcionario
- **Acelerar la resolución** de casos
- **Detectar problemas** antes de que se agraven
- **Proporcionar insights** para decisiones estratégicas
- **Mejorar la consistencia** en las resoluciones
- **Reducir errores** mediante el aprendizaje de casos pasados

Estos análisis transforman el sistema de un simple gestor de casos en una herramienta de inteligencia de negocio que ayuda al funcionario a tomar decisiones más informadas y eficientes.

