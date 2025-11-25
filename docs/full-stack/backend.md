# Documentación Técnica: Backend del Sistema de Análisis de Reclamos SEC

## 1. Visión General

El backend del sistema está implementado en **Python 3.11+** utilizando el framework **FastAPI** para la exposición de servicios REST. Su arquitectura sigue un patrón modular que separa la lógica de negocio en motores especializados (OMC, MIN, MGR) y gestiona la persistencia mediante una estrategia híbrida JSON/SQLite.

## 2. Estructura de Carpetas

```
backend/
├── main.py                    # Punto de entrada FastAPI
├── requirements.txt           # Dependencias Python
├── src/                        # Código fuente principal
│   ├── models.py              # Modelos Pydantic (EDN, CaseSummary, Checklist)
│   ├── engine/                # Motores de procesamiento
│   │   ├── omc/               # Objeto Maestro de Compilación
│   │   │   ├── document_processor.py
│   │   │   ├── pdf_extractor.py
│   │   │   ├── docx_extractor.py
│   │   │   ├── document_classifier.py
│   │   │   └── entity_extractor.py
│   │   ├── min/               # Motor de Inferencia Normativa
│   │   │   ├── rule_engine.py
│   │   │   └── rules/
│   │   │       ├── base_rules.py
│   │   │       └── cnr_rules.py
│   │   └── mgr/               # Motor de Generación de Resoluciones
│   │       └── resolucion_generator.py
│   ├── routes/                 # Endpoints de la API
│   │   └── casos.py
│   ├── generators/             # Generadores de contenido
│   │   └── checklist_generator.py
│   ├── utils/                  # Utilidades compartidas
│   ├── scripts/                # Scripts de procesamiento
│   └── database/               # Gestores de base de datos
│       ├── json_db_manager.py
│       └── db_manager.py
├── templates/                   # Plantillas configurables
│   ├── checklist/             # Configuraciones de checklist (JSON)
│   ├── expediente/            # Esquemas EDN
│   └── resolucion/            # Plantillas de resoluciones (Markdown)
│       └── snippets/          # Fragmentos de argumentos legales
└── data/                       # Datos y archivos
    ├── DataBase/              # Base de datos JSON relacional
    ├── Files/                 # Archivos de casos
    └── sec_reclamos.db        # Base de datos SQLite (opcional)
```

## 3. Componentes Principales

### 3.1. `main.py` - Aplicación FastAPI

**Responsabilidades:**
- Inicialización de la aplicación FastAPI
- Configuración de CORS para comunicación con frontend
- Registro de routers y endpoints
- Configuración de rutas de módulos Python (`sys.path`)

**Configuración:**
- CORS habilitado para `localhost:5173` (Vite) y `localhost:3000`
- Router principal: `/api` con tag `casos`
- Manipulación de `sys.path` para importar módulos desde `src/`

### 3.2. `src/models.py` - Modelos de Datos Pydantic

**Modelos Principales:**

#### `ExpedienteDigitalNormalizado`
Modelo completo del EDN que representa el contrato de datos estandarizado.

**Campos Clave:**
- `compilation_metadata`: Metadatos del procesamiento (case_id, timestamp, status, tipo_caso)
- `unified_context`: Contexto unificado (cliente, suministro, contacto)
- `document_inventory`: Inventario de documentos por nivel (critical, supporting, missing)
- `checklist`: Checklist de validación estructurado en 3 grupos
- `materia`, `monto_disputa`, `empresa`, `fecha_ingreso`, `alertas`

#### `CaseSummary`
Resumen de caso para visualización en Dashboard.

**Campos:**
- `case_id`, `client_name`, `rut_client`, `materia`, `monto_disputa`
- `status`, `fecha_ingreso`, `empresa`

#### `Checklist`
Estructura jerárquica del checklist de validación.

**Grupos:**
- `group_a_admisibilidad`: Lista de `ChecklistItem`
- `group_b_instruccion`: Lista de `ChecklistItem`
- `group_c_analisis`: Lista de `ChecklistItem`

