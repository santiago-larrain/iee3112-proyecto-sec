# Capítulo 7: Checklist

[← Anterior: MIN](6_MIN.md) | [Siguiente: MGR →](8_MGR.md)

## 7.1. Definición y Propósito

El **Checklist de Validación** es la interfaz de usuario resultante del procesamiento del MIN. Presenta de manera estructurada y visual el estado de cumplimiento de todos los requisitos normativos para un caso de reclamo, permitiendo al funcionario revisar, validar y corregir las evaluaciones automáticas.

## 7.2. Estructura Jerárquica

### 7.2.1. Organización en Grupos

El checklist está organizado en **3 grupos secuenciales** que reflejan el proceso de análisis de un reclamo:

1. **Grupo A: Etapa de Admisibilidad y Forma**
2. **Grupo B: Etapa de Instrucción (Integridad Probatoria)**
3. **Grupo C: Etapa de Análisis Técnico-Jurídico (Fondo del Asunto)**

### 7.2.2. Secuencialidad de Grupos

**Principio:** El estado de cada grupo condiciona el siguiente. Si falla la Admisibilidad, no se evalúa el Fondo.

**Lógica:**
- Si Grupo A tiene items NO_CUMPLE → Caso puede ser rechazado sin análisis profundo
- Si Grupo A CUMPLE → Se evalúa Grupo B
- Si Grupo B CUMPLE → Se evalúa Grupo C (análisis técnico-jurídico)

## 7.3. Grupo A: Etapa de Admisibilidad y Forma

### 7.3.1. Objetivo

Verificar que se cumplan los requisitos administrativos y plazos legales antes de entrar al fondo del asunto.

### 7.3.2. Items del Grupo A

#### A.1. Validación de Plazo de Respuesta

**Regla:** `Fecha_Respuesta_Empresa` - `Fecha_Reclamo_Cliente` ≤ 30 días corridos

**Estados Posibles:**
- ✅ **CUMPLE**: "En Plazo (15 días)"
- ❌ **NO_CUMPLE**: "Fuera de Plazo (45 días) - **Causal de Instrucción Inmediata**"

**Fuente:** Metadatos del Caso SEC vs. Fecha extraída de la Carta de Respuesta

#### A.2. Trazabilidad del Reclamo Previo

**Regla:** Existe un `ID_Reclamo_Interno` citado en la Carta de Respuesta que vincula el caso

**Estados Posibles:**
- ✅ **CUMPLE**: "Vinculación Correcta (Ticket #6463468)"
- ⚠️ **REVISION_MANUAL**: "No se detecta referencia a reclamo previo"

#### A.3. Competencia de la Materia

**Regla:** La materia clasificada (`CNR`) coincide con los documentos adjuntos

**Estados Posibles:**
- ✅ **CUMPLE**: "Coherencia Documental (Mat: CNR)"
- ❌ **NO_CUMPLE**: "Incoherencia: Materia 'Corte de Luz' pero documentos son de 'Cobro'"

## 7.4. Grupo B: Etapa de Instrucción (Integridad Probatoria)

### 7.4.1. Objetivo

Verificar que la empresa (el "instruido") haya aportado todas las piezas del expediente exigidas por el Oficio de la SEC.

### 7.4.2. Items del Grupo B

#### B.1. Existencia de Orden de Trabajo (OT)

**Regla:** `EDN.document_inventory.level_1_critical` contiene `TIPO: ORDEN_TRABAJO`

**Estados Posibles:**
- ✅ **CUMPLE**: "OT Adjunta (Folio 197803311)"
- ❌ **NO_CUMPLE**: "Falta OT - **Imposible acreditar hecho**"

**Evidencia:** Link directo al documento OT

#### B.2. Existencia de Evidencia Fotográfica

**Regla:** `EDN.document_inventory.level_2_supporting` contiene `TIPO: EVIDENCIA_FOTOGRAFICA` con `cantidad >= 1`

**Estados Posibles:**
- ✅ **CUMPLE**: "Set Fotográfico (3 imágenes)"
- ⚠️ **REVISION_MANUAL**: "Fotos insuficientes o de baja calidad (OCR confidence < 50%)"
- ❌ **NO_CUMPLE**: "Sin evidencia visual"

#### B.3. Existencia de Memoria de Cálculo

**Regla:** `EDN.document_inventory.level_1_critical` contiene `TIPO: TABLA_CALCULO`

**Estados Posibles:**
- ✅ **CUMPLE**: "Tabla Detallada Disponible"
- ❌ **NO_CUMPLE**: "Falta desglose de deuda"

#### B.4. Acreditación de Notificación

**Regla:** Búsqueda de palabras clave ("Carta Certificada", "Notificación Personal", "Firma") en los documentos adjuntos

