# Manual Técnico del Sistema Full-Stack de Análisis de Reclamos SEC

## Tabla de Contenidos

1. [Arquitectura General](#1-arquitectura-general)
2. [Interfaz Visual y Paneles](#2-interfaz-visual-y-paneles)
3. [Capacidades y Responsabilidades del Funcionario](#3-capacidades-y-responsabilidades-del-funcionario)
4. [Backend - Detalle Técnico](#4-backend---detalle-técnico)
5. [Frontend - Detalle Técnico](#5-frontend---detalle-técnico)
6. [Base de Datos](#6-base-de-datos)
7. [OMC: Objeto Maestro de Compilación](#7-omc-objeto-maestro-de-compilación)
8. [Guía de Desarrollo](#8-guía-de-desarrollo)

---

## 1. Arquitectura General

### 1.1. Visión General del Sistema

El sistema es una aplicación **Full-Stack** diseñada para que funcionarios de la SEC (Superintendencia de Electricidad y Combustibles) gestionen y analicen reclamos de manera eficiente. El sistema procesa documentos no estructurados, los normaliza en un formato estándar (EDN), y proporciona una interfaz interactiva para su revisión, validación y resolución.

### 1.2. Arquitectura de Capas

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Vue.js 3)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Dashboard   │  │ CasoDetalle   │  │  Componentes │ │
│  │   (Vista)    │  │   (Vista)     │  │  (Secciones) │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         API Service (Axios)                      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                        ↕ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Routes     │  │   Models     │  │  Checklist   │ │
│  │  (API)       │  │  (Pydantic)  │  │  Generator   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Database    │  │  Ingestion   │  │   Scripts    │ │
│  │  Managers    │  │   (OMC)      │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│                    DATA LAYER                           │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  JSON Files  │  │   SQLite     │                    │
│  │  (DataBase/) │  │  (sec_*.db)  │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### 1.3. Flujo de Datos Principal

1. **Ingesta**: Los documentos se procesan mediante el OMC (Objeto Maestro de Compilación) que genera EDNs (Expedientes Digitales Normalizados).
2. **Persistencia**: Los EDNs se almacenan en una base de datos relacional (JSON o SQLite) con esquema estrella.
3. **Visualización**: El frontend consume la API REST para mostrar casos en el Dashboard.
4. **Análisis**: El funcionario revisa, edita y valida información mediante las 4 secciones del caso.
5. **Resolución**: Se genera y firma la resolución final, cerrando el caso.

### 1.4. Tecnologías Principales

- **Backend**: Python 3.11+, FastAPI, Pydantic, SQLAlchemy
- **Frontend**: Vue.js 3, Vue Router, Axios, Vite
- **Base de Datos**: SQLite (producción futura), JSON (desarrollo actual)
- **Procesamiento**: pdfplumber, python-docx, regex para extracción de entidades

---

## 2. Interfaz Visual y Paneles

### 2.1. Estructura de Navegación

La aplicación es una **Single Page Application (SPA)** con dos vistas principales:

#### 2.1.1. Dashboard (`/`)
Panel principal con diseño estilo Mail que muestra todos los casos de reclamos con información resumida.

**Layout:**
- **Panel Izquierdo (Sidebar)**: Panel fijo de ~300px con:
  - **Estadísticas**: Tarjetas con métricas:
    - Total de Casos
    - Pendientes
    - Resueltos
  - **Sección de Análisis**: Placeholder para futuras funcionalidades de análisis
- **Área Principal (Main Content)**: Área flexible con:
  - **Barra de Búsqueda**: Buscador con debouncing que busca en campos del EDN
  - **Filtros**: 
    - Filtro por Estado (Todos, Pendientes, Resueltos)
    - Filtro por Tipo de Caso (Todos, CNR, Otro)
  - **Tabla de Casos**: Tabla interactiva con columnas:
    - ID Caso (SEC)
    - Cliente (Nombre)
    - RUT
    - Materia
    - Monto en Disputa
    - Empresa
    - Estado (con badge de color)
    - Fecha de Ingreso
    - Acciones (botón Abrir)
  - Botón "Abrir" para ver detalles

**Estados Visuales:**
- `PENDIENTE`: Badge naranja (#f57c00)
- `EN_REVISION`: Badge azul (#1976d2)
- `RESUELTO`: Badge verde (#388e3c)
- `CERRADO`: Badge morado (#7b1fa2)

#### 2.1.2. Vista de Detalle de Caso (`/caso/:id`)
Vista completa de un caso individual, dividida en 4 secciones funcionales.

### 2.2. Secciones del Caso Detalle

#### Sección A: Resumen de Contexto
**Propósito**: Mostrar y editar información contextual del caso.

**Componentes:**
- **3 Tarjetas de Información**:
  1. **Cliente**: Nombre, RUT, Email, Teléfono
  2. **Suministro**: Dirección, Comuna, N° Cliente/NIS
  3. **Caso**: ID SEC, Materia, Monto en Disputa, Empresa, Fecha Ingreso

**Funcionalidad:**
- Botón "✏️ Editar" en la esquina superior derecha
- Al activar edición, todos los campos se vuelven editables (inputs)
- Botón cambia a "💾 Guardar" durante la edición
- Los cambios se persisten en `DataBase/casos.json`, `personas.json` y `suministros.json`
- Recarga automática del caso después de guardar

**Diseño Visual:**
- Tarjetas con header con gradiente púrpura
- Iconos distintivos por categoría (👤 Cliente, 🏠 Suministro, 📋 Caso)
- Layout responsive con grid adaptativo

#### Sección B: Gestor Documental Inteligente
**Propósito**: Gestionar y visualizar documentos del caso.

**Componentes:**
- **Nivel 1: Documentos Críticos** (📌):
  - Documentos esenciales para el análisis (CARTA_RESPUESTA, ORDEN_TRABAJO, TABLA_CALCULO)
  - Cada documento muestra:
    - Nombre estandarizado
    - Nombre original
    - Dropdown para cambiar tipo de documento
    - Botón "Ver" para vista previa
- **Nivel 2: Documentos Soportantes** (📎):
  - Documentos complementarios (EVIDENCIA_FOTOGRAFICA, GRAFICO_CONSUMO, OTROS)
- **Nivel 0: Documentos Ausentes** (⚠️):
  - Alertas de documentos requeridos que no se encontraron

**Funcionalidad:**
- **Re-clasificación de Documentos**: Dropdown para cambiar el tipo de documento
  - Al cambiar, se solicita nombre personalizado (opcional)
  - Se actualiza `standardized_name` en `documentos.json`
  - Se recalcula automáticamente el checklist
- **Vista Previa de Documentos**:
  - Modal con visor de PDF (iframe)
  - Visor de imágenes (img tag)
  - Descarga para otros tipos de archivo
  - Endpoint: `GET /api/casos/{case_id}/documentos/{file_id}/preview`

**Diseño Visual:**
- Lista de documentos con iconos por nivel
- Colores distintivos por nivel (rojo crítico, azul soporte, naranja ausente)
- Modal centrado con overlay oscuro

#### Sección C: Checklist de Validación Expandible
**Propósito**: Validar sistemáticamente el cumplimiento de requisitos legales y técnicos.

**Estructura Jerárquica:**
El checklist está organizado en 3 grupos secuenciales:

1. **Grupo A: Etapa de Admisibilidad y Forma**
   - A.1: Validación de Plazo de Respuesta
   - A.2: Trazabilidad del Reclamo Previo
   - A.3: Competencia de la Materia

2. **Grupo B: Etapa de Instrucción (Integridad Probatoria)**
   - B.1: Existencia de Orden de Trabajo (OT)
   - B.2: Existencia de Evidencia Fotográfica
   - B.3: Existencia de Memoria de Cálculo
   - B.4: Acreditación de Notificación

3. **Grupo C: Etapa de Análisis Técnico-Jurídico (Fondo del Asunto)**
   - C.1.1: Consistencia del Hallazgo
   - C.1.2: Prueba de Exactitud (Laboratorio)
   - C.2.1: Validación del CIM (Consumo Índice Mensual)
   - C.2.2: Periodo Retroactivo
   - C.2.3: Corrección Monetaria

**Componente ChecklistItem:**
Cada item del checklist es un componente expandible que muestra:
- **Header**:
  - Icono de estado (✅ CUMPLE, ❌ NO_CUMPLE, ⚠️ REVISION_MANUAL)
  - Título del item
  - Checkbox "Validado" (marcado por el funcionario)
  - Icono de expandir/colapsar (▶/▼)
- **Detalles** (al expandir):
  - Evidencia: Dato o archivo que respalda la validación
  - Descripción: Explicación del requisito
  - Tipo de evidencia: Badge indicando si es "📊 Dato" o "📄 Archivo"

**Estados Visuales:**
- `CUMPLE`: Borde verde, fondo verde claro (#f1f8e9)
- `NO_CUMPLE`: Borde rojo, fondo rojo claro (#ffebee)
- `REVISION_MANUAL`: Borde naranja, fondo naranja claro (#fff3e0)

**Funcionalidad:**
- Clic en header para expandir/colapsar
- Checkbox "Validado" para marcar items revisados manualmente
- El checklist se recalcula automáticamente al cambiar tipos de documentos
- Los cambios se persisten en memoria y se recargan desde la BD

#### Sección D: Motor de Resolución y Respuesta
**Propósito**: Generar, editar y firmar resoluciones finales.

**Componentes:**
- **Selector de Tipo de Resolución**:
  - Dropdown: "Instrucción a la Empresa" o "Improcedente"
  - Botón "Generar Borrador"
- **Editor de Resolución**:
  - Textarea grande (15 filas) para editar el borrador
  - Auto-genera borrador al cargar la vista
  - Reemplaza contenido al cambiar tipo o generar nuevo borrador
- **Botón "Firmar y Cerrar Caso"**:
  - Valida que haya contenido en la resolución
  - Muestra confirmación antes de cerrar
  - Actualiza estado a `CERRADO` en la base de datos
  - Guarda resolución y fecha de cierre
  - Redirige al dashboard

**Funcionalidad:**
- **Generación Automática**: El borrador se genera basado en el estado del checklist
- **Templates Dinámicos**: 
  - Si hay items NO_CUMPLE validados → Template "INSTRUCCION"
  - Si todo CUMPLE → Template "IMPROCEDENTE"
- **Edición Manual**: El funcionario puede editar el borrador antes de firmar
- **Persistencia**: La resolución se guarda en `casos.json` con fecha de firma

**Diseño Visual:**
- Selector con fondo gris claro
- Editor con borde y padding cómodo
- Botón de firma verde destacado
- Estado de carga durante el cierre

### 2.3. Header Global

**Componentes:**
- Título: "Sistema de Análisis de Reclamos SEC"
- Botón de Modo: Toggle entre "🧪 Test" y "✅ Validate"
  - **Test**: Usa datos mock (`mock_casos.json`)
  - **Validate**: Usa casos reales de `DataBase/`
  - El modo se persiste en `localStorage`
- Link "Dashboard": Navegación rápida al inicio

**Diseño Visual:**
- Header con gradiente púrpura (#667eea → #764ba2)
- Botón de modo con colores distintivos (amarillo test, verde validate)

---

## 3. Capacidades y Responsabilidades del Funcionario

### 3.1. Flujo de Trabajo del Funcionario

#### 3.1.1. Revisión Inicial
1. El funcionario accede al Dashboard y ve todos los casos pendientes
2. Puede filtrar por estado para enfocarse en casos específicos
3. Hace clic en "Abrir" para ver el detalle de un caso

#### 3.1.2. Análisis del Caso
1. **Revisa Sección A**: Verifica información del cliente, suministro y caso
2. **Revisa Sección B**: 
   - Visualiza documentos críticos y soportantes
   - Puede ver la vista previa de cada documento
   - Re-clasifica documentos si fueron mal categorizados automáticamente
3. **Revisa Sección C**: 
   - Expande items del checklist para ver evidencia
   - Marca items como "Validados" después de revisión manual
   - Identifica items que NO_CUMPLE para generar instrucciones

#### 3.1.3. Corrección y Actualización
1. **Edita Información Contextual** (Sección A):
   - Activa modo edición
   - Completa campos faltantes (ej: email, teléfono, dirección)
   - Guarda cambios (se persisten en BD)
2. **Re-clasifica Documentos** (Sección B):
   - Cambia tipo de documento si es necesario
   - Opcionalmente personaliza el nombre del documento
   - El checklist se recalcula automáticamente

#### 3.1.4. Generación de Resolución
1. **Revisa Sección D**:
   - El sistema auto-genera un borrador basado en el checklist
   - El funcionario puede cambiar el tipo de resolución (Instrucción/Improcedente)
   - Puede editar manualmente el contenido del borrador
2. **Firma y Cierra**:
   - Revisa el borrador final
   - Hace clic en "Firmar y Cerrar Caso"
   - Confirma la acción
   - El caso cambia a estado `CERRADO` y se guarda la resolución

### 3.2. Responsabilidades Clave

- **Validación de Información**: Verificar que los datos extraídos automáticamente sean correctos
- **Re-clasificación Documental**: Corregir errores de clasificación automática
- **Validación de Checklist**: Marcar items como validados después de revisión manual
- **Completar Información Faltante**: Rellenar campos que el sistema no pudo extraer
- **Generación de Resolución**: Revisar y editar borradores antes de firmar
- **Cierre de Casos**: Finalizar casos con resolución firmada

### 3.3. Modos de Operación

#### Modo Test (🧪)
- **Propósito**: Desarrollo y pruebas
- **Fuente de Datos**: `mock_casos.json`
- **Limitaciones**: 
  - No se pueden editar casos (solo lectura)
  - No se pueden cerrar casos
  - Cambios no se persisten

#### Modo Validate (✅)
- **Propósito**: Trabajo con casos reales
- **Fuente de Datos**: `DataBase/casos.json`, `personas.json`, `suministros.json`, `documentos.json`
- **Capacidades Completas**:
  - Edición de información contextual
  - Re-clasificación de documentos
  - Validación de checklist
  - Generación y firma de resoluciones
  - Cierre de casos
  - Todos los cambios se persisten en la base de datos

---

## 4. Backend - Detalle Técnico

### 4.1. Estructura de Carpetas

```
backend/
├── main.py                 # Punto de entrada FastAPI
├── models.py               # Modelos Pydantic (EDN, CaseSummary, etc.)
├── checklist_generator.py  # Generador de checklist basado en EDN
├── requirements.txt        # Dependencias Python
├── routes/                 # Endpoints de la API
│   ├── __init__.py
│   └── casos.py           # Rutas principales de casos
├── database/              # Gestores de base de datos
│   ├── __init__.py
│   ├── db_manager.py     # SQLite DB Manager
│   └── json_db_manager.py # JSON DB Manager (prioritario)
├── engine/                # Motores de procesamiento
│   ├── omc/              # Objeto Maestro de Compilación (OMC)
│   │   ├── __init__.py
│   │   ├── document_processor.py  # Orquestador principal
│   │   ├── pdf_extractor.py      # Extracción de PDFs con bbox
│   │   ├── docx_extractor.py     # Extracción de DOCX
│   │   ├── document_classifier.py # Clasificación de documentos y tipo_caso
│   │   └── entity_extractor.py   # Extracción de entidades con posición
│   └── min/              # Motor de Inferencia Normativa (MIN)
│       ├── __init__.py
│       ├── rule_engine.py        # Motor principal de reglas
│       └── rules/                # Reglas de validación
│           ├── __init__.py       # Registro de reglas
│           ├── base_rules.py     # Reglas base compartidas
│           └── cnr_rules.py      # Reglas específicas CNR
├── checklist_tipo/        # JSONs de configuración de checklist
│   ├── template.json     # Plantilla base
│   └── cnr.json          # Checklist específico para CNR
├── scripts/               # Scripts de utilidad
│   ├── __init__.py
│   ├── process_example_cases.py  # Procesa casos de ejemplo
│   └── create_json_database.py  # Crea BD JSON desde casos
└── data/                  # Datos y archivos
    ├── DataBase/          # Base de datos JSON relacional
    │   ├── casos.json     # Metadatos de casos (sin EDN embebido)
    │   ├── edn.json       # EDNs separados: {case_id: edn_object}
    │   ├── personas.json
    │   ├── suministros.json
    │   └── documentos.json
    ├── example_cases/     # Casos de ejemplo para procesamiento
    ├── mock_casos.json    # Datos mock para modo test
    └── sec_reclamos.db    # Base de datos SQLite (opcional)
```

### 4.2. Módulos Principales

#### 4.2.1. `main.py` - Aplicación FastAPI

**Responsabilidades:**
- Inicializar la aplicación FastAPI
- Configurar CORS para permitir requests del frontend
- Registrar routers (endpoints)
- Punto de entrada para `uvicorn`

**Configuración:**
- CORS habilitado para `localhost:5173` (Vite) y `localhost:3000`
- Router principal: `/api` con tag `casos`

#### 4.2.2. `models.py` - Modelos de Datos Pydantic

**Modelos Principales:**

- **`ExpedienteDigitalNormalizado`**: Modelo completo del EDN
  - `compilation_metadata`: Metadatos del procesamiento
  - `unified_context`: Contexto unificado (cliente, suministro)
  - `document_inventory`: Inventario de documentos por nivel
  - `checklist`: Checklist de validación (3 grupos)
  - `materia`, `monto_disputa`, `empresa`, `fecha_ingreso`, `alertas`

- **`CaseSummary`**: Resumen para el Dashboard
  - `case_id`, `client_name`, `rut_client`, `materia`, `monto_disputa`, `status`, `fecha_ingreso`, `empresa`

- **`Checklist`**: Estructura jerárquica del checklist
  - `group_a_admisibilidad`: Lista de ChecklistItem
  - `group_b_instruccion`: Lista de ChecklistItem
  - `group_c_analisis`: Lista de ChecklistItem

- **`ChecklistItem`**: Item individual del checklist
  - `id`, `title`, `status` (CUMPLE/NO_CUMPLE/REVISION_MANUAL), `evidence`, `evidence_type`, `description`, `validated`

- **Enums**:
  - `DocumentType`: Tipos de documentos (CARTA_RESPUESTA, ORDEN_TRABAJO, etc.)
  - `ChecklistStatus`: Estados del checklist
  - `CaseStatus`: Estados del caso (PENDIENTE, EN_REVISION, RESUELTO, CERRADO)

- **Request/Response Models**:
  - `DocumentUpdateRequest`: Actualización de tipo de documento
  - `ChecklistItemUpdateRequest`: Actualización de validación
  - `UnifiedContextUpdateRequest`: Actualización de contexto
  - `CerrarCasoRequest`: Cierre de caso con resolución
  - `ResolucionRequest/Response`: Generación de resolución

#### 4.2.3. `routes/casos.py` - Endpoints de la API

**Endpoints Principales:**

1. **`GET /api/casos`**: Lista todos los casos (resumen)
   - Soporta modo test/validate
   - Retorna `List[CaseSummary]`
   - Determina estado basado en checklist o BD

2. **`GET /api/casos/{case_id}`**: Obtiene un caso completo
   - Retorna `ExpedienteDigitalNormalizado`
   - Aplica `ensure_edn_completeness()` para valores por defecto
   - Genera checklist si no existe
   - Soporta modo test/validate

4. **`PUT /api/casos/{case_id}/documentos/{file_id}`**: Actualiza tipo de documento
   - Permite re-clasificación
   - Soporta nombre personalizado
   - Recalcula checklist automáticamente
   - Guarda en `documentos.json`
   - Recarga caso desde BD

4. **`PUT /api/casos/{case_id}/checklist/{item_id}`**: Actualiza validación de item
   - Marca item como validado/no validado
   - Persiste en memoria (cache)

6. **`PUT /api/casos/{case_id}/contexto`**: Actualiza contexto unificado
   - Edita información de cliente, suministro, caso
   - Guarda en `casos.json`, `personas.json`, `suministros.json`
   - Recarga caso desde BD
   - Solo disponible en modo validate

7. **`POST /api/casos/{case_id}/resolucion`**: Genera borrador de resolución
   - Basado en estado del checklist
   - Templates: INSTRUCCION o IMPROCEDENTE
   - Retorna borrador editable

7. **`POST /api/casos/{case_id}/cerrar`**: Cierra un caso
   - Actualiza estado a `CERRADO`
   - Guarda resolución y fecha de cierre
   - Solo disponible en modo validate

9. **`GET /api/casos/{case_id}/documentos/{file_id}/preview`**: Vista previa de documento
   - Sirve archivos desde `example_cases/` o rutas absolutas
   - Soporta PDF, imágenes, otros formatos
   - Headers correctos para visualización inline

**Funciones Helper:**
- `get_app_mode()`: Determina modo desde header o query param
- `get_cases_data_with_mode()`: Obtiene casos según modo
- `get_cases_data()`: Obtiene casos con prioridad (JSON DB → SQLite → Mock)
- `ensure_edn_completeness()`: Asegura valores por defecto en EDN
- `recalculate_checklist()`: Recalcula checklist (usando ChecklistGenerator)
- `_save_document_to_database()`: Guarda documento en `documentos.json` y actualiza EDN en `edn.json`
- `_update_persona_in_database()`: Actualiza persona en `personas.json`
- `_update_suministro_in_database()`: Actualiza suministro en `suministros.json`

**Nota sobre Persistencia:**
- Las actualizaciones de EDN se guardan en `edn.json` (estructura separada)
- Las actualizaciones de metadatos de caso se guardan en `casos.json`
- Se usa `json_db_manager.update_edn()` para actualizar EDNs

**Gestión de Cache:**
- `cases_store`: Diccionario en memoria para cambios temporales
- Se limpia después de guardar en BD para forzar recarga desde disco

#### 4.2.4. `checklist_generator.py` - Generador de Checklist (Wrapper)

**Clase `ChecklistGenerator`:**

**Propósito**: Wrapper que delega la generación al Motor de Inferencia Normativa (MIN).

**Método Principal:**
- `generate_checklist(edn: Dict) -> Dict`: Genera checklist completo usando `RuleEngine`

**Implementación:**
- Inicializa `RuleEngine` internamente
- Convierte `Checklist` (Pydantic) a diccionario para compatibilidad

#### 4.2.5. `engine/min/` - Motor de Inferencia Normativa (MIN)

**Propósito**: Ejecuta reglas de validación basadas en JSONs configurables.

**Componentes:**

1. **`rule_engine.py` - RuleEngine**:
   - `load_checklist_config(tipo_caso)`: Carga JSON de configuración según tipo de caso
   - `generate_checklist(edn)`: Genera checklist ejecutando reglas
   - `_evaluate_item(item_config, edn)`: Evalúa un item ejecutando su regla asociada

2. **`rules/base_rules.py` - Reglas Base**:
   - `rule_check_response_deadline()`: A.1 - Validación de plazo de respuesta
   - `rule_check_previous_claim_trace()`: A.2 - Trazabilidad del reclamo previo
   - `rule_check_materia_consistency()`: A.3 - Competencia de la materia
   - `rule_check_ot_exists()`: B.1 - Existencia de Orden de Trabajo
   - `rule_check_photos_existence()`: B.2 - Existencia de evidencia fotográfica
   - `rule_check_calculation_table()`: B.3 - Existencia de memoria de cálculo
   - `rule_check_notification_proof()`: B.4 - Acreditación de notificación

3. **`rules/cnr_rules.py` - Reglas CNR**:
   - `rule_check_finding_consistency()`: C.1.1 - Consistencia del hallazgo
   - `rule_check_accuracy_proof()`: C.1.2 - Prueba de exactitud
   - `rule_check_cim_validation()`: C.2.1 - Validación del CIM
   - `rule_check_retroactive_period()`: C.2.2 - Periodo retroactivo
   - `rule_check_tariff_correction()`: C.2.3 - Corrección monetaria

**Flujo de Ejecución:**
1. MIN lee `EDN.compilation_metadata.tipo_caso` (ej: "CNR")
2. Carga JSON correspondiente (`checklist_tipo/cnr.json`)
3. Para cada item en el JSON:
   - Obtiene `rule_ref` (ej: "RULE_CHECK_OT_EXISTS")
   - Busca función Python en `RULE_REGISTRY`
   - Ejecuta función pasando EDN como argumento
   - Retorna estado (CUMPLE/NO_CUMPLE/REVISION_MANUAL) + evidencia + datos con deep linking

**Ventajas del Enfoque Modular:**
- JSONs configurables sin código Python
- Reglas testeables independientemente
- Fácil agregar nuevos tipos de casos (solo crear nuevo JSON)
- Lógica de negocio separada de estructura visual

#### 4.2.6. `checklist_tipo/` - Configuración de Checklist

**Archivos:**
- `template.json`: Plantilla base con estructura de 3 grupos
- `cnr.json`: Checklist específico para casos CNR

**Estructura de JSON:**
```json
{
  "metadata": {
    "tipo_caso": "CNR",
    "version": "1.0"
  },
  "groups": {
    "group_a_admisibilidad": {
      "items": [
        {
          "id": "A.1",
          "title": "Validación de Plazo de Respuesta",
          "description": "...",
          "rule_ref": "RULE_CHECK_RESPONSE_DEADLINE",
          "evidence_type": "dato"
        }
      ]
    }
  }
}
```

#### 4.2.7. `engine/omc/` - Objeto Maestro de Compilación (OMC)

**Mejoras Implementadas:**

1. **Información de Posición (bbox)**:
   - `PDFExtractor.extract_text()` ahora soporta `include_positions=True`
   - Retorna datos de posición por página con coordenadas de palabras
   - `EntityExtractor.extract_all()` acepta `positions_data` y retorna `source` con `file_ref`, `page_index`, `coordinates`

2. **Clasificación de Tipo de Caso**:
   - `DocumentClassifier.classify_tipo_caso()` determina tipo (CNR, CORTE_SUMINISTRO, etc.)
   - Se guarda en `EDN.compilation_metadata.tipo_caso`
   - Heurísticas basadas en documentos presentes

3. **Estructura Mejorada**:
   - Módulo movido de `ingestion/` a `engine/omc/`
   - Mantiene compatibilidad con imports anteriores (actualizados en scripts)
   - B.3: Verifica existencia de TABLA_CALCULO
   - B.4: Busca acreditación de notificación (heurística básica)

3. **Grupo C - Análisis Técnico-Jurídico**:
   - C.1.1: Consistencia entre OT y fotos (requiere revisión manual avanzada)
   - C.1.2: Prueba de exactitud (verifica INFORME_CNR)
   - C.2.1: Validación de CIM (requiere comparación con histórico)
   - C.2.2: Periodo retroactivo (verifica que sea ≤ 12 meses)
   - C.2.3: Corrección monetaria (verifica tarifa vigente)

**Estados Generados:**
- `CUMPLE`: Requisito cumplido según evidencia
- `NO_CUMPLE`: Requisito no cumplido (causal de instrucción)
- `REVISION_MANUAL`: Requiere revisión humana (datos insuficientes o lógica compleja)

#### 4.2.5. `database/` - Gestores de Base de Datos

##### `json_db_manager.py` - Gestor de Base de Datos JSON

**Clase `JSONDBManager`:**

**Responsabilidades:**
- Cargar datos desde archivos JSON relacionales
- Proporcionar acceso a casos, personas, suministros, documentos
- Recargar datos después de actualizaciones

**Métodos:**
- `_load_data()`: Carga inicial de todos los JSON (incluyendo `edn.json`)
- `get_caso_by_case_id(case_id)`: Obtiene EDN de un caso fusionado con metadatos del caso
- `get_all_casos()`: Obtiene resúmenes de todos los casos
- `reload()`: Recarga todos los datos desde disco
- `reload_case(case_id)`: Recarga un caso específico desde ambos archivos
- `update_edn(case_id, edn)`: Actualiza un EDN en `edn.json`

**Estructura de Datos:**
- `self.personas`: Dict[RUT → Persona]
- `self.suministros`: Dict["NIS-Comuna" → Suministro]
- `self.casos`: List[Caso] (solo metadatos, sin EDN embebido)
- `self.edns`: Dict[case_id → EDN] (EDNs separados)
- `self.documentos`: List[Documento]

**Métodos Adicionales:**
- `update_edn(case_id, edn)`: Actualiza un EDN en `edn.json`

##### `db_manager.py` - Gestor de Base de Datos SQLite

**Clase `DBManager`:**

**Responsabilidades:**
- Gestionar base de datos SQLite con esquema estrella
- Implementar lógica de upsert inteligente
- Proporcionar acceso a datos relacionales

**Esquema de Tablas:**
- `personas`: RUT (PK), nombre, email, telefono
- `suministros`: NIS + Comuna (PK), direccion, numero_cliente
- `casos`: case_id (PK), persona_id (FK), suministro_id (FK), empresa, materia, monto_disputa, fecha_ingreso, estado, edn_json (JSONB)
- `documentos`: id (PK), caso_id (FK), file_id, original_name, type, level, file_path, extracted_data (JSONB), metadata (JSONB)

**Métodos Upsert:**
- `upsert_persona()`: Inserta o actualiza persona por RUT
- `upsert_suministro()`: Inserta o actualiza suministro por NIS+Comuna
- `upsert_caso()`: Inserta o actualiza caso por case_id
- `upsert_documento()`: Inserta o actualiza documento por caso_id+file_id

**Métodos de Consulta:**
- `get_all_casos()`: Lista todos los casos con información resumida
- `get_caso_by_case_id()`: Obtiene EDN completo de un caso

**Nota**: Actualmente el sistema prioriza `JSONDBManager` sobre `DBManager` para desarrollo. SQLite se mantiene como opción para producción futura.

#### 4.2.8. Modelos Extendidos

**Nuevos Modelos en `models.py`:**

- **`SourceReference`**: Referencia a fuente de dato extraído
  - `file_ref`: file_id del documento
  - `page_index`: Índice de página (0-based)
  - `coordinates`: [x, y, width, height] para bbox

- **`ExtractedDataWithSource`**: Dato con referencia a fuente
  - `value`: Valor extraído
  - `source`: SourceReference opcional

- **`ChecklistItem` extendido**:
  - `evidence_data`: Datos con deep linking (file_id, page_index, coordinates)
  - `rule_ref`: Referencia a la regla que lo generó

- **`CompilationMetadata` extendido**:
  - `tipo_caso`: Tipo de caso (CNR, CORTE_SUMINISTRO, etc.)

Este módulo implementa el "black box" de procesamiento de documentos. Para documentación detallada, ver [Sección 7: OMC](#7-omc-objeto-maestro-de-compilación) y el documento `OMC_Explained.md`.

**Componentes Principales:**

- **`document_processor.py`**: Orquestador principal que coordina el pipeline completo
- **`pdf_extractor.py`**: Extracción de texto de PDFs usando `pdfplumber`
- **`docx_extractor.py`**: Extracción de texto de DOCX usando `python-docx`
- **`document_classifier.py`**: Clasificación heurística de documentos por tipo
- **`entity_extractor.py`**: Extracción de entidades (RUT, NIS, direcciones, montos) usando regex

**Flujo de Procesamiento:**
1. Sanitización de archivos
2. Extracción de texto (OCR si es necesario)
3. Clasificación por tipo de documento
4. Extracción de entidades específicas por tipo
5. Consolidación en contexto unificado
6. Generación de EDN

#### 4.2.7. `scripts/` - Scripts de Utilidad

##### `process_example_cases.py`
**Propósito**: Procesar casos de ejemplo y almacenarlos en la base de datos.

**Funcionalidad:**
- Escanea `data/example_cases/`
- Procesa cada carpeta como un caso
- Usa `DocumentProcessor` para generar EDNs
- Almacena en SQLite usando `DBManager`
- Logging detallado del proceso

**Uso:**
```bash
cd backend
python scripts/process_example_cases.py
```

##### `create_json_database.py`
**Propósito**: Crear base de datos JSON relacional desde casos de ejemplo.

**Funcionalidad:**
- Extrae información de casos desde nombres de archivos y estructura
- Genera `personas.json`, `suministros.json`, `casos.json`, `documentos.json`
- Organiza documentos por nivel (critical, supporting, missing)
- Crea relaciones entre entidades

**Uso:**
```bash
cd backend
python scripts/create_json_database.py
```

### 4.3. Dependencias Principales

Ver `requirements.txt`:
- `fastapi`: Framework web
- `uvicorn`: Servidor ASGI
- `pydantic`: Validación de datos
- `pdfplumber`: Extracción de PDFs
- `python-docx`: Extracción de DOCX
- `sqlalchemy`: ORM para SQLite
- `python-multipart`: Soporte para uploads

---

## 5. Frontend - Detalle Técnico

### 5.1. Estructura de Carpetas

```
frontend/
├── index.html              # HTML base
├── vite.config.js          # Configuración de Vite
├── package.json            # Dependencias npm
├── src/
│   ├── main.js            # Punto de entrada Vue
│   ├── App.vue            # Componente raíz
│   ├── router/
│   │   └── index.js       # Configuración de rutas
│   ├── services/
│   │   └── api.js         # Servicio de API (Axios)
│   ├── views/             # Vistas principales
│   │   ├── Dashboard.vue  # Panel de casos
│   │   └── CasoDetalle.vue # Vista de detalle
│   └── components/        # Componentes reutilizables
│       ├── SeccionA.vue   # Resumen de contexto
│       ├── SeccionB.vue    # Gestor documental
│       ├── SeccionC.vue    # Checklist
│       ├── ChecklistItem.vue # Item de checklist
│       └── SeccionD.vue    # Motor de resolución
```

### 5.2. Módulos Principales

#### 5.2.1. `main.js` - Punto de Entrada

**Responsabilidades:**
- Crear instancia de aplicación Vue
- Registrar router
- Montar aplicación en `#app`

#### 5.2.2. `App.vue` - Componente Raíz

**Funcionalidad:**
- Header global con título y navegación
- Toggle de modo Test/Validate
- Persistencia de modo en `localStorage`
- Router-view para vistas dinámicas

**Estilos Globales:**
- Reset CSS básico
- Fuentes del sistema
- Colores y gradientes principales

#### 5.2.3. `router/index.js` - Enrutamiento

**Rutas:**
- `/`: Dashboard (lista de casos)
- `/caso/:id`: CasoDetalle (vista de detalle)

**Configuración:**
- History mode habilitado
- Props automáticas para rutas con parámetros

#### 5.2.4. `services/api.js` - Servicio de API

**Clase `casosAPI`:**

**Métodos:**
- `getCasos(tipoCaso)`: Obtiene lista de casos, opcionalmente filtrados por tipo
- `searchCasos(query)`: Busca casos por texto en campos del EDN
- `getCaso(caseId)`: Obtiene caso completo
- `updateDocumento(caseId, fileId, tipo, customName)`: Actualiza documento
- `updateChecklistItem(caseId, itemId, validated)`: Actualiza checklist
- `updateUnifiedContext(caseId, updates)`: Actualiza contexto
- `generarResolucion(caseId, templateType, content)`: Genera borrador
- `cerrarCaso(caseId, resolucionContent)`: Cierra caso

**Interceptor Axios:**
- Agrega header `X-App-Mode` en cada request
- Agrega query param `mode` para compatibilidad
- Lee modo desde `localStorage`

#### 5.2.5. `views/Dashboard.vue` - Panel Principal

**Layout:**
- Diseño estilo Mail con sidebar izquierdo fijo y área principal flexible
- Usa componentes: `Sidebar.vue`, `SearchBar.vue`, `FilterBar.vue`, `CasesTable.vue`

**Funcionalidad:**
- Carga lista de casos al montar
- Búsqueda con debouncing (300ms) que busca en campos del EDN
- Filtros por estado y tipo de caso
- Estadísticas en sidebar que se actualizan con filtros
- Tabla interactiva con casos
- Navegación a detalle de caso

**Computed Properties:**
- `totalCasos`: Total de casos
- `pendientes`: Casos pendientes
- `resueltos`: Casos resueltos
- `casosFiltrados`: Casos filtrados por estado y tipo

**Métodos:**
- `cargarCasos(tipoCaso)`: Fetch de casos desde API con filtro opcional
- `onSearch(query)`: Maneja búsqueda, llama a `casosAPI.searchCasos()`
- `onFilter(filters)`: Maneja filtros de estado y tipo
- `abrirCaso(caseId)`: Navegación a detalle

#### 5.2.6. `views/CasoDetalle.vue` - Vista de Detalle

**Funcionalidad:**
- Carga caso completo al montar
- Orquesta las 4 secciones (A, B, C, D)
- Proporciona funciones compartidas mediante `provide/inject`
- Maneja estados de carga y error
- Normaliza datos para robustez

**Provide/Inject:**
- `actualizarDocumento`: Función para actualizar tipo de documento
- `actualizarChecklistItem`: Función para validar items
- `generarResolucion`: Función para generar borrador

**Métodos:**
- `cargarCaso()`: Fetch de caso desde API
- `normalizeCaso()`: Asegura estructura completa con valores por defecto
- `createEmptyCaso()`: Crea caso vacío en caso de error
- `recargarCaso()`: Recarga caso después de actualizaciones
- `onDocumentoActualizado()`: Handler de actualización de documento

**Robustez:**
- Maneja errores de red mostrando estructura parcial
- Valores por defecto ("—") para campos faltantes
- Recarga automática después de cambios

#### 5.2.7. `components/SeccionA.vue` - Resumen de Contexto

**Props:**
- `unifiedContext`: Contexto unificado
- `compilationMetadata`: Metadatos del caso
- `materia`, `montoDisputa`, `empresa`, `fechaIngreso`, `alertas`

**Funcionalidad:**
- Modo visualización: Muestra información en tarjetas
- Modo edición: Inputs editables para todos los campos
- Toggle entre modos con botón "Editar"/"Guardar"
- Guarda cambios mediante `updateUnifiedContext`
- Emite evento `contexto-actualizado` para recargar caso

**Diseño:**
- Grid responsive de 3 tarjetas
- Headers con gradiente púrpura
- Iconos distintivos por categoría

#### 5.2.8. `components/SeccionB.vue` - Gestor Documental

**Props:**
- `documentInventory`: Inventario de documentos
- `caseId`: ID del caso

**Funcionalidad:**
- Lista documentos por nivel (critical, supporting, missing)
- Dropdown para cambiar tipo de documento
- Prompt para nombre personalizado al cambiar tipo
- Modal de vista previa de documentos
- Soporte para PDFs (iframe) e imágenes (img tag)

**Métodos:**
- `actualizarTipoDocumento()`: Actualiza tipo y nombre
- `verDocumento()`: Abre modal de vista previa
- `cerrarVisor()`: Cierra modal
- `cargarDocumento()`: Construye URL de preview

**Estados:**
- `documentoSeleccionado`: Documento actual en modal
- `documentUrl`: URL del documento para preview
- `loadingDocument`: Estado de carga
- `documentError`: Error al cargar documento

#### 5.2.9. `components/SeccionC.vue` - Checklist

**Props:**
- `checklist`: Objeto Checklist con 3 grupos
- `caseId`: ID del caso

**Funcionalidad:**
- Renderiza 3 grupos de checklist
- Usa componente `ChecklistItem` para cada item
- Emite evento `checklist-actualizado` cuando se valida un item

**Diseño:**
- Títulos de grupo con estilo distintivo
- Lista de items con espaciado consistente

#### 5.2.10. `components/ChecklistItem.vue` - Item de Checklist

**Props:**
- `item`: Objeto ChecklistItem
- `caseId`: ID del caso

**Funcionalidad:**
- Header expandible/colapsable
- Icono de estado visual
- Checkbox "Validado" para marcado manual
- Detalles expandidos: evidencia, descripción, tipo

**Inyecta:**
- `actualizarChecklistItem`: Función del padre para actualizar validación

**Métodos:**
- `toggleExpand()`: Expande/colapsa detalles
- `getStatusIcon()`: Retorna emoji según estado
- `getStatusClass()`: Retorna clase CSS según estado
- `actualizarValidacion()`: Actualiza validación en backend

**Estilos Dinámicos:**
- Colores de borde y fondo según estado
- Transiciones suaves

#### 5.2.11. `components/SeccionD.vue` - Motor de Resolución

**Props:**
- `caseId`: ID del caso
- `checklist`: Checklist para determinar tipo de resolución

**Funcionalidad:**
- Selector de tipo de resolución (Instrucción/Improcedente)
- Auto-generación de borrador al cargar
- Generación de borrador al cambiar tipo
- Editor de texto para editar borrador
- Botón "Firmar y Cerrar Caso"

**Métodos:**
- `onTemplateChange()`: Handler de cambio de tipo
- `generarBorrador()`: Genera nuevo borrador (reemplaza contenido)
- `firmarYCerrar()`: Cierra caso y guarda resolución

**Validaciones:**
- Verifica que haya contenido antes de cerrar
- Muestra confirmación antes de cerrar
- Estado de carga durante cierre

### 5.3. Dependencias Principales

Ver `package.json`:
- `vue`: Framework frontend
- `vue-router`: Enrutamiento
- `axios`: Cliente HTTP
- `vite`: Build tool y dev server

---

## 6. Base de Datos

### 6.1. Arquitectura de Persistencia

El sistema utiliza una **estrategia híbrida** de persistencia:

1. **Base de Datos JSON Relacional** (Prioritaria - Desarrollo Actual)
   - Ubicación: `backend/data/DataBase/`
   - Archivos: `casos.json`, `edn.json`, `personas.json`, `suministros.json`, `documentos.json`
   - Gestor: `JSONDBManager`
   - **Nota**: EDNs están separados en `edn.json` para mejor modularidad

2. **Base de Datos SQLite** (Opcional - Producción Futura)
   - Ubicación: `backend/data/sec_reclamos.db`
   - Gestor: `DBManager`
   - Esquema estrella con JSONB para datos flexibles

### 6.2. Estructura de Base de Datos JSON

#### 6.2.1. `personas.json`

**Estructura:**
```json
[
  {
    "id": 1,
    "rut": "12.345.678-9",
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "telefono": "+56912345678"
  }
]
```

**Propósito:**
- Almacenar información de clientes identificados por RUT
- Historial de contacto
- Relación 1:N con casos (un cliente puede tener múltiples reclamos)

**Clave Primaria**: `rut`

#### 6.2.2. `suministros.json`

**Estructura:**
```json
[
  {
    "id": 1,
    "nis": "608749",
    "comuna": "Santiago",
    "direccion": "Av. Principal 123",
    "numero_cliente": "4421"
  }
]
```

**Propósito:**
- Almacenar información de puntos de suministro (activos físicos)
- Identificados por NIS + Comuna (clave compuesta)
- Crítico para detectar reincidencia de fraudes en ubicación física
- Relación 1:N con casos (un suministro puede tener múltiples reclamos)

**Clave Primaria**: `nis` + `comuna` (compuesta)

#### 6.2.3. `casos.json`

**Estructura:**
```json
[
  {
    "id": 1,
    "case_id": "240108-000010",
    "persona_id": 1,
    "suministro_id": 1,
    "empresa": "Grupo Saesa",
    "materia": "Reclamo SEC",
    "monto_disputa": 150000,
    "fecha_ingreso": "2024-01-08",
    "fecha_cierre": "2024-01-15",
    "estado": "CERRADO"
  }
]
```

**Propósito:**
- Almacenar metadatos de casos de reclamos (sin EDN embebido)
- Relaciones con personas y suministros mediante IDs
- Estado del caso (PENDIENTE, EN_REVISION, RESUELTO, CERRADO)
- **Nota**: El EDN está separado en `edn.json` (ver sección 6.2.4)

**Clave Primaria**: `case_id` (formato SEC: YYMMDD-XXXXXX)

**Relación**: 1:1 con `edn.json` mediante `case_id`

#### 6.2.4. `edn.json`

**Estructura (EDNs Separados):**
```json
{
  "230125-000509": {
    "compilation_metadata": {
      "case_id": "230125-000509",
      "processing_timestamp": "2025-11-20T06:00:49.251482+00:00",
      "status": "COMPLETED",
      "tipo_caso": "CNR"
    },
    "unified_context": {
      "rut_client": "12.345.678-9",
      "client_name": "Juan Pérez",
      "service_nis": "608749",
      "address_standard": "Av. Principal 123",
      "commune": "Santiago",
      "email": "juan@example.com",
      "phone": "+56912345678"
    },
    "document_inventory": {
      "level_1_critical": [...],
      "level_2_supporting": [...],
      "level_0_missing": [...]
    },
    "checklist": {
      "group_a_admisibilidad": [...],
      "group_b_instruccion": [...],
      "group_c_analisis": [...]
    },
    "resolucion": {
      "content": "...",
      "fecha_firma": "2025-01-15T10:30:00Z"
    }
  }
}
```

**Propósito:**
- Almacenar EDNs (Expedientes Digitales Normalizados) separados de los metadatos del caso
- Facilita actualizaciones independientes de EDN y metadatos
- Mejora la modularidad y el rendimiento (no cargar EDN completo cuando solo se necesitan metadatos)
- Permite versionado y auditoría de cambios en EDN

**Clave**: `case_id` (coincide con `casos.json`)

**Relación**: 1:1 con `casos.json` (un caso tiene un EDN)

#### 6.2.5. `documentos.json`

**Estructura:**
```json
[
  {
    "id": 1,
    "caso_id": 1,
    "case_id": "240108-000010",
    "type": "CARTA_RESPUESTA",
    "file_id": "240108-000010-1",
    "original_name": "Respuesta_Reclamo_N°117350430.pdf",
    "standardized_name": "CARTA_RESPUESTA - Respuesta_Reclamo_N°117350430.pdf",
    "file_path": "Respuesta_Reclamo_N°117350430.pdf",
    "absolute_path": "/path/to/file.pdf",
    "level": "level_1_critical"
  }
]
```

**Propósito:**
- Índice de todos los documentos procesados
- Relación con casos mediante `case_id`
- Metadatos de archivo y clasificación
- Rutas para acceso a archivos físicos

**Clave Primaria**: `id` (auto-incremental)
**Índices**: `case_id`, `file_id`

### 6.3. Relaciones entre Entidades

```
PERSONA (1) ──< (N) CASO (N) >── (1) SUMINISTRO
                │
                │ (1)
                │
                ▼
            DOCUMENTO (N)
```

**Relaciones:**
- Una **Persona** puede tener múltiples **Casos**
- Un **Suministro** puede tener múltiples **Casos**
- Un **Caso** pertenece a una **Persona** y un **Suministro**
- Un **Caso** tiene múltiples **Documentos**

### 6.4. Estrategia de Upsert

El sistema implementa **lógica de upsert inteligente**:

1. **Personas**: Si existe RUT, actualiza; si no, crea nueva
2. **Suministros**: Si existe NIS+Comuna, actualiza; si no, crea nuevo
3. **Casos**: Si existe `case_id`, actualiza; si no, crea nuevo
4. **Documentos**: Si existe `case_id`+`file_id`, actualiza; si no, crea nuevo

**Ventajas:**
- Idempotencia: Procesar el mismo caso múltiples veces no crea duplicados
- Actualización incremental: Se pueden agregar documentos a casos existentes
- Historial preservado: No se pierden datos al reprocesar

### 6.5. Objetivo de la Base de Datos

La base de datos JSON relacional replica el **esquema estrella** descrito en la especificación técnica:

- **Centro (Hecho)**: `casos` - Eventos temporales de reclamos
- **Dimensiones (Actores)**: `personas`, `suministros` - Entidades persistentes
- **Hechos Detallados**: `documentos` - Granularidad de evidencia

**Objetivos:**
1. **Trazabilidad Histórica**: Mantener historial de todos los reclamos de un cliente o suministro
2. **Detección de Patrones**: Identificar reincidencias (mismo cliente, mismo suministro)
3. **Análisis Longitudinal**: Comparar casos a lo largo del tiempo
4. **Integridad Referencial**: Relaciones claras entre entidades
5. **Normalización**: Evitar duplicación de datos (DRY)

**Migración Futura:**
La estructura JSON está diseñada para migrar fácilmente a SQLite o PostgreSQL manteniendo el mismo esquema relacional.

### 6.6. Gestión de Cache y Recarga

**Problema Resuelto:**
Inicialmente, los datos se cargaban una sola vez al iniciar el backend, causando que los cambios no se reflejaran hasta reiniciar.

**Solución Implementada:**
- `JSONDBManager.reload()`: Recarga todos los datos desde disco
- `JSONDBManager.reload_case(case_id)`: Recarga un caso específico
- Limpieza de cache en memoria (`cases_store`) después de guardar
- Recarga automática después de cada actualización

**Flujo de Actualización:**
1. Usuario edita y guarda → Backend guarda en JSON
2. Backend llama `reload()` o `reload_case()`
3. Backend limpia `cases_store[case_id]`
4. Frontend recarga caso → Backend devuelve datos actualizados desde disco

---

## 7. OMC: Objeto Maestro de Compilación

### 7.1. Visión General

El **Objeto Maestro de Compilación (OMC)** es el núcleo del sistema de ingesta. Actúa como una "caja negra" que transforma documentos no estructurados en dos salidas estructuradas:

1. **Base de Datos Relacional Normalizada**: Esquema estrella con historial de actores
2. **Expediente Digital Normalizado (EDN)**: Contrato JSON estandarizado

### 7.2. Documentación Detallada

Para documentación técnica completa del OMC, incluyendo:
- Arquitectura y principios de diseño
- Pipeline de procesamiento (7 fases)
- Clasificación documental detallada
- Extracción de entidades por tipo
- Esquema de base de datos
- Lógica de upsert
- Bibliotecas recomendadas
- Ejemplo de flujo completo

**Ver**: `docs/OMC_Explained.md`

### 7.3. Integración en el Sistema

El OMC se integra en el sistema mediante:

1. **Scripts de Procesamiento**:
   - `scripts/process_example_cases.py`: Procesa casos y almacena en SQLite
   - `scripts/create_json_database.py`: Crea BD JSON desde casos

2. **Módulo de Ingesta**:
   - `engine/omc/document_processor.py`: Orquestador principal
   - `engine/omc/pdf_extractor.py`: Extracción de PDFs con bbox
   - `engine/omc/docx_extractor.py`: Extracción de DOCX
   - `engine/omc/document_classifier.py`: Clasificación y tipo_caso
   - `engine/omc/entity_extractor.py`: Extracción de entidades con posición
   - `engine/min/rule_engine.py`: Motor de reglas
   - `engine/min/rules/`: Reglas de validación
   - `checklist_tipo/*.json`: Configuraciones de checklist

3. **Uso en Producción**:
   - Los casos procesados se almacenan en `DataBase/`
   - El frontend consume los EDNs generados
   - El funcionario puede revisar y corregir la clasificación automática

### 7.4. Flujo de Procesamiento

```
Archivos No Estructurados
         ↓
    [OMC Pipeline]
         ↓
┌────────────────────┐
│  EDN (JSON)        │ → Frontend (Visualización)
│  Base de Datos     │ → Análisis y Validación
└────────────────────┘
```

---

## 8. Guía de Desarrollo

### 8.1. Configuración del Entorno

#### Backend

```bash
cd reclamos-sec/full-stack/backend
pip install -r requirements.txt
```

#### Frontend

```bash
cd reclamos-sec/full-stack/frontend
npm install
```

### 8.2. Ejecución del Sistema

#### Iniciar Backend

```bash
cd reclamos-sec/full-stack/backend
python main.py
# O alternativamente:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en `http://localhost:8000`

#### Iniciar Frontend

```bash
cd reclamos-sec/full-stack/frontend
npm run dev
```

El frontend estará disponible en `http://localhost:5173`

### 8.3. Procesar Casos de Ejemplo

Para procesar los casos reales ubicados en `backend/data/example_cases/`:

```bash
cd reclamos-sec/full-stack/backend
python scripts/create_json_database.py
```

Esto generará los archivos JSON en `backend/data/DataBase/`

### 8.4. Estructura de Archivos para Nuevos Casos

Para agregar nuevos casos:

1. Crear carpeta en `backend/data/example_cases/` con nombre `YYMMDD-XXXXXX`
2. Colocar todos los documentos del caso en esa carpeta
3. Ejecutar `create_json_database.py` para actualizar la BD

### 8.5. Modificando el Sistema

#### Agregar Nuevo Tipo de Documento

1. **Backend**:
   - Agregar tipo en `models.py` → `DocumentType` enum
   - Actualizar `document_classifier.py` con heurísticas de clasificación
   - Actualizar `entity_extractor.py` con extracción específica

2. **Frontend**:
   - Agregar opción en `SeccionB.vue` → dropdown de tipos

#### Agregar Nuevo Item al Checklist

1. **Backend**:
   - Agregar lógica en `checklist_generator.py` → método `generate_checklist()`
   - Definir regla de evaluación (CUMPLE/NO_CUMPLE/REVISION_MANUAL)

2. **Frontend**:
   - El componente `ChecklistItem.vue` renderiza automáticamente nuevos items

#### Modificar Templates de Resolución

1. **Backend**:
   - Editar `routes/casos.py` → función `generar_resolucion()`
   - Modificar strings de templates INSTRUCCION e IMPROCEDENTE

### 8.6. Debugging y Troubleshooting

#### Problema: Cambios no se reflejan en la interfaz

**Solución**: Verificar que:
- `JSONDBManager.reload()` se llama después de guardar
- `cases_store[case_id]` se limpia después de guardar
- Frontend recarga el caso después de actualizaciones

#### Problema: Documentos no se muestran en vista previa

**Solución**: Verificar que:
- `absolute_path` o `file_path` están correctos en `documentos.json`
- Archivos existen en `example_cases/`
- Endpoint `/preview` tiene permisos de lectura

#### Problema: Checklist no se recalcula

**Solución**: Verificar que:
- `ChecklistGenerator` está inicializado correctamente
- Se llama `generate_checklist()` después de actualizar documentos
- El EDN tiene estructura completa

### 8.7. Próximos Pasos de Desarrollo

**Mejoras Sugeridas:**

1. **Autenticación y Autorización**:
   - Sistema de login para funcionarios
   - Roles y permisos
   - Auditoría de cambios

2. **Mejoras en OMC**:
   - OCR avanzado para imágenes
   - NLP para clasificación más precisa
   - Extracción de tablas de Excel

3. **Base de Datos de Producción**:
   - Migración a PostgreSQL
   - Índices optimizados
   - Backup automático

4. **Funcionalidades Adicionales**:
   - Búsqueda avanzada de casos
   - Exportación de reportes
   - Notificaciones de cambios
   - Historial de modificaciones

5. **Testing**:
   - Tests unitarios para backend
   - Tests de integración
   - Tests E2E para frontend

---

## Conclusión

Este manual proporciona una visión completa del sistema Full-Stack de Análisis de Reclamos SEC. El sistema está diseñado para ser modular, extensible y mantenible, permitiendo a desarrolladores entender rápidamente la arquitectura y realizar modificaciones de manera eficiente.

Para preguntas específicas sobre implementación o detalles técnicos, consultar:
- `docs/OMC_Explained.md` - Documentación detallada del OMC
- `docs/especificacion_requerimientos_tecnicos.md` - Especificación original
- Código fuente con comentarios inline

---

**Versión del Manual**: 1.0  
**Última Actualización**: 2024  
**Mantenido por**: Equipo de Desarrollo SEC

