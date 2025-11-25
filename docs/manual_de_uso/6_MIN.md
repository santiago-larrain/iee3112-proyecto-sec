# Capítulo 6: MIN (Motor de Inferencia Normativa)

[← Anterior: EDN](5_EDN.md) | [Siguiente: Checklist →](7_Checklist.md)

## 6.1. Definición y Propósito

El **Motor de Inferencia Normativa (MIN)** es el componente del sistema que **genera automáticamente el checklist de validación** para cada reclamo, evaluando si cumple o no con los requisitos normativos establecidos por la SEC. El MIN transforma el EDN en un checklist estructurado con estados de cumplimiento y evidencia identificada.

**Arquitectura Fact-Centric:**
El MIN opera sobre `consolidated_facts` (features) en lugar de buscar información dispersa en documentos. Esto permite que las reglas sean simples y eficientes: `if edn.features.periodo_meses > 12: return FAIL`.

## 6.2. Problema que Resuelve

### 6.2.1. Antes del MIN

**Problemas:**
- El funcionario debe recordar manualmente todas las reglas según el tipo de reclamo
- Revisión manual de cada documento buscando evidencia
- Propenso a errores (fácil olvidar validaciones importantes)
- Inconsistente entre diferentes funcionarios
- No escalable (agregar nuevos tipos requiere entrenar a todos)

### 6.2.2. Con el MIN

**Soluciones:**
- Checklist generado automáticamente en milisegundos
- No se olvida ninguna validación
- Consistente para todos los funcionarios
- Escalable (agregar nuevos tipos solo requiere crear JSON)
- Acceso directo a evidencia sin buscar manualmente

## 6.3. Arquitectura del MIN

### 6.3.1. Componentes Principales

```
┌─────────────────────────────────────────┐
│         ChecklistGenerator               │
│      (Wrapper/Interface Pública)        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         RuleEngine (MIN)                │
│  ┌──────────────────────────────────┐  │
│  │ 1. Lee EDN.tipo_caso            │  │
│  │ 2. Carga JSON correspondiente   │  │
│  │ 3. Para cada item en JSON:       │  │
│  │    - Obtiene rule_ref            │  │
│  │    - Busca función en REGISTRY   │  │
│  │    - Ejecuta función con EDN     │  │
│  │    - Retorna estado + evidencia  │  │
│  └──────────────────────────────────┘  │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│base_rules│ │cnr_rules │ │otros_rules│
└──────────┘ └──────────┘ └──────────┘
```

### 6.3.2. Flujo de Datos

```
EDN (Expediente Digital Normalizado)
    │
    ├─ compilation_metadata.tipo_caso = "CNR"
    ├─ consolidated_facts = { "periodo_meses": 6, "monto_cnr": 86500, ... }
    ├─ evidence_map = { "periodo_meses": [...], "monto_cnr": [...] }
    │
    ▼
RuleEngine.load_checklist_config("CNR")
    │
    ├─ Busca: templates/checklist/cnr.json
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
    ├─ item.rule_ref = "RULE_CHECK_RETROACTIVE_PERIOD"
    │
    ▼
RULE_REGISTRY.get("RULE_CHECK_RETROACTIVE_PERIOD")
    │
    ├─ Retorna: función Python rule_check_retroactive_period()
    │
    ▼
Ejecuta: rule_check_retroactive_period(edn)
    │
    ├─ Lee: edn.consolidated_facts["periodo_meses"]
    ├─ Evalúa: if periodo_meses > 12: return NO_CUMPLE
    │
    ▼
Retorna:
    {
        "status": "CUMPLE",
        "evidence": "Periodo Normativo (6 meses)",
        "evidence_data": {
            "file_id": "Informe_Tecnico.pdf",
            "page_index": 2,
            "snippet": "el periodo comprendido entre 10-09-2023 y 15-05-2024"
        }
    }
    │
    ▼
construir_evidencias_para_regla()
    │
    ├─ Vincula evidencias desde evidence_map
    │
    ▼
ChecklistItem generado
    ├─ id: "C.2.2"
    ├─ title: "Periodo Retroactivo"
    ├─ status: CUMPLE
    ├─ evidence: "Periodo Normativo (6 meses)"
    └─ evidence_data: { file_id, page_index, snippet }
```

## 6.4. Separación de Reglas y Configuración

### 6.4.1. Principio de Diseño

El MIN separa claramente:
- **Estructura Visual (JSON)**: Define QUÉ validar y CÓMO se muestra
- **Lógica de Evaluación (Python)**: Define CÓMO validar

### 6.4.2. Configuración JSON

**Ubicación:** `templates/checklist/{tipo_caso}.json`

