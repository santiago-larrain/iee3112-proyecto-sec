# Capítulo 5: EDN (Expediente Digital Normalizado)

[← Anterior: DataBase](4_DataBase.md) | [Siguiente: MIN →](6_MIN.md)

## 5.1. Definición y Propósito

El **Expediente Digital Normalizado (EDN)** es el **contrato de datos** estandarizado que sirve como fuente única de verdad para todos los módulos posteriores del sistema. Es un objeto JSON estructurado que representa el estado completo de un caso de reclamo después del procesamiento por el OMC.

## 5.2. Importancia del EDN

### 5.2.1. Fuente Única de Verdad

El EDN actúa como:
- **Input único** para el Motor de Inferencia Normativa (MIN)
- **Input único** para el Motor de Generación de Resoluciones (MGR)
- **Contrato de datos** entre módulos del sistema
- **Representación completa** del estado del caso

### 5.2.2. Ventajas del Diseño

**Normalización:**
- Formato estándar independiente del origen de los documentos
- Estructura predecible y validable
- Facilita integración con sistemas externos

**Completitud:**
- Contiene toda la información necesaria para análisis y resolución
- No requiere consultas adicionales a la base de datos durante procesamiento
- Estado autocontenido del caso

**Versionado:**
- Cada EDN puede versionarse independientemente
- Historial de cambios preservado
- Facilita auditoría y rollback

## 5.3. Estructura del EDN

### 5.3.1. Componentes Principales

```json
{
  "compilation_metadata": { ... },
  "unified_context": { ... },
  "document_inventory": { ... },
  "consolidated_facts": { ... },
  "evidence_map": { ... },
  "checklist": { ... },
  "materia": "Facturación",
  "monto_disputa": 150000.0,
  "empresa": "ENEL",
  "fecha_ingreso": "2023-12-20",
  "alertas": []
}
```

### 5.3.2. `compilation_metadata`

**Propósito:** Metadatos del procesamiento del OMC.

**Estructura:**
```json
{
  "case_id": "231220-000557",
  "processing_timestamp": "2023-12-20T14:30:00Z",
  "status": "COMPLETED",
  "processing_version": "1.0",
  "tipo_caso": "CNR",
  "errors": []
}
```

**Campos:**
- `case_id`: Identificador único del caso (formato SEC)
- `processing_timestamp`: Fecha y hora del procesamiento (ISO 8601)
- `status`: Estado del procesamiento (COMPLETED, COMPLETED_WITH_WARNINGS, FAILED)
- `processing_version`: Versión del procesador OMC
- `tipo_caso`: Tipo de caso identificado (CNR, CORTE_SUMINISTRO, etc.)
- `errors`: Lista de errores encontrados durante procesamiento

### 5.3.3. `unified_context`

**Propósito:** Contexto consolidado extraído de todos los documentos.

**Estructura:**
```json
{
  "rut_client": "12.345.678-9",
  "client_name": "Juan Pérez González",
  "service_nis": "5854164",
  "address_standard": "Av. Providencia 1234, Depto 45",
  "commune": "Providencia",
  "email": "juan.perez@email.com",
  "phone": "+56912345678"
}
```

**Características:**
- **Consolidado**: Valores extraídos de múltiples documentos y normalizados
- **Normalizado**: Formatos estandarizados (RUT con puntos y guión)
- **Completo**: Intenta incluir toda la información disponible

### 5.3.4. `document_inventory`

**Propósito:** Inventario de documentos organizados por nivel de relevancia.

**Estructura:**
```json
{
  "level_1_critical": [ ... ],
  "level_2_supporting": [ ... ],
  "level_0_missing": [ ... ]
}
```

#### Level 1 - Críticos

Documentos esenciales para el análisis del caso.

**Tipos Comunes:**
- `CARTA_RESPUESTA`: Respuesta de la empresa al reclamo
- `ORDEN_TRABAJO`: Evidencia técnica de terreno
- `TABLA_CALCULO`: Memoria de cálculo de facturación

**Estructura de Documento:**
```json
{
  "type": "CARTA_RESPUESTA",
  "file_id": "uuid-1234",
  "original_name": "Respuesta_Reclamo_2642280.pdf",
  "standardized_name": "CARTA_RESPUESTA - Respuesta Reclamo 2642280",
  "file_path": "documents/231220-000557/Respuesta_Reclamo_2642280.pdf",
  "extracted_data": {
    "response_date": "2023-12-21",
    "decision": "IMPROCEDENTE",
    "resolution_number": "12345"
  },
  "metadata": {
    "page_count": 3,
    "file_size": 245678,
    "extraction_confidence": 0.95
  }
}
```