**Estados Posibles:**
- ✅ **CUMPLE**: "Cliente Notificado (Ref: Carta Certificada)"
- ⚠️ **REVISION_MANUAL**: "No se acredita entrega de notificación de cobro"

## 7.5. Grupo C: Etapa de Análisis Técnico-Jurídico (Fondo del Asunto)

### 7.5.1. Objetivo

Cruzarse los datos extraídos para validar la legalidad del cobro. Esta es la etapa más compleja y requiere "Inteligencia Lógica".

### 7.5.2. Sub-checklist C.1: Acreditación del Hecho (El Fraude)

#### C.1.1. Consistencia del Hallazgo

**Regla:** La descripción en la OT ("Sello Roto") coincide con las etiquetas de la IA en las Fotos ("broken_seal")

**Estados Posibles:**
- ✅ **CUMPLE**: "Hallazgo Coherente: Sello Adulterado"
- ❌ **NO_CUMPLE**: "Contradicción: OT dice 'Intervención' pero fotos muestran medidor normal"
- ⚠️ **REVISION_MANUAL**: Requiere análisis avanzado de imágenes

#### C.1.2. Prueba de Exactitud (Laboratorio)

**Regla:** Si se cambió el medidor, ¿existe Certificado de Calibración o prueba in-situ en la OT?

**Estados Posibles:**
- ✅ **CUMPLE**: "Prueba In-Situ: Error -81%" [cite: página 211 del PDF]
- ⚠️ **REVISION_MANUAL**: "No se adjunta prueba de error de medida"

### 7.5.3. Sub-checklist C.2: Legalidad del Cobro (Las Matemáticas)

#### C.2.1. Validación del CIM (Consumo Índice Mensual)

**Regla:** Compara el `CIM_Aplicado` (del Excel/Tabla de Cálculo) vs. `Promedio_Historico_Cliente` (de la Base de Datos de Suministros)

**Tolerancia:** Alerta si `CIM` > 150% del `Promedio`

**Estados Posibles:**
- ✅ **CUMPLE**: "CIM Razonable (623 kWh vs Histórico 600 kWh)"
- ❌ **NO_CUMPLE**: "CIM Desproporcionado (623 kWh vs Histórico 150 kWh)"

#### C.2.2. Periodo Retroactivo

**Regla:** `Fecha_Fin_Cobro` - `Fecha_Inicio_Cobro` ≤ 12 meses (Norma general)

**Estados Posibles:**
- ✅ **CUMPLE**: "Periodo Normativo (12 meses)" [cite: página 154 del PDF]
- ❌ **NO_CUMPLE**: "Cobro Excesivo (>12 meses retroactivos)"

#### C.2.3. Corrección Monetaria

**Regla:** Verifica que el valor del kWh usado corresponda a la tarifa vigente en la fecha del cobro

**Estados Posibles:**
- ✅ **CUMPLE**: "Tarifa Vigente Aplicada"
- ⚠️ **REVISION_MANUAL**: "Posible error en valor unitario kWh"

## 7.6. Componente Visual: ChecklistItem

### 7.6.1. Estructura del Item

Cada item del checklist es un componente expandible que muestra:

**Header (Siempre Visible):**
- Icono de estado (✅ CUMPLE, ❌ NO_CUMPLE, ⚠️ REVISION_MANUAL)
- Título del item (ej: "B.1 Existencia de Orden de Trabajo (OT)")
- Checkbox "Validado" (marcado por el funcionario)
- Icono de expandir/colapsar (▶/▼)

**Detalles (Al Expandir):**
- **Evidencia**: Dato o archivo que respalda la validación
- **Descripción**: Explicación del requisito (texto estático del JSON)
- **Tipo de evidencia**: Badge indicando si es "📊 Dato" o "📄 Archivo"
- **Deep Linking**: Botón "📄 Abrir Documento (Página X)" si hay evidencia

### 7.6.2. Estados Visuales

