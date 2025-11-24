# Motor de Inferencia Normativa (MIN) - Explicación Técnica

## Tabla de Contenidos

1. [Visión General](#1-visión-general)
2. [Problema que Resuelve](#2-problema-que-resuelve)
3. [Arquitectura del MIN](#3-arquitectura-del-min)
4. [Flujo de Trabajo del Funcionario](#4-flujo-de-trabajo-del-funcionario)
5. [Manejo de Múltiples Tipos de Reclamos](#5-manejo-de-múltiples-tipos-de-reclamos)
6. [Estructura de Configuración (JSONs)](#6-estructura-de-configuración-jsons)
7. [Sistema de Reglas](#7-sistema-de-reglas)
8. [Deep Linking y Evidencia](#8-deep-linking-y-evidencia)
9. [Ventajas del Enfoque Modular](#9-ventajas-del-enfoque-modular)
10. [Ejemplo Práctico Completo](#10-ejemplo-práctico-completo)

---

## 1. Visión General

El **Motor de Inferencia Normativa (MIN)** es el componente del sistema que **genera automáticamente el checklist de validación** para cada reclamo, evaluando si cumple o no con los requisitos normativos establecidos por la SEC.

### 1.1. Propósito Principal

El MIN existe para **acelerar el procesamiento de reclamos** permitiendo que el funcionario:

- **No tenga que recordar** todas las reglas de validación para cada tipo de reclamo
- **Vea inmediatamente** qué documentos faltan o qué irregularidades existen
- **Tenga acceso directo** a la evidencia que respalda cada validación
- **Trabaje con diferentes tipos de reclamos** sin necesidad de cambiar su flujo de trabajo

### 1.2. Contexto del Problema

Un funcionario de la SEC debe procesar múltiples tipos de reclamos:

- **CNR** (Recuperación de Consumo): Requiere OT, evidencia fotográfica, tabla de cálculo, validación de CIM, etc.
- **CORTE_SUMINISTRO**: Requiere documentos diferentes (notificaciones de corte, comprobantes de pago, etc.)
- **DAÑO_EQUIPOS**: Requiere informes técnicos, fotografías de daños, evaluaciones de responsabilidad
- **ATENCION_COMERCIAL**: Requiere registros de atención, respuestas de la empresa, etc.

Cada tipo tiene **reglas de validación completamente diferentes**, pero el funcionario necesita un **proceso uniforme** para revisarlos.

---

## 2. Problema que Resuelve

### 2.1. Antes del MIN (Problema)

**Escenario sin MIN:**
1. El funcionario recibe un reclamo
2. Debe **recordar manualmente** todas las reglas según el tipo de reclamo
3. Revisa documentos uno por uno buscando evidencia
4. Anota mentalmente qué falta o qué está mal
5. Genera la resolución basándose en su memoria

**Problemas:**
- ❌ **Propenso a errores**: Fácil olvidar validaciones importantes
- ❌ **Lento**: Revisión manual de cada documento
- ❌ **Inconsistente**: Diferentes funcionarios pueden validar diferente
- ❌ **No escalable**: Agregar nuevos tipos de reclamos requiere entrenar a todos

### 2.2. Con el MIN (Solución)

**Escenario con MIN:**
1. El funcionario recibe un reclamo
2. El sistema **automáticamente identifica** el tipo de reclamo (CNR, CORTE_SUMINISTRO, etc.)
3. El MIN **genera un checklist completo** con todas las validaciones relevantes
4. Cada item muestra:
   - ✅/❌/⚠️ Estado automático (CUMPLE/NO_CUMPLE/REVISION_MANUAL)
   - 📋 Descripción del requisito
   - 🔍 Evidencia encontrada (ej: "OT Adjunta (Folio 197803311)")
   - 📎 Link directo al documento que contiene la evidencia
5. El funcionario solo necesita **revisar y validar** los items marcados

**Ventajas:**
- ✅ **Rápido**: Checklist generado en milisegundos
- ✅ **Completo**: No se olvida ninguna validación
- ✅ **Consistente**: Misma lógica para todos los funcionarios
- ✅ **Escalable**: Agregar nuevos tipos solo requiere crear un JSON

---

## 3. Arquitectura del MIN

### 3.1. Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│                    ChecklistGenerator                    │
│              (Wrapper/Interface Pública)                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    RuleEngine (MIN)                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. Lee EDN.compilation_metadata.tipo_caso       │  │
│  │  2. Carga JSON correspondiente (cnr.json, etc.)  │  │
│  │  3. Para cada item en JSON:                      │  │
│  │     - Obtiene rule_ref (ej: "RULE_CHECK_OT")     │  │
│  │     - Busca función Python en RULE_REGISTRY      │  │
│  │     - Ejecuta función pasando EDN                │  │
│  │     - Retorna estado + evidencia + datos         │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ base_rules.py│ │ cnr_rules.py │ │ otros_rules  │
│ (Reglas      │ │ (Reglas      │ │ (Futuro)     │
│  Compartidas)│ │  Específicas)│ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

### 3.2. Flujo de Datos

```
EDN (Expediente Digital Normalizado)
    │
    ├─ compilation_metadata.tipo_caso = "CNR"
    │
    ▼
RuleEngine.load_checklist_config("CNR")
    │
    ├─ Busca: checklist_tipo/cnr.json
    │
    ▼
JSON Configuración
    │
    ├─ groups.group_a_admisibilidad.items[]
    ├─ groups.group_b_instruccion.items[]
    └─ groups.group_c_analisis.items[]
    │
    ▼
Para cada item:
    ├─ item.rule_ref = "RULE_CHECK_OT_EXISTS"
    │
    ▼
RULE_REGISTRY.get("RULE_CHECK_OT_EXISTS")
    │
    ├─ Retorna: función Python rule_check_ot_exists()
    │
    ▼
Ejecuta: rule_check_ot_exists(edn)
    │
    ├─ Analiza: edn.document_inventory
    ├─ Busca: DocumentType.ORDEN_TRABAJO
    │
    ▼
Retorna:
    {
        "status": "CUMPLE",
        "evidence": "OT Adjunta (Folio 197803311)",
        "evidence_data": {
            "file_id": "uuid-123",
            "page_index": 0,
            "coordinates": [100, 200, 400, 250]
        }
    }
    │
    ▼
ChecklistItem generado
    ├─ id: "B.1"
    ├─ title: "Existencia de Orden de Trabajo (OT)"
    ├─ status: CUMPLE
    ├─ evidence: "OT Adjunta (Folio 197803311)"
    ├─ evidence_data: { file_id, page_index, coordinates }
    └─ description: "Debe existir una Orden de Trabajo..."
```

---

## 4. Flujo de Trabajo del Funcionario

### 4.1. Proceso Paso a Paso

#### Paso 1: Acceso al Caso
El funcionario abre un caso desde el Dashboard. El sistema automáticamente:
- Carga el EDN del caso
- Identifica `tipo_caso` (ej: "CNR")
- Llama a `ChecklistGenerator.generate_checklist(edn)`

#### Paso 2: Generación Automática del Checklist
El MIN ejecuta en milisegundos:
1. Carga `checklist_tipo/cnr.json`
2. Ejecuta todas las reglas (A.1, A.2, A.3, B.1, B.2, B.3, B.4, C.1.1, C.1.2, C.2.1, C.2.2, C.2.3)
3. Genera 11 items de checklist con estados automáticos

#### Paso 3: Visualización en Sección C
El funcionario ve el checklist expandible con:
- **Grupo A (Admisibilidad)**: 3 items
- **Grupo B (Instrucción)**: 4 items
- **Grupo C (Análisis)**: 5 items

Cada item muestra:
- ✅/❌/⚠️ Icono de estado
- Título del requisito
- Checkbox "Validado" (para revisión manual)

#### Paso 4: Revisión Detallada
Al expandir un item, el funcionario ve:

1. **📋 Descripción**: Texto estático explicando el requisito
   ```
   "Debe existir una Orden de Trabajo que acredite la visita técnica y el hallazgo en terreno."
   ```

2. **🔍 Evidencia Identificada**: Resultado de la regla ejecutada
   ```
   "OT Adjunta (Folio 197803311)"
   ```

3. **📎 Datos/Contexto**: Deep linking a la evidencia
   - Botón "📄 Abrir Documento (Página 1)"
   - Coordenadas: [100, 200, 400, 250] (si está disponible)

#### Paso 5: Validación Manual
El funcionario:
- Hace clic en "Abrir Documento" → Se abre el PDF en la página correcta
- Verifica que la evidencia sea correcta
- Marca checkbox "Validado" si está conforme
- Si encuentra irregularidades, el item ya está marcado como ❌ NO_CUMPLE

#### Paso 6: Generación de Resolución
El sistema usa el estado del checklist para:
- Si hay items ❌ NO_CUMPLE validados → Genera template "INSTRUCCION"
- Si todo ✅ CUMPLE → Genera template "IMPROCEDENTE"

---

## 5. Manejo de Múltiples Tipos de Reclamos

### 5.1. Identificación Automática del Tipo

El OMC (Objeto Maestro de Compilación) determina `tipo_caso` durante el procesamiento:

```python
# En engine/omc/document_classifier.py
def classify_tipo_caso(document_inventory, unified_context):
    # Heurística 1: CNR
    if "ORDEN_TRABAJO" in doc_types and "TABLA_CALCULO" in doc_types:
        return "CNR"
    
    # Heurística 2: CORTE_SUMINISTRO
    if any("corte" in doc.name.lower() for doc in docs):
        return "CORTE_SUMINISTRO"
    
    # Heurística 3: DAÑO_EQUIPOS
    if "EVIDENCIA_FOTOGRAFICA" in doc_types and "daño" in tags:
        return "DAÑO_EQUIPOS"
    
    # Por defecto
    return "CNR"
```

Este `tipo_caso` se guarda en `EDN.compilation_metadata.tipo_caso`.

### 5.2. Carga Dinámica de Configuración

El MIN usa el `tipo_caso` para cargar el JSON correcto:

```python
# En engine/min/rule_engine.py
def load_checklist_config(self, tipo_caso: str):
    # Busca: checklist_tipo/cnr.json
    # O: checklist_tipo/corte_suministro.json
    # O: checklist_tipo/dano_equipos.json
    config_file = self.checklist_dir / f"{tipo_caso.lower()}.json"
    
    if not config_file.exists():
        # Fallback a template.json
        config_file = self.checklist_dir / "template.json"
```

### 5.3. Ejemplo: Agregar Nuevo Tipo de Reclamo

**Escenario**: Se necesita agregar validación para "ATENCION_COMERCIAL"

**Pasos:**

1. **Crear JSON de configuración**:
   ```json
   // checklist_tipo/atencion_comercial.json
   {
     "metadata": {
       "tipo_caso": "ATENCION_COMERCIAL",
       "version": "1.0"
     },
     "groups": {
       "group_a_admisibilidad": {
         "items": [
           {
             "id": "A.1",
             "title": "Registro de Atención",
             "description": "Debe existir registro de la atención al cliente.",
             "rule_ref": "RULE_CHECK_ATTENTION_RECORD",
             "evidence_type": "archivo"
           }
         ]
       }
     }
   }
   ```

2. **Crear reglas específicas** (si es necesario):
   ```python
   # engine/min/rules/atencion_comercial_rules.py
   def rule_check_attention_record(edn: Dict[str, Any]) -> Dict[str, Any]:
       # Lógica específica para ATENCION_COMERCIAL
       ...
   ```

3. **Registrar reglas**:
   ```python
   # engine/min/rules/__init__.py
   RULE_REGISTRY = {
       ...
       'RULE_CHECK_ATTENTION_RECORD': rule_check_attention_record,
   }
   ```

4. **Actualizar clasificador** (si es necesario):
   ```python
   # engine/omc/document_classifier.py
   def classify_tipo_caso(...):
       # Agregar heurística para ATENCION_COMERCIAL
       ...
   ```

**Resultado**: El sistema automáticamente usará el nuevo checklist cuando detecte `tipo_caso = "ATENCION_COMERCIAL"`.

---

## 6. Estructura de Configuración (JSONs)

### 6.1. Formato del JSON

```json
{
  "metadata": {
    "tipo_caso": "CNR",
    "version": "1.0",
    "description": "Checklist de validación para casos de Recuperación de Consumo (CNR)",
    "last_updated": "2024-01-01"
  },
  "groups": {
    "group_a_admisibilidad": {
      "title": "Etapa de Admisibilidad y Forma",
      "items": [
        {
          "id": "A.1",
          "title": "Validación de Plazo de Respuesta",
          "description": "Verifica que la respuesta de la empresa esté dentro de los 30 días corridos.",
          "rule_ref": "RULE_CHECK_RESPONSE_DEADLINE",
          "group": "group_a_admisibilidad",
          "order": 1,
          "required": true,
          "evidence_type": "dato"
        }
      ]
    },
    "group_b_instruccion": {
      "title": "Etapa de Instrucción (Integridad Probatoria)",
      "items": [...]
    },
    "group_c_analisis": {
      "title": "Etapa de Análisis Técnico-Jurídico (Fondo del Asunto)",
      "items": [...]
    }
  }
}
```

### 6.2. Campos del Item

- **`id`**: Identificador único (ej: "A.1", "B.2")
- **`title`**: Título visible en el checklist
- **`description`**: Texto explicativo estático (mostrado al expandir)
- **`rule_ref`**: Referencia a la función Python (ej: "RULE_CHECK_OT_EXISTS")
- **`group`**: Grupo al que pertenece
- **`order`**: Orden de visualización
- **`required`**: Si es obligatorio
- **`evidence_type`**: "dato" o "archivo" (para el badge visual)

### 6.3. Separación de Responsabilidades

**JSON (Estructura Visual)**:
- Define QUÉ validar
- Define CÓMO se muestra
- NO contiene lógica de negocio

**Python (Lógica de Evaluación)**:
- Define CÓMO validar
- Contiene toda la lógica de negocio
- Es testeable independientemente

---

## 7. Sistema de Reglas

### 7.1. Estructura de una Regla

Todas las reglas siguen el mismo patrón:

```python
def rule_check_ot_exists(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    B.1. Existencia de Orden de Trabajo (OT)
    Verifica la presencia de una Orden de Trabajo en los documentos críticos.
    """
    doc_inventory = edn.get("document_inventory", {})
    
    # Lógica de evaluación
    ot_docs = [
        doc for doc in doc_inventory.get("level_1_critical", [])
        if doc.get("type") == DocumentType.ORDEN_TRABAJO.value
    ]
    
    # Determinar estado
    if ot_docs:
        status = ChecklistStatus.CUMPLE.value
        evidence = "OT Adjunta (Folio 197803311)"
        evidence_data = {
            "file_id": ot_docs[0].get("file_id"),
            "page_index": 0,
            "coordinates": None
        }
    else:
        status = ChecklistStatus.NO_CUMPLE.value
        evidence = "Falta OT - Imposible acreditar hecho"
        evidence_data = None
    
    # Retornar resultado
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }
```

### 7.2. Tipos de Reglas

#### Reglas Base (Compartidas)
Ubicación: `engine/min/rules/base_rules.py`

- `RULE_CHECK_RESPONSE_DEADLINE`: A.1 - Plazo de respuesta
- `RULE_CHECK_PREVIOUS_CLAIM_TRACE`: A.2 - Trazabilidad
- `RULE_CHECK_MATERIA_CONSISTENCY`: A.3 - Competencia de materia
- `RULE_CHECK_OT_EXISTS`: B.1 - Existencia de OT
- `RULE_CHECK_PHOTOS_EXISTENCE`: B.2 - Evidencia fotográfica
- `RULE_CHECK_CALCULATION_TABLE`: B.3 - Memoria de cálculo
- `RULE_CHECK_NOTIFICATION_PROOF`: B.4 - Acreditación de notificación

#### Reglas Específicas CNR
Ubicación: `engine/min/rules/cnr_rules.py`

- `RULE_CHECK_FINDING_CONSISTENCY`: C.1.1 - Consistencia del hallazgo
- `RULE_CHECK_ACCURACY_PROOF`: C.1.2 - Prueba de exactitud
- `RULE_CHECK_CIM_VALIDATION`: C.2.1 - Validación del CIM
- `RULE_CHECK_RETROACTIVE_PERIOD`: C.2.2 - Periodo retroactivo
- `RULE_CHECK_TARIFF_CORRECTION`: C.2.3 - Corrección monetaria

### 7.3. Registro de Reglas

```python
# engine/min/rules/__init__.py
RULE_REGISTRY = {
    # Reglas base
    'RULE_CHECK_RESPONSE_DEADLINE': rule_check_response_deadline,
    'RULE_CHECK_OT_EXISTS': rule_check_ot_exists,
    ...
    
    # Reglas CNR
    'RULE_CHECK_CIM_VALIDATION': rule_check_cim_validation,
    ...
}

def get_rule(rule_ref: str):
    """Obtiene una regla por su referencia"""
    return RULE_REGISTRY.get(rule_ref)
```

---

## 8. Deep Linking y Evidencia

### 8.1. Información de Posición en Documentos

El OMC mejorado captura información de posición (bbox) durante la extracción:

```python
# En engine/omc/pdf_extractor.py
def extract_text(file_path, include_positions=True):
    # Retorna datos con posición por página
    return [
        {
            'page_index': 0,
            'text': "...",
            'words': [
                {
                    'text': '150000',
                    'bbox': [100, 200, 400, 250]  # [x0, y0, x1, y1]
                }
            ]
        }
    ]
```

### 8.2. Evidencia con Deep Linking

Las reglas retornan `evidence_data` con referencias a documentos:

```python
evidence_data = {
    "file_id": "uuid-del-documento",
    "page_index": 0,  # Página donde está la evidencia
    "coordinates": [100, 200, 400, 250]  # Bbox para resaltar
}
```

### 8.3. Visualización en Frontend

El componente `ChecklistItem.vue` muestra:

1. **Descripción**: Texto estático del requisito
2. **Evidencia Identificada**: Resultado de la regla (ej: "OT Adjunta (Folio 197803311)")
3. **Datos/Contexto**: 
   - Botón "📄 Abrir Documento (Página 1)"
   - Al hacer clic, abre el PDF en la página específica
   - Si hay coordenadas, puede resaltar el área (futuro)

---

## 9. Ventajas del Enfoque Modular

### 9.1. Para el Funcionario

✅ **Rapidez**: Checklist generado automáticamente en milisegundos
✅ **Completitud**: No se olvida ninguna validación
✅ **Consistencia**: Misma lógica para todos
✅ **Acceso Directo**: Links a evidencia sin buscar manualmente
✅ **Proceso Uniforme**: Mismo flujo para todos los tipos de reclamos

### 9.2. Para el Desarrollo

✅ **Mantenibilidad**: Cambiar reglas no requiere tocar JSONs
✅ **Testabilidad**: Reglas Python independientes y testeables
✅ **Extensibilidad**: Agregar nuevos tipos solo requiere crear JSON
✅ **Separación de Responsabilidades**: Estructura (JSON) vs Lógica (Python)
✅ **Reutilización**: Reglas base compartidas entre tipos

### 9.3. Para la Organización

✅ **Escalabilidad**: Fácil agregar nuevos tipos de reclamos
✅ **Documentación**: JSONs sirven como documentación viva
✅ **Auditoría**: Todas las validaciones están registradas
✅ **Evolución**: Reglas pueden mejorarse sin cambiar estructura

---

## 10. Ejemplo Práctico Completo

### 10.1. Caso: Reclamo CNR

**Input**: EDN de un caso CNR

```json
{
  "compilation_metadata": {
    "case_id": "231220-000557",
    "tipo_caso": "CNR"
  },
  "document_inventory": {
    "level_1_critical": [
      {
        "type": "ORDEN_TRABAJO",
        "file_id": "uuid-ot-123",
        "original_name": "OT_197803311.pdf"
      },
      {
        "type": "TABLA_CALCULO",
        "file_id": "uuid-tabla-456",
        "original_name": "Calculo_CNR.xlsx"
      }
    ],
    "level_2_supporting": [
      {
        "type": "EVIDENCIA_FOTOGRAFICA",
        "file_id": "uuid-foto-789",
        "original_name": "foto_medidor.jpg"
      }
    ]
  }
}
```

### 10.2. Proceso del MIN

1. **RuleEngine** lee `tipo_caso = "CNR"`
2. Carga `checklist_tipo/cnr.json`
3. Para cada item en el JSON:
   - **Item B.1** (`rule_ref: "RULE_CHECK_OT_EXISTS"`):
     - Ejecuta `rule_check_ot_exists(edn)`
     - Busca `ORDEN_TRABAJO` en `level_1_critical`
     - ✅ Encuentra: `uuid-ot-123`
     - Retorna: `{ status: "CUMPLE", evidence: "OT Adjunta", evidence_data: { file_id: "uuid-ot-123" } }`
   
   - **Item B.2** (`rule_ref: "RULE_CHECK_PHOTOS_EXISTENCE"`):
     - Ejecuta `rule_check_photos_existence(edn)`
     - Cuenta `EVIDENCIA_FOTOGRAFICA` en `level_2_supporting`
     - ✅ Encuentra: 1 foto
     - Retorna: `{ status: "CUMPLE", evidence: "Set Fotográfico (1 imágenes)", evidence_data: { file_ids: ["uuid-foto-789"], count: 1 } }`

4. Genera `Checklist` completo con 11 items

### 10.3. Visualización para el Funcionario

El funcionario ve en la Sección C:

```
Grupo B: Etapa de Instrucción (Integridad Probatoria)

✅ B.1  Existencia de Orden de Trabajo (OT)          [Validado ☑]
   └─ Evidencia: "OT Adjunta"
   └─ 📎 Abrir Documento (Página 1)

✅ B.2  Existencia de Evidencia Fotográfica          [Validado ☑]
   └─ Evidencia: "Set Fotográfico (1 imágenes)"
   └─ 📎 Abrir Documento 1
```

### 10.4. Flujo de Validación

1. Funcionario expande "B.1"
2. Ve evidencia: "OT Adjunta"
3. Hace clic en "Abrir Documento"
4. Se abre `OT_197803311.pdf` en nueva pestaña
5. Verifica que la OT sea correcta
6. Marca checkbox "Validado"
7. Continúa con el siguiente item

### 10.5. Generación de Resolución

Al finalizar la revisión:
- Si todos los items están ✅ CUMPLE → Template "IMPROCEDENTE"
- Si hay items ❌ NO_CUMPLE → Template "INSTRUCCION" con lista de irregularidades

---

## Conclusión

El MIN es el **cerebro del sistema de validación**, permitiendo que:

1. **El funcionario se enfoque en la revisión** en lugar de recordar reglas
2. **El sistema sea escalable** para múltiples tipos de reclamos
3. **La validación sea consistente** entre diferentes funcionarios
4. **El proceso sea rápido** con acceso directo a evidencia

La arquitectura modular (JSONs + Reglas Python) permite:
- Agregar nuevos tipos de reclamos sin cambiar código existente
- Mejorar reglas sin tocar estructura visual
- Mantener separación clara entre configuración y lógica

**Idealmente**, el MIN debería:
- ✅ Soportar todos los tipos de reclamos de la SEC
- ✅ Incluir reglas más sofisticadas (NLP, comparación con históricos)
- ✅ Aprender de validaciones manuales del funcionario
- ✅ Generar reportes de cumplimiento normativo
- ✅ Integrarse con sistemas externos (BD de suministros, tarifas vigentes)