#### Level 2 - Soportantes

Documentos complementarios que corroboran o amplían información.

**Tipos Comunes:**
- `EVIDENCIA_FOTOGRAFICA`: Fotografías de evidencia
- `GRAFICO_CONSUMO`: Gráficos de consumo histórico
- `INFORME_CNR`: Informes técnicos
- `OTROS`: Documentos no clasificados

**Estructura Similar:**
Misma estructura que Level 1, pero con `extracted_data` específico según tipo.

#### Level 0 - Ausentes

Documentos requeridos que no se encontraron durante el procesamiento.

**Estructura:**
```json
{
  "required_type": "ORDEN_TRABAJO",
  "alert_level": "HIGH",
  "description": "No se detectó documento técnico de terreno."
}
```

**Propósito:**
- Alertar al funcionario sobre documentos faltantes
- Guiar la revisión del caso
- Informar al MIN sobre requisitos no cumplidos

### 5.3.5. `consolidated_facts` (alias: `features`)

**Propósito:** Variables de negocio ya destiladas y consolidadas en un objeto plano.

**Motivación Fact-Centric:**
El EDN evoluciona de una arquitectura "centrada en documentos" a una arquitectura **"centrada en hechos" (Fact-Centric)**. En lugar de que el MIN busque información dispersa en múltiples documentos, el OMC extrae y consolida los hechos relevantes en `consolidated_facts`, permitiendo que las reglas del MIN sean simples y directas.

**Estructura:**
```json
{
  "periodo_meses": 6,
  "fecha_inicio": "2023-09-10",
  "fecha_termino": "2024-05-15",
  "origen": "conexion_irregular",
  "descripcion_origen": "bypass",
  "historial_12_meses_disponible": true,
  "historial_fuente": "grafico_informe",
  "tiene_grafico_consumo": true,
  "grafico_fuente": "Informe_Tecnico.pdf",
  "tiene_fotos_irregularidad": true,
  "tiene_foto_medidor": true,
  "tiene_foto_sello": true,
  "monto_cnr": 86500,
  "n_cuotas_totales": 6,
  "n_cuota_actual": 1,
  "notificacion_previa_en_boleta": false,
  "hay_constancia_notarial": false,
  "hay_certificado_laboratorio": true
}
```

**Características:**
- **Plano**: Estructura de diccionario simple, sin anidación compleja
- **Normalizado**: Valores ya procesados y listos para evaluación
- **Completo**: Contiene todas las variables de negocio necesarias para las reglas del MIN
- **Eficiente**: Permite que las reglas sean simples: `if edn.features.periodo_meses > 12: return FAIL`

**Ejemplo de Uso en Reglas:**
```python
def rule_check_retroactive_period(edn: Dict[str, Any]) -> Dict[str, Any]:
    features = edn.get("consolidated_facts", {})
    periodo_meses = features.get("periodo_meses")
    
    if periodo_meses and periodo_meses > 12:
        return {"status": "NO_CUMPLE", "evidence": f"Periodo excede 12 meses"}
    return {"status": "CUMPLE", "evidence": f"Periodo normativo ({periodo_meses} meses)"}
```

### 5.3.6. `evidence_map` (alias: `evidencias`)

**Propósito:** Mapa que vincula cada *fact* en `consolidated_facts` con su fuente exacta en los documentos.

**Estructura:**
```json
{
  "periodo_meses": [
    {
      "tipo": "texto",
      "documento": "Informe_Tecnico.pdf",
      "pagina": 2,
      "snippet": "el periodo comprendido entre 10-09-2023 y 15-05-2024"
    }
  ],
  "origen": [
    {
      "tipo": "texto",
      "documento": "Acta_Inspeccion.pdf",
      "pagina": 1,
      "snippet": "se detecta bypass en conductor fase del medidor"
    }
  ],
  "tiene_fotos_irregularidad": [
    {
      "tipo": "foto",
      "archivo": "Foto1.jpg",
      "etiqueta": "irregularidad_medidor"
    },
    {
      "tipo": "foto",
      "archivo": "Foto2.jpg",
      "etiqueta": "sello_roto"
    }
  ],
  "tiene_grafico_consumo": [
    {
      "tipo": "imagen",
      "documento": "Informe_Tecnico.pdf",
      "pagina": 3,
      "descripcion": "gráfico de consumo histórico de 12 meses"
    }
  ],
  "monto_cnr": [
    {
      "tipo": "texto",
      "documento": "Boleta_Mayo.pdf",
      "pagina": 1,
      "snippet": "Consumos No Registrados: $86.500"
    }
  ]
}
```