#### `ChecklistItem`
Item individual del checklist con estado y evidencia.

**Campos:**
- `id`, `title`, `status` (CUMPLE/NO_CUMPLE/REVISION_MANUAL)
- `evidence`, `evidence_type`, `description`, `validated`
- `evidence_data`: Datos con deep linking (file_id, page_index, coordinates)

**Enums:**
- `DocumentType`: Tipos de documentos (CARTA_RESPUESTA, ORDEN_TRABAJO, TABLA_CALCULO, etc.)
- `ChecklistStatus`: Estados del checklist
- `CaseStatus`: Estados del caso (PENDIENTE, EN_REVISION, RESUELTO, CERRADO)

### 3.3. `src/routes/casos.py` - Endpoints de la API

**Endpoints Principales:**

#### `GET /api/casos`
Lista todos los casos (resumen para Dashboard).

**Parámetros:**
- `mode`: `test` o `validate` (query param o header `X-App-Mode`)

**Respuesta:** `List[CaseSummary]`

**Lógica:**
- Determina modo desde header o query param
- Carga desde `mock_casos.json` (test) o `DataBase/` (validate)
- Determina estado basado en checklist o BD

#### `GET /api/casos/{case_id}`
Obtiene un caso completo con EDN.

**Respuesta:** `ExpedienteDigitalNormalizado`

**Procesamiento:**
- Aplica `ensure_edn_completeness()` para valores por defecto
- Genera checklist si no existe
- Soporta modo test/validate

#### `PUT /api/casos/{case_id}/documentos/{file_id}`
Actualiza tipo de documento (re-clasificación).

**Body:**
```json
{
  "type": "ORDEN_TRABAJO",
  "custom_name": "OT Personalizada (opcional)"
}
```

**Efectos:**
- Actualiza `type` y `standardized_name` en `documentos.json`
- Recalcula checklist automáticamente
- Recarga caso desde BD

#### `PUT /api/casos/{case_id}/checklist/{item_id}`
Actualiza validación de item del checklist.

**Body:**
```json
{
  "validated": true
}
```

**Persistencia:** En memoria (cache) hasta recarga

#### `PUT /api/casos/{case_id}/contexto`
Actualiza contexto unificado (Sección A).

**Body:**
```json
{
  "client_name": "...",
  "rut_client": "...",
  "email": "...",
  ...
}
```

**Efectos:**
- Guarda en `casos.json`, `personas.json`, `suministros.json`
- Recarga caso desde BD
- Solo disponible en modo validate

#### `POST /api/casos/{case_id}/resolucion`
Genera borrador de resolución.

**Body:**
```json
{
  "template_type": "INSTRUCCION" | "IMPROCEDENTE"
}
```

**Respuesta:** `{ "content": "..." }`

**Lógica:**
- Usa `ResolucionGenerator` para generar desde templates
- Basado en estado del checklist
- Inyecta snippets de argumentos legales

#### `POST /api/casos/{case_id}/cerrar`
Cierra un caso con resolución.

**Body:**
```json
{
  "resolucion_content": "..."
}
```

**Efectos:**
- Actualiza estado a `CERRADO`
- Guarda resolución y fecha de cierre
- Solo disponible en modo validate

#### `GET /api/casos/{case_id}/documentos/{file_id}/preview`
Vista previa de documento.

**Respuesta:** Stream de archivo con headers apropiados

**Lógica:**
- Sirve archivos desde `data/Files/` usando rutas relativas
- Soporta PDF, imágenes, otros formatos
- Headers correctos para visualización inline

### 3.4. `src/engine/omc/` - Objeto Maestro de Compilación

**Componentes:**

#### `document_processor.py`
Orquestador principal del pipeline de procesamiento.