**Estructura:**
```json
{
  "metadata": {
    "tipo_caso": "CNR",
    "version": "1.0",
    "description": "Checklist de validación para casos CNR"
  },
  "groups": {
    "group_a_admisibilidad": {
      "title": "Etapa de Admisibilidad y Forma",
      "items": [
        {
          "id": "A.1",
          "title": "Validación de Plazo de Respuesta",
          "description": "Verifica que la respuesta esté dentro de 30 días.",
          "rule_ref": "RULE_CHECK_RESPONSE_DEADLINE",
          "group": "group_a_admisibilidad",
          "order": 1,
          "required": true,
          "evidence_type": "dato"
        }
      ]
    }
  }
}
```

**Campos del Item:**
- `id`: Identificador único (ej: "A.1", "B.2")
- `title`: Título visible en el checklist
- `description`: Texto explicativo estático
- `rule_ref`: Referencia a la función Python
- `group`: Grupo al que pertenece
- `order`: Orden de visualización
- `required`: Si es obligatorio
- `evidence_type`: "dato" o "archivo" (para badge visual)

### 6.4.3. Reglas Python

**Ubicación:** `src/engine/min/rules/`

**Estructura de una Regla (Fact-Centric):**
```python
def rule_check_retroactive_period(edn: Dict[str, Any]) -> Dict[str, Any]:
    """
    C.2.2. Periodo Retroactivo
    Verifica que el periodo de cobro retroactivo no exceda los 12 meses.
    """
    # Consumir desde consolidated_facts (fact-centric)
    features = edn.get("consolidated_facts", {})
    periodo_meses = features.get("periodo_meses")
    
    status = ChecklistStatus.REVISION_MANUAL.value
    evidence = "Periodo de cobro no disponible"
    evidence_data = None
    
    if periodo_meses is not None:
        if periodo_meses <= 12:
            status = ChecklistStatus.CUMPLE.value
            evidence = f"Periodo Normativo ({periodo_meses} meses)"
        else:
            status = ChecklistStatus.NO_CUMPLE.value
            evidence = f"Periodo Excede Normativo ({periodo_meses} meses > 12 meses)"
        
        # Obtener evidencia desde evidence_map
        evidence_map = edn.get("evidence_map", {})
        if "periodo_meses" in evidence_map and evidence_map["periodo_meses"]:
            primera_evidencia = evidence_map["periodo_meses"][0]
            evidence_data = {
                "file_id": primera_evidencia.get("documento"),
                "page_index": primera_evidencia.get("pagina", 0),
                "snippet": primera_evidencia.get("snippet")
            }
    
    return {
        "status": status,
        "evidence": evidence,
        "evidence_data": evidence_data
    }
```

**Características:**
- Toma EDN como input
- **Consume `consolidated_facts`** en lugar de buscar en documentos
- **Usa `evidence_map`** para vincular evidencias
- Retorna estado, evidencia y datos con deep linking
- Independiente y testeable
- **Simple y eficiente**: No necesita buscar en múltiples documentos

### 6.4.4. Registro de Reglas

**Ubicación:** `src/engine/min/rules/__init__.py`

```python
RULE_REGISTRY = {
    # Reglas base
    'RULE_CHECK_RESPONSE_DEADLINE': rule_check_response_deadline,
    'RULE_CHECK_OT_EXISTS': rule_check_ot_exists,
    'RULE_CHECK_PHOTOS_EXISTENCE': rule_check_photos_existence,
    ...
    
    # Reglas CNR
    'RULE_CHECK_CIM_VALIDATION': rule_check_cim_validation,
    ...
}

def get_rule(rule_ref: str):
    """Obtiene una regla por su referencia"""
    return RULE_REGISTRY.get(rule_ref)
```

## 6.5. Tipos de Reglas

### 6.5.1. Reglas Base (Compartidas)

**Ubicación:** `src/engine/min/rules/base_rules.py`

**Reglas:**
- `RULE_CHECK_RESPONSE_DEADLINE`: A.1 - Plazo de respuesta
- `RULE_CHECK_PREVIOUS_CLAIM_TRACE`: A.2 - Trazabilidad
- `RULE_CHECK_MATERIA_CONSISTENCY`: A.3 - Competencia de materia
- `RULE_CHECK_OT_EXISTS`: B.1 - Existencia de OT
- `RULE_CHECK_PHOTOS_EXISTENCE`: B.2 - Evidencia fotográfica
- `RULE_CHECK_CALCULATION_TABLE`: B.3 - Memoria de cálculo
- `RULE_CHECK_NOTIFICATION_PROOF`: B.4 - Acreditación de notificación