**Campos de una Entrada de Evidencia:**
- `tipo`: Tipo de evidencia ("texto", "foto", "imagen")
- `documento`: Nombre del documento o `file_id` donde se encontró
- `archivo`: Nombre del archivo (para fotos)
- `pagina`: Número de página donde se encontró (0-based o 1-based según contexto)
- `snippet`: Fragmento de texto extraído exacto (concepto clave para trazabilidad)
- `descripcion`: Descripción de la evidencia (para imágenes/gráficos)
- `etiqueta`: Etiqueta para fotos (ej: "irregularidad_medidor", "sello_roto")
- `coordinates`: Coordenadas bbox `[x, y, width, height]` para deep linking (opcional)

**Concepto de Snippet:**
El **snippet** es un fragmento de texto extraído exacto que muestra el contexto donde se encontró un hecho. Esto permite:
- **Trazabilidad**: Saber exactamente dónde se encontró cada variable
- **Validación**: El funcionario puede verificar la fuente rápidamente
- **Deep Linking**: El frontend puede abrir el documento en la página específica y resaltar el área relevante

**Uso en Checklist:**
El MIN usa `construir_evidencias_para_regla()` para vincular cada item del checklist con las evidencias relevantes del `evidence_map`, permitiendo que cada validación tenga acceso directo a su fuente.

### 5.3.7. `checklist`

**Propósito:** Checklist de validación generado por el MIN.

**Estructura:**
```json
{
  "group_a_admisibilidad": [ ... ],
  "group_b_instruccion": [ ... ],
  "group_c_analisis": [ ... ]
}
```

**Nota:** Este campo se genera después del procesamiento inicial por el MIN. Ver Capítulo 6 para detalles.

### 5.3.8. Campos Adicionales

**`materia`:**
- Tipo de materia del reclamo (Facturación, Corte de Suministro, etc.)

**`monto_disputa`:**
- Monto en disputa en pesos chilenos

**`empresa`:**
- Nombre de la empresa distribuidora

**`fecha_ingreso`:**
- Fecha de ingreso del reclamo (formato ISO 8601)

**`alertas`:**
- Lista de alertas y advertencias del sistema

## 5.4. Niveles de Inventario Documental

### 5.4.1. Criterios de Clasificación

**Level 1 - Críticos:**
- Documentos sin los cuales no se puede resolver el caso
- Evidencia directa de la decisión o cálculo
- Requeridos por normativa

**Level 2 - Soportantes:**
- Documentos que corroboran información
- Evidencia complementaria
- Útiles pero no esenciales

**Level 0 - Ausentes:**
- Documentos requeridos que no se encontraron
- Alertas de incompletitud
- Guían la revisión del funcionario

### 5.4.2. Impacto en el Checklist

El MIN utiliza los niveles del inventario para:
- Determinar si un requisito se CUMPLE (documento presente en Level 1)
- Generar alertas de NO_CUMPLE (documento requerido en Level 0)
- Evaluar calidad de evidencia (documentos en Level 2)

## 5.5. Generación del EDN

### 5.5.1. Proceso de Construcción

**Entrada:**
- Lista de documentos procesados
- Entidades extraídas
- Metadatos del caso

**Proceso:**
1. Agregar metadatos de compilación
2. Consolidar entidades en `unified_context`
3. Organizar documentos por nivel
4. Detectar documentos faltantes
5. **Extraer y consolidar features** (nuevo - arquitectura fact-centric)
6. **Construir evidence_map** (nuevo - trazabilidad de hechos)
7. Construir EDN final

**Salida:**
- EDN completo y validado

### 5.5.2. Algoritmo de Construcción