**Flujo:**
1. Sanitización de archivos
2. Extracción de texto (OCR si es necesario)
3. Clasificación por tipo de documento
4. Extracción de entidades específicas por tipo
5. Consolidación en contexto unificado
6. Generación de EDN

#### `pdf_extractor.py`
Extracción de texto de PDFs con información de posición.

**Características:**
- Usa `pdfplumber` para extracción de texto y tablas
- Preserva coordenadas de texto (bbox) para deep linking
- Extrae metadatos (autor, fecha, título)

#### `document_classifier.py`
Clasificación heurística de documentos por tipo.

**Estrategia Multi-Capa:**
- Análisis de nombre de archivo (peso: 0.3)
- Análisis de contenido (peso: 0.5)
- Análisis estructural (peso: 0.2)

**Método:**
- `classify_tipo_caso()`: Determina tipo de caso (CNR, CORTE_SUMINISTRO, etc.)
- Se guarda en `EDN.compilation_metadata.tipo_caso`

#### `entity_extractor.py`
Extracción de entidades (RUT, NIS, direcciones, montos) usando regex.

**Características:**
- Extracción genérica (entidades maestras)
- Extracción específica por tipo de documento
- Retorna `source` con `file_ref`, `page_index`, `coordinates`

### 3.5. `src/engine/min/` - Motor de Inferencia Normativa

#### `rule_engine.py`
Motor principal de reglas de validación.

**Métodos:**
- `load_checklist_config(tipo_caso)`: Carga JSON de configuración según tipo
- `generate_checklist(edn)`: Genera checklist ejecutando reglas
- `_evaluate_item(item_config, edn)`: Evalúa un item ejecutando su regla

**Flujo:**
1. Lee `EDN.compilation_metadata.tipo_caso`
2. Carga JSON correspondiente (`templates/checklist/{tipo_caso}.json`)
3. Para cada item en JSON:
   - Obtiene `rule_ref`
   - Busca función Python en `RULE_REGISTRY`
   - Ejecuta función pasando EDN
   - Retorna estado + evidencia + datos con deep linking

#### `rules/base_rules.py`
Reglas base compartidas entre tipos de casos.

**Reglas:**
- `RULE_CHECK_RESPONSE_DEADLINE`: A.1 - Validación de plazo
- `RULE_CHECK_OT_EXISTS`: B.1 - Existencia de OT
- `RULE_CHECK_PHOTOS_EXISTENCE`: B.2 - Evidencia fotográfica
- `RULE_CHECK_CALCULATION_TABLE`: B.3 - Memoria de cálculo
- `RULE_CHECK_NOTIFICATION_PROOF`: B.4 - Acreditación de notificación

#### `rules/cnr_rules.py`
Reglas específicas para casos CNR.

**Reglas:**
- `RULE_CHECK_FINDING_CONSISTENCY`: C.1.1 - Consistencia del hallazgo
- `RULE_CHECK_ACCURACY_PROOF`: C.1.2 - Prueba de exactitud
- `RULE_CHECK_CIM_VALIDATION`: C.2.1 - Validación del CIM
- `RULE_CHECK_RETROACTIVE_PERIOD`: C.2.2 - Periodo retroactivo
- `RULE_CHECK_TARIFF_CORRECTION`: C.2.3 - Corrección monetaria

#### `checklist_generator.py`
Wrapper que delega la generación al Motor de Inferencia Normativa (MIN).

**Clase `ChecklistGenerator`:**

**Propósito:** Genera checklist estructurado usando el MIN y JSONs configurables.

**Método Principal:**
- `generate_checklist(edn: Dict) -> Dict`: Genera checklist completo usando `RuleEngine`

**Implementación:**
- Inicializa `RuleEngine` internamente
- Convierte `Checklist` (Pydantic) a diccionario para compatibilidad con el frontend
- Ubicación: `src/engine/min/checklist_generator.py`

### 3.6. `src/engine/mgr/` - Motor de Generación de Resoluciones

#### `resolucion_generator.py`
Generador de resoluciones desde templates Markdown.