**`CUMPLE`:**
- Borde verde, fondo verde claro (#f1f8e9)
- Icono ✅
- Texto de evidencia en verde

**`NO_CUMPLE`:**
- Borde rojo, fondo rojo claro (#ffebee)
- Icono ❌
- Texto de evidencia en rojo
- Causal de instrucción a la empresa

**`REVISION_MANUAL`:**
- Borde naranja, fondo naranja claro (#fff3e0)
- Icono ⚠️
- Requiere intervención humana

## 7.7. Funcionalidad de Deep Linking

### 7.7.1. Concepto

El **Deep Linking** permite navegar directamente a la evidencia específica dentro de un documento, sin necesidad de buscar manualmente.

### 7.7.2. Información de Posición

El OMC captura información de posición (bbox) durante la extracción:

```json
{
  "file_id": "uuid-del-documento",
  "page_index": 0,
  "coordinates": [100, 200, 400, 250]  // [x0, y0, x1, y1]
}
```

### 7.7.3. Visualización en Frontend

**Componente `ChecklistItem.vue` muestra:**

1. **Descripción**: Texto estático del requisito
2. **Evidencia Identificada**: Resultado de la regla (ej: "OT Adjunta (Folio 197803311)")
3. **Datos/Contexto**: 
   - Botón "📄 Abrir Documento (Página 1)"
   - Al hacer clic, abre el PDF en la página específica
   - Si hay coordenadas, puede resaltar el área (futuro)

### 7.7.4. Implementación

**Backend retorna:**
```json
{
  "evidence_data": {
    "file_id": "uuid-123",
    "page_index": 0,
    "coordinates": [100, 200, 400, 250]
  }
}
```

**Frontend construye URL:**
```
/api/casos/{case_id}/documentos/{file_id}/preview?page=0
```

**Vista Previa:**
- Modal con visor de PDF (iframe)
- Navegación a página específica
- Resaltado de área (futuro con coordenadas)

## 7.8. Proceso de Validación Humana

### 7.8.1. Flujo del Funcionario

1. **Acceso al Caso**: El funcionario abre un caso desde el Dashboard
2. **Visualización del Checklist**: Ve el checklist expandible con estados automáticos
3. **Revisión de Items**: Expande items para ver evidencia
4. **Validación Manual**: Marca checkbox "Validado" después de revisar
5. **Corrección de Errores**: Si encuentra irregularidades, el item ya está marcado como ❌
6. **Continuación**: Continúa con siguiente item o grupo

### 7.8.2. Interacción con el Checklist

**Expandir/Colapsar:**
- Clic en header para expandir/colapsar detalles
- Transición suave con animación

**Validar Item:**
- Checkbox "Validado" para marcar items revisados
- Persistencia en backend
- Estado visual de validación

**Abrir Evidencia:**
- Botón "Abrir Documento" abre modal con vista previa
- Navegación directa a página relevante
- Cierre de modal para continuar revisión

### 7.8.3. Reactividad del Sistema

**Re-clasificación de Documentos:**
- Si el funcionario re-clasifica un documento (Sección B)
- El checklist se recalcula automáticamente
- Items afectados se actualizan en tiempo real

**Ejemplo:**
- Checklist marca "Falta Tabla de Cálculo" (❌)
- Funcionario re-clasifica documento como `TABLA_CALCULO`
- Sistema recalcula checklist
- Item se actualiza a "Tabla Detallada Disponible" (✅)

## 7.9. Persistencia de Validaciones

### 7.9.1. Almacenamiento

**Validaciones Manuales:**
- Checkbox "Validado" se guarda en backend
- Persistencia en memoria (cache) hasta recarga
- Actualización en EDN al cerrar caso

**Estados Automáticos:**
- Generados por MIN en cada recarga
- No se persisten (se recalculan)
- Pueden cambiar si cambian documentos

### 7.9.2. Sincronización

**Flujo:**
1. Funcionario marca item como "Validado"
2. Frontend envía actualización a backend
3. Backend actualiza cache en memoria
4. Frontend recarga caso → Backend devuelve estado actualizado

## 7.10. Impacto en Generación de Resolución

### 7.10.1. Determinación del Tipo de Resolución

El estado del checklist determina el tipo de resolución:

**Si hay items ❌ NO_CUMPLE validados:**
- → Genera template "INSTRUCCION"
- → Inyecta argumentos legales según items fallidos

**Si todo ✅ CUMPLE:**
- → Genera template "IMPROCEDENTE"
- → Ratifica que la empresa actuó conforme a norma

### 7.10.2. Inyección de Argumentos

Cada item NO_CUMPLE tiene un `snippet_ref` que referencia un fragmento de argumento legal:

- `arg_falta_fotos.md`: Argumento para falta de evidencia fotográfica
- `arg_calculo_erroneo.md`: Argumento para cálculo erróneo
- `arg_falta_ot.md`: Argumento para falta de OT

El MGR inyecta estos snippets en la plantilla de resolución.

## 7.11. Conclusión

El Checklist de Validación es la interfaz crítica entre la automatización del MIN y la validación humana del funcionario. Su estructura jerárquica en grupos refleja el proceso de análisis normativo, mientras que la funcionalidad de deep linking acelera la revisión de evidencia. La reactividad del sistema garantiza que las correcciones del funcionario se reflejen inmediatamente, mientras que la persistencia de validaciones preserva el trabajo realizado. El checklist no es solo una visualización, sino el núcleo de la decisión que determina el tipo de resolución final.

---

[← Anterior: MIN](6_MIN.md) | [Siguiente: MGR →](8_MGR.md)

