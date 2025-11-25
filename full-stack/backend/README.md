# 🛠 Backend: Motor de Procesamiento SEC

API REST construida con FastAPI que implementa los tres motores principales del sistema: **OMC**, **MIN** y **MGR**. Este backend procesa documentos, genera checklists normativos y crea borradores de resoluciones legales.

## 📁 Estructura del Proyecto

```
backend/
├── src/
│   ├── __init__.py
│   ├── config.py            # Configuración de rutas y directorios
│   ├── models.py            # Modelos Pydantic (EDN, CaseSummary, Checklist)
│   ├── engine/              # Motores principales
│   │   ├── omc/             # Objeto Maestro de Compilación
│   │   │   ├── document_processor.py    # Procesamiento de documentos
│   │   │   ├── pdf_extractor.py        # Extracción de PDFs
│   │   │   ├── docx_extractor.py       # Extracción de DOCX
│   │   │   ├── document_classifier.py  # Clasificación de documentos
│   │   │   ├── document_categorizer.py  # Categorización funcional
│   │   │   ├── entity_extractor.py     # Extracción de entidades
│   │   │   ├── fact_extractor.py       # Extracción de features (fact-centric)
│   │   │   ├── strategy_selector.py     # Selección de estrategia de fuentes
│   │   │   ├── create_json_database.py # Script para poblar BD
│   │   │   └── README.md                # Documentación del OMC
│   │   ├── min/             # Motor de Inferencia Normativa
│   │   │   ├── rule_engine.py          # Motor de reglas
│   │   │   ├── checklist_generator.py  # Generador de checklist
│   │   │   └── rules/                  # Reglas configurables
│   │   │       ├── __init__.py
│   │   │       ├── base_rules.py       # Reglas base
│   │   │       └── cnr_rules.py        # Reglas CNR
│   │   └── mgr/             # Motor de Generación de Resoluciones
│   │       └── resolucion_generator.py # Generador de resoluciones
│   ├── routes/              # Endpoints API
│   │   ├── __init__.py
│   │   └── casos.py        # Rutas principales de casos
│   ├── database/            # Gestión de datos
│   │   ├── __init__.py
│   │   ├── json_db_manager.py
│   │   └── db_manager.py
│   ├── utils/               # Utilidades
│   │   ├── __init__.py
│   │   ├── helpers.py       # Funciones auxiliares
│   │   ├── docx_to_html.py # Conversión DOCX a HTML
│   │   ├── docx_to_pdf.py   # Conversión DOCX a PDF
│   │   ├── resolucion_pdf.py # Generación de PDFs de resoluciones
│   │   └── README_DOCX_CONVERSION.md
│   └── scripts/             # Scripts de utilidad (si existe)
├── templates/                # Plantillas configurables
│   ├── checklist/          # Configuraciones de checklist (JSON)
│   │   ├── cnr.json
│   │   └── template.json
│   ├── expediente/         # Esquemas EDN
│   │   └── edn_schema.json
│   └── resolucion/         # Templates Markdown de resoluciones
│       ├── master_instruccion.md
│       ├── master_improcedente.md
│       └── snippets/        # Fragmentos de argumentos legales
│           ├── arg_calculo_erroneo.md
│           ├── arg_cim_invalido.md
│           ├── arg_falta_fotos.md
│           ├── arg_falta_ot.md
│           └── arg_periodo_excesivo.md
├── data/                    # Datos persistentes
│   ├── DataBase/           # Base de datos JSON
│   │   ├── casos.json
│   │   ├── documentos.json
│   │   ├── edn.json
│   │   ├── personas.json
│   │   └── suministros.json
│   ├── Files/              # Archivos de casos
│   │   └── {case_id}/      # Carpeta por caso
│   │       ├── [documentos del caso]
│   │       └── resoluciones/ # Resoluciones generadas (opcional)
│   ├── temp_pdfs/          # PDFs temporales para previews
│   ├── mock_casos.json     # Casos de prueba
│   └── sec_reclamos.db     # Base de datos SQLite (opcional)
├── main.py                  # Punto de entrada
├── README.md                # Este archivo
└── requirements.txt         # Dependencias Python
```

## 🚀 Instalación

### 1. Crear Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Variables de Entorno (Opcional)

Actualmente no se requieren variables de entorno. La configuración se maneja mediante `src/config.py` con rutas relativas.

## ▶️ Ejecución

### Modo Desarrollo (con recarga automática)