**Características:**
- Compartidas entre múltiples tipos de casos
- Lógica genérica aplicable a cualquier reclamo

### 6.5.2. Reglas Específicas CNR

**Ubicación:** `src/engine/min/rules/cnr_rules.py`

**Reglas:**
- `RULE_CHECK_FINDING_CONSISTENCY`: C.1.1 - Consistencia del hallazgo
- `RULE_CHECK_ACCURACY_PROOF`: C.1.2 - Prueba de exactitud
- `RULE_CHECK_CIM_VALIDATION`: C.2.1 - Validación del CIM
- `RULE_CHECK_RETROACTIVE_PERIOD`: C.2.2 - Periodo retroactivo
- `RULE_CHECK_TARIFF_CORRECTION`: C.2.3 - Corrección monetaria

**Características:**
- Específicas para casos CNR
- Lógica especializada en recuperación de consumo

## 6.6. Concepto de Binding

### 6.6.1. Definición

El **Binding** es el proceso mediante el cual el MIN conecta un item de configuración JSON con su función Python correspondiente.

### 6.6.2. Proceso de Binding

1. **Carga de Configuración**: MIN lee JSON según `tipo_caso`
2. **Iteración de Items**: Para cada item en el JSON
3. **Obtención de `rule_ref`**: Lee `item.rule_ref` (ej: "RULE_CHECK_OT_EXISTS")
4. **Búsqueda en Registry**: Busca función en `RULE_REGISTRY`
5. **Ejecución**: Ejecuta función pasando EDN como argumento
6. **Resultado**: Retorna estado, evidencia y datos

### 6.6.3. Ventajas del Binding

**Flexibilidad:**
- Cambiar estructura visual sin tocar código Python
- Cambiar lógica sin tocar JSONs
- Agregar nuevos items solo requiere crear entrada en JSON

**Mantenibilidad:**
- Separación clara de responsabilidades
- Fácil identificar qué regla evalúa qué item
- Testing independiente de reglas

## 6.7. Construcción de Evidencias para Reglas

### 6.7.1. Función `construir_evidencias_para_regla()`

**Propósito:** Junta las evidencias asociadas a los features usados en una regla desde el `evidence_map`.

**Ubicación:** `src/engine/min/rule_engine.py`

**Implementación:**
```python
def construir_evidencias_para_regla(
    rule_ref: str,
    result: Dict[str, Any],
    evidence_map: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Junta las evidencias asociadas a los features usados en una regla.
    """
    evidencias_regla = []
    
    # Mapeo de reglas a features que usan
    rule_to_features = {
        "RULE_CHECK_RETROACTIVE_PERIOD": ["periodo_meses", "fecha_inicio", "fecha_termino"],
        "RULE_CHECK_CIM_VALIDATION": ["historial_12_meses_disponible", "tiene_grafico_consumo"],
        "RULE_CHECK_FINDING_CONSISTENCY": ["origen", "tiene_fotos_irregularidad"],
    }
    
    # Obtener features usados por esta regla
    features_usados = rule_to_features.get(rule_ref, [])
    
    # Recolectar evidencias de los features usados
    for feature in features_usados:
        if feature in evidence_map:
            evidencias_regla.extend(evidence_map[feature])
    
    return evidencias_regla
```

**Integración en Generación de Checklist:**
El `RuleEngine` llama a `construir_evidencias_para_regla()` después de ejecutar cada regla, permitiendo que cada item del checklist tenga acceso directo a las evidencias relevantes del `evidence_map`.

## 6.8. Decisión de Cumplimiento

### 6.8.1. Estados Posibles

**`CUMPLE`:**
- Requisito cumplido según evidencia encontrada
- Documento presente y válido
- Datos consistentes

**`NO_CUMPLE`:**
- Requisito no cumplido
- Documento faltante o inválido
- Datos inconsistentes o contradictorios
- Causal de instrucción a la empresa

**`REVISION_MANUAL`:**
- Datos insuficientes para decisión automática
- Lógica compleja que requiere revisión humana
- Confianza del algoritmo baja (< 70%)

### 6.8.2. Lógica de Decisión

**Ejemplo: Existencia de OT**

```python
def rule_check_ot_exists(edn):
    # Buscar OT en documentos críticos
    ot_docs = [
        doc for doc in edn["document_inventory"]["level_1_critical"]
        if doc["type"] == "ORDEN_TRABAJO"
    ]
    
    if ot_docs:
        # OT encontrada → CUMPLE
        return {
            "status": "CUMPLE",
            "evidence": f"OT Adjunta ({ot_docs[0]['file_id']})",
            "evidence_data": {"file_id": ot_docs[0]["file_id"]}
        }
    else:
        # OT no encontrada → NO_CUMPLE
        return {
            "status": "NO_CUMPLE",
            "evidence": "Falta OT - Imposible acreditar hecho",
            "evidence_data": None
        }
```