```python
def build_edn(case_id: str, processed_documents: List[Dict],
              case_metadata: Dict) -> Dict[str, Any]:
    # 1. Metadatos de compilación
    compilation_metadata = {
        'case_id': case_id,
        'processing_timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': 'COMPLETED',
        'processing_version': '1.0',
        'tipo_caso': classify_tipo_caso(processed_documents),
        'errors': []
    }
    
    # 2. Contexto unificado
    unified_context = consolidate_entities(processed_documents)
    
    # 3. Inventario de documentos
    document_inventory = organize_documents_by_level(processed_documents)
    
    # 4. Documentos faltantes
    document_inventory['level_0_missing'] = detect_missing_documents(
        processed_documents, case_metadata.get('tipo_caso')
    )
    
    # 5. Extraer features consolidados (fact-centric)
    texto_normalizado = consolidate_text_from_documents(processed_documents)
    consolidated_facts, evidence_map = construir_features(
        expediente={'document_inventory': document_inventory},
        texto_normalizado=texto_normalizado,
        boletas=extract_boletas(processed_documents),
        fotos=extract_fotos(processed_documents)
    )
    
    # 6. EDN final
    edn = {
        'compilation_metadata': compilation_metadata,
        'unified_context': unified_context,
        'document_inventory': document_inventory,
        'consolidated_facts': consolidated_facts,  # Nuevo
        'evidence_map': evidence_map,  # Nuevo
        'materia': case_metadata.get('materia'),
        'monto_disputa': extract_max_amount(processed_documents),
        'empresa': case_metadata.get('empresa'),
        'fecha_ingreso': case_metadata.get('fecha_ingreso'),
        'alertas': detect_alerts(unified_context, processed_documents)
    }
    
    return edn
```

## 5.6. Validación del EDN

### 5.6.1. Validaciones de Integridad

**Validaciones Post-Procesamiento:**
1. **RUT válido**: Verificar dígito verificador
2. **NIS válido**: Rango numérico razonable
3. **Fechas consistentes**: `fecha_ingreso` <= `response_date` (si existe)
4. **Montos razonables**: Entre 1.000 y 10.000.000 CLP
5. **Documentos críticos**: Al menos uno de `CARTA_RESPUESTA` o `TABLA_CALCULO`

### 5.6.2. Validación de Esquema

El EDN debe cumplir con un esquema JSON estricto definido en `templates/expediente/edn_schema.json`.

**Validación:**
- Usar Pydantic para validación de tipos
- Verificar campos requeridos
- Validar formatos (fechas, montos, etc.)

## 5.7. Uso del EDN en Módulos Posteriores

### 5.7.1. MIN (Motor de Inferencia Normativa)

**Input:** EDN completo

**Uso:**
- Lee `compilation_metadata.tipo_caso` para cargar configuración
- **Consume `consolidated_facts`** para evaluar reglas (fact-centric)
- **Usa `evidence_map`** para vincular evidencias con items del checklist
- Genera `checklist` basado en reglas

**Output:** EDN actualizado con `checklist` generado

### 5.7.2. MGR (Motor de Generación de Resoluciones)

**Input:** EDN con `checklist` validado

**Uso:**
- Lee estado de items del `checklist`
- Determina tipo de resolución (Instrucción/Improcedente)
- Genera borrador usando templates

**Output:** Resolución generada

### 5.7.3. Interfaz de Usuario

**Input:** EDN completo

**Uso:**
- Muestra `unified_context` en Sección A
- Lista `document_inventory` en Sección B
- Renderiza `checklist` en Sección C
- Muestra resolución en Sección D

## 5.8. Persistencia del EDN

### 5.8.1. Almacenamiento Separado

Los EDNs se almacenan en `edn.json` separado de los metadatos del caso:

**Estructura:**
```json
{
  "231220-000557": { /* EDN completo */ },
  "231221-000558": { /* EDN completo */ }
}
```

**Ventajas:**
- Actualizaciones independientes
- Mejor rendimiento (no cargar EDN completo en listas)
- Versionado y auditoría

### 5.8.2. Actualización del EDN

**Escenarios de Actualización:**
1. **Re-clasificación de documento**: Actualiza `document_inventory`
2. **Validación de checklist**: Actualiza `checklist` con validaciones humanas
3. **Edición de contexto**: Actualiza `unified_context`
4. **Generación de resolución**: Agrega `resolucion` al EDN

**Proceso:**
1. Cargar EDN desde `edn.json`
2. Aplicar cambios
3. Validar EDN actualizado
4. Guardar en `edn.json`
5. Recargar desde disco

## 5.9. Conclusión

El EDN es el contrato de datos fundamental del sistema. Su estructura normalizada y completa permite que todos los módulos posteriores trabajen con la misma fuente de verdad. La organización por niveles del inventario documental facilita la evaluación automática de requisitos, mientras que la separación de almacenamiento optimiza el rendimiento. El EDN garantiza consistencia, trazabilidad y escalabilidad del sistema.

---

[← Anterior: DataBase](4_DataBase.md) | [Siguiente: MIN →](6_MIN.md)