**Métodos:**
- `load_template(template_name)`: Carga template master (instruccion/improcedente)
- `load_snippet(snippet_name)`: Carga fragmento de argumento legal
- `generate_resolucion(case_data, template_type, custom_content)`: Genera resolución completa

**Templates:**
- `templates/resolucion/master_instruccion.md`
- `templates/resolucion/master_improcedente.md`
- `templates/resolucion/snippets/`: Fragmentos de argumentos (arg_falta_fotos.md, etc.)

### 3.7. `src/database/` - Gestores de Base de Datos

#### `json_db_manager.py`
Gestor de base de datos JSON relacional (prioritario).

**Estructura de Datos:**
- `personas.json`: Dict[RUT → Persona]
- `suministros.json`: Dict["NIS-Comuna" → Suministro]
- `casos.json`: List[Caso] (solo metadatos)
- `edn.json`: Dict[case_id → EDN] (EDNs separados)
- `documentos.json`: List[Documento]

**Métodos:**
- `_load_data()`: Carga inicial de todos los JSON
- `get_caso_by_case_id(case_id)`: Obtiene EDN fusionado con metadatos
- `get_all_casos()`: Obtiene resúmenes de todos los casos
- `reload()`: Recarga todos los datos desde disco
- `reload_case(case_id)`: Recarga un caso específico
- `update_edn(case_id, edn)`: Actualiza un EDN en `edn.json`

#### `db_manager.py`
Gestor de base de datos SQLite (opcional para producción futura).

**Esquema:**
- Tablas: `personas`, `suministros`, `casos`, `documentos`
- Lógica de upsert inteligente
- JSONB para datos flexibles

## 4. Gestión de Persistencia

### 4.1. Estrategia Híbrida

El sistema utiliza una **estrategia híbrida** de persistencia:

1. **Base de Datos JSON Relacional** (Prioritaria - Desarrollo Actual)
   - Ubicación: `backend/data/DataBase/`
   - Archivos: `casos.json`, `edn.json`, `personas.json`, `suministros.json`, `documentos.json`
   - Gestor: `JSONDBManager`

2. **Base de Datos SQLite** (Opcional - Producción Futura)
   - Ubicación: `backend/data/sec_reclamos.db`
   - Gestor: `DBManager`
   - Esquema estrella con JSONB para datos flexibles

### 4.2. Separación de EDN y Metadatos

**Diseño Clave:**
- Los EDNs están separados en `edn.json` para mejor modularidad
- Los metadatos de casos están en `casos.json`
- Esta separación permite:
  - Actualizaciones independientes
  - Mejor rendimiento (no cargar EDN completo cuando solo se necesitan metadatos)
  - Versionado y auditoría de cambios en EDN

### 4.3. Gestión de Cache y Recarga

**Problema Resuelto:**
Inicialmente, los datos se cargaban una sola vez al iniciar, causando que los cambios no se reflejaran hasta reiniciar.

**Solución Implementada:**
- `JSONDBManager.reload()`: Recarga todos los datos desde disco
- `JSONDBManager.reload_case(case_id)`: Recarga un caso específico
- Limpieza de cache en memoria (`cases_store`) después de guardar
- Recarga automática después de cada actualización

## 5. Dependencias Principales

Ver `requirements.txt`:
- `fastapi`: Framework web
- `uvicorn`: Servidor ASGI
- `pydantic`: Validación de datos
- `pdfplumber`: Extracción de PDFs
- `python-docx`: Extracción de DOCX
- `sqlalchemy`: ORM para SQLite
- `python-multipart`: Soporte para uploads

## 6. Configuración y Ejecución

### 6.1. Instalación

```bash
cd reclamos-sec/full-stack/backend
pip install -r requirements.txt
```

### 6.2. Ejecución

```bash
python main.py
# O alternativamente:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en `http://localhost:8000`

### 6.3. Documentación de API

FastAPI genera automáticamente documentación interactiva en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