### 6.8.3. Evidencia con Deep Linking

Las reglas retornan `evidence_data` con referencias a documentos:

```python
evidence_data = {
    "file_id": "uuid-del-documento",
    "page_index": 0,  # Página donde está la evidencia
    "coordinates": [100, 200, 400, 250]  # Bbox para resaltar
}
```

**Uso:**
- Frontend puede abrir documento en página específica
- Resaltar área relevante (futuro)
- Navegación directa a evidencia

## 6.9. Manejo de Múltiples Tipos de Reclamos

### 6.9.1. Identificación Automática

El OMC determina `tipo_caso` durante el procesamiento y lo guarda en `EDN.compilation_metadata.tipo_caso`.

### 6.9.2. Carga Dinámica de Configuración

El MIN usa el `tipo_caso` para cargar el JSON correcto:

```python
def load_checklist_config(self, tipo_caso: str):
    # Busca: templates/checklist/cnr.json
    # O: templates/checklist/corte_suministro.json
    config_file = self.checklist_dir / f"{tipo_caso.lower()}.json"
    
    if not config_file.exists():
        # Fallback a template.json
        config_file = self.checklist_dir / "template.json"
```

### 6.9.3. Agregar Nuevo Tipo de Reclamo

**Pasos:**
1. Crear JSON de configuración en `templates/checklist/{nuevo_tipo}.json`
2. Implementar reglas específicas en `src/engine/min/rules/{nuevo_tipo}_rules.py` (si es necesario)
3. Registrar reglas en `RULE_REGISTRY`
4. Actualizar clasificador en OMC para identificar el nuevo tipo

**Sin Modificar Código Existente:**
- La estructura de EDN permanece igual
- El flujo de procesamiento no cambia
- La interfaz de usuario se adapta automáticamente

## 6.10. Ventajas del Enfoque Fact-Centric

### 6.10.1. Eficiencia

**Antes (Document-Centric):**
- Las reglas debían buscar información en múltiples documentos
- Procesamiento repetitivo de documentos en cada regla
- Lógica compleja para encontrar datos relevantes

**Ahora (Fact-Centric):**
- Las reglas consumen directamente `consolidated_facts`
- Procesamiento único de documentos en el OMC
- Lógica simple: `if features.periodo_meses > 12: return FAIL`

### 6.10.2. Trazabilidad

- Cada feature tiene su fuente exacta en `evidence_map`
- Snippets permiten verificar rápidamente la evidencia
- Deep linking directo a documentos y páginas específicas

### 6.10.3. Mantenibilidad

- Separación clara: OMC extrae, MIN evalúa
- Reglas más simples y fáciles de entender
- Agregar nuevos features solo requiere actualizar OMC

## 6.11. Ventajas del Enfoque Modular

### 6.11.1. Para el Funcionario

- **Rapidez**: Checklist generado automáticamente en milisegundos
- **Completitud**: No se olvida ninguna validación
- **Consistencia**: Misma lógica para todos
- **Acceso Directo**: Links a evidencia sin buscar manualmente
- **Proceso Uniforme**: Mismo flujo para todos los tipos de reclamos

### 6.11.2. Para el Desarrollo

- **Mantenibilidad**: Cambiar reglas no requiere tocar JSONs
- **Testabilidad**: Reglas Python independientes y testeables
- **Extensibilidad**: Agregar nuevos tipos solo requiere crear JSON
- **Separación de Responsabilidades**: Estructura (JSON) vs Lógica (Python)
- **Reutilización**: Reglas base compartidas entre tipos

### 6.11.3. Para la Organización

- **Escalabilidad**: Fácil agregar nuevos tipos de reclamos
- **Documentación**: JSONs sirven como documentación viva
- **Auditoría**: Todas las validaciones están registradas
- **Evolución**: Reglas pueden mejorarse sin cambiar estructura

## 6.12. Conclusión

El MIN es el cerebro del sistema de validación, permitiendo que el funcionario se enfoque en la revisión en lugar de recordar reglas. La arquitectura modular (JSONs + Reglas Python) permite agregar nuevos tipos de reclamos sin cambiar código existente, mejorar reglas sin tocar estructura visual, y mantener separación clara entre configuración y lógica. El concepto de binding conecta elegantemente la estructura visual con la lógica de evaluación, garantizando flexibilidad y mantenibilidad.

---

[← Anterior: EDN](5_EDN.md) | [Siguiente: Checklist →](7_Checklist.md)

