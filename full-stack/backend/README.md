# 🛠 Backend: Motor de Procesamiento SEC

API REST construida con FastAPI que implementa los tres motores principales del sistema: **OMC**, **MIN** y **MGR**. Este backend procesa documentos, genera checklists normativos y crea borradores de resoluciones legales.

## 📁 Estructura del Proyecto

```
backend/
├── src/
│   ├── engine/              # Motores principales
│   │   ├── omc/             # Objeto Maestro de Compilación
│   │   │   ├── document_processor.py    # Procesamiento de documentos
│   │   │   ├── pdf_extractor.py        # Extracción de PDFs
│   │   │   ├── docx_extractor.py       # Extracción de DOCX
│   │   │   ├── document_classifier.py  # Clasificación de documentos
│   │   │   └── entity_extractor.py     # Extracción de entidades
│   │   ├── min/             # Motor de Inferencia Normativa
│   │   │   ├── rule_engine.py          # Motor de reglas
│   │   │   └── rules/                  # Reglas configurables
│   │   │       ├── base_rules.py       # Reglas base
│   │   │       └── cnr_rules.py        # Reglas CNR
│   │   └── mgr/             # Motor de Generación de Resoluciones
│   │       └── resolucion_generator.py # Generador de resoluciones
│   ├── routes/              # Endpoints API
│   │   └── casos.py        # Rutas principales de casos
│   ├── generators/          # Generadores auxiliares
│   │   └── checklist_generator.py
│   ├── database/            # Gestión de datos
│   │   ├── json_db_manager.py
│   │   └── db_manager.py
│   ├── utils/               # Utilidades
│   ├── scripts/             # Scripts de utilidad
│   └── models.py            # Modelos Pydantic
├── templates/                # Plantillas configurables
│   ├── checklist/          # Configuraciones de checklist (JSON)
│   ├── expediente/         # Esquemas EDN
│   └── resolucion/         # Templates Markdown de resoluciones
│       ├── master_instruccion.md
│       ├── master_improcedente.md
│       └── snippets/        # Fragmentos de argumentos legales
├── data/                    # Datos persistentes
│   ├── DataBase/           # Base de datos JSON
│   ├── Files/              # Archivos de casos
│   └── mock_casos.json     # Casos de prueba
├── main.py                  # Punto de entrada
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
- **Responsabilidad**: Ingestiona documentos, extrae datos mediante OCR, clasifica documentos y genera el EDN (Expediente Digital Normalizado)
- **Flujo**: PDF/DOCX → Extracción → Clasificación → EDN JSON

### MIN (Motor de Inferencia Normativa)
- **Ubicación**: `src/engine/min/`
- **Responsabilidad**: Evalúa el EDN contra reglas Python configurables y genera checklists estructurados
- **Flujo**: EDN → Reglas → Checklist JSON
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

- `fastapi` - Framework web
- `uvicorn` - Servidor ASGI
- `pydantic` - Validación de datos
- `pdfplumber` - Extracción de PDFs
- `python-docx` - Procesamiento de DOCX
- `reportlab` - Generación de PDFs

## 🔍 Debugging

Para ver logs detallados, el sistema usa el módulo `logging` de Python. Los logs incluyen:
- Procesamiento de documentos (OMC)
- Generación de checklists (MIN)
- Generación de resoluciones (MGR)
- Errores de API

## 📖 Documentación Adicional

- [Manual de Arquitectura](../../docs/manual_de_uso/3_OMC.md) - Detalles del OMC
- [Manual de Arquitectura](../../docs/manual_de_uso/6_MIN.md) - Detalles del MIN
- [Manual de Arquitectura](../../docs/manual_de_uso/8_MGR.md) - Detalles del MGR
- [Documentación Técnica](../../docs/full-stack/backend.md) - Implementación detallada