```bash
python main.py
```

O usando Uvicorn directamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Modo Producción

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

El servidor estará disponible en:
- **API**: `http://localhost:8000`
- **Documentación Swagger**: `http://localhost:8000/docs`
- **Documentación ReDoc**: `http://localhost:8000/redoc`

## 🔧 Scripts de Utilidad

### Poblar Base de Datos desde Casos de Ejemplo

```bash
python src/engine/omc/create_json_database.py
```

Este script usa el motor **OMC** para procesar casos y generar la base de datos JSON:
- Lee casos de ejemplo desde `data/Files/` (directamente, sin subcarpeta `example_cases`)
- Procesa documentos con OCR, extracción de entidades y clasificación (usando el OMC)
- Genera la estructura de base de datos JSON completa
- Crea entidades normalizadas (Personas, Suministros, Casos, Documentos, EDNs)

## 🏛 Arquitectura

El backend implementa el patrón **Pipeline & Filters** a través de tres motores modulares:

### OMC (Objeto Maestro de Compilación)
- **Ubicación**: `src/engine/omc/`
- **Responsabilidad**: Ingestiona documentos, extrae datos mediante OCR, clasifica documentos, extrae features (fact-centric) y genera el EDN (Expediente Digital Normalizado)
- **Flujo**: PDF/DOCX → Extracción → Clasificación → Extracción de Features → EDN JSON
- **Arquitectura Fact-Centric**: Extrae `consolidated_facts` y `evidence_map` para que el MIN opere eficientemente

### MIN (Motor de Inferencia Normativa)
- **Ubicación**: `src/engine/min/`
- **Responsabilidad**: Evalúa el EDN contra reglas Python configurables y genera checklists estructurados
- **Flujo**: EDN → Consume `consolidated_facts` → Reglas → Checklist JSON
- **Arquitectura Fact-Centric**: Opera sobre `consolidated_facts` en lugar de buscar en documentos
- **Configuración**: Templates en `templates/checklist/` (ej: `cnr.json`)

### MGR (Motor de Generación de Resoluciones)
- **Ubicación**: `src/engine/mgr/`
- **Responsabilidad**: Genera borradores de resoluciones legales combinando templates Markdown con datos del caso
- **Flujo**: Checklist + Templates → Resolución Markdown
- **Templates**: `templates/resolucion/master_*.md` y `snippets/*.md`

## 📡 Endpoints Principales

- `GET /api/casos` - Listar casos (con paginación y filtros)
- `GET /api/casos/{case_id}` - Obtener caso completo
- `PUT /api/casos/{case_id}/checklist/{item_id}` - Actualizar item de checklist
- `POST /api/casos/{case_id}/resolucion` - Generar borrador de resolución
- `GET /api/casos/{case_id}/documentos/{file_id}/preview` - Vista previa de documento

Ver documentación completa en `/docs` cuando el servidor esté corriendo.

## 🧪 Modos de Operación

El backend soporta dos modos mediante el parámetro `mode`:

- **`test`**: Usa datos mock desde `mock_casos.json`
- **`validate`**: Usa datos reales desde la base de datos JSON

## 📚 Dependencias Principales

Ver `requirements.txt` para lista completa. Principales:

- `fastapi` - Framework web
- `uvicorn` - Servidor ASGI
- `pydantic` - Validación de datos
- `pdfplumber` - Extracción de PDFs
- `python-docx` - Procesamiento de DOCX
- `reportlab` - Generación de PDFs (para resoluciones)

## 🔍 Debugging

Para ver logs detallados, el sistema usa el módulo `logging` de Python. Los logs incluyen:
- Procesamiento de documentos (OMC)
- Generación de checklists (MIN)
- Generación de resoluciones (MGR)
- Errores de API

## 📖 Documentación Adicional

- [Manual de Arquitectura](../../docs/manual_de_uso/3_OMC.md) - Detalles del OMC (incluye fact-centric)
- [Manual de Arquitectura](../../docs/manual_de_uso/5_EDN.md) - Estructura del EDN (incluye consolidated_facts y evidence_map)
- [Manual de Arquitectura](../../docs/manual_de_uso/6_MIN.md) - Detalles del MIN (incluye fact-centric)
- [Manual de Arquitectura](../../docs/manual_de_uso/8_MGR.md) - Detalles del MGR
- [Documentación Técnica](../../docs/full-stack/backend.md) - Implementación detallada completa

