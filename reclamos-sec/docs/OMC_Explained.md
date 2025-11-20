# OMC: Objeto Maestro de Compilación - Documentación Técnica Detallada

## 1. Visión General y Arquitectura

### 1.1. Definición del OMC

El **Objeto Maestro de Compilación (OMC)** es el núcleo del sistema de ingesta de la SEC. Actúa como una "caja negra" que transforma documentos no estructurados y dispersos en dos salidas estructuradas y analizables:

1. **Base de Datos Relacional Normalizada**: Un esquema estrella que preserva la historia de actores (Personas, Suministros) y eventos (Casos).
2. **Expediente Digital Normalizado (EDN)**: Un contrato JSON estandarizado que alimenta todos los módulos posteriores de análisis.

### 1.2. Principios de Diseño

- **Idempotencia**: Procesar el mismo lote de archivos múltiples veces no debe crear duplicados.
- **Tolerancia a Fallos**: Un documento corrupto no detiene el procesamiento del caso completo.
- **Extracción Específica por Tipo**: Cada tipo de documento tiene un esquema de extracción único y campos específicos en la base de datos.
- **Upsert Inteligente**: Resolución automática de entidades existentes vs. nuevas.
- **Traza Completa**: Todo documento procesado queda indexado con metadatos de extracción.

---

## 2. Pipeline de Procesamiento: Flujo Detallado

### 2.1. Fase 1: Recepción y Validación de Entrada

**Endpoint/Watcher:**
- **REST API**: `POST /api/ingestion/process-case`
- **File Watcher**: Monitoreo de carpeta `incoming/` (opcional para integración con sistemas externos)

**Input Contract:**
```json
{
  "case_id": "231220-000557",
  "case_metadata": {
    "origen": "SIAC",
    "fecha_ingreso": "2023-12-20",
    "empresa": "ENEL"
  },
  "files": [
    {
      "filename": "Respuesta_Reclamo_2642280.pdf",
      "content": "<base64_binary>",
      "mime_type": "application/pdf"
    }
  ]
}
```

**Validaciones Iniciales:**
- Verificar que `case_id` cumpla formato SEC (YYMMDD-XXXXXX)
- Validar tipos MIME permitidos: `application/pdf`, `image/jpeg`, `image/png`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Rechazar archivos > 50MB (configurable)
- Verificar integridad de archivos binarios (checksum)

**Librerías:**
- `python-magic` o `filetype` para detección MIME
- `hashlib` para checksums (SHA-256)

---

### 2.2. Fase 2: Sanitización y Normalización de Archivos

**Objetivo:** Convertir todos los formatos a estándares procesables y reparar documentos corruptos.

#### 2.2.1. Sanitización de PDFs

**Problemas Comunes:**
- PDFs escaneados sin capa de texto (solo imágenes)
- PDFs con cabeceras corruptas
- PDFs con protección/contraseña
- PDFs con metadatos inconsistentes

**Proceso:**
1. **Validación de Estructura**: Usar `PyPDF2` o `pypdf` para verificar estructura interna
2. **Reparación de Cabeceras**: Usar `qpdf` (herramienta externa) para reparar PDFs corruptos
3. **Detección de Capa de Texto**: 
   - Si existe capa de texto → Extracción directa
   - Si NO existe → Marcar para OCR posterior
4. **Conversión a PDF/A**: Usar `pdf2pdfa` o `ghostscript` para normalización

**Librerías:**
- `pypdf` / `PyPDF2`: Lectura y validación de PDFs
- `pdfplumber`: Extracción avanzada de texto y tablas
- `qpdf` (CLI): Reparación de PDFs corruptos
- `ghostscript` (CLI): Conversión a PDF/A

**Código de Ejemplo:**
```python
def sanitize_pdf(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Sanitiza un PDF y determina si requiere OCR
    
    Returns:
        (has_text_layer, error_message)
    """
    try:
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            has_text = len(pdf.pages) > 0 and any(
                page.extract_text().strip() for page in pdf.pages
            )
            return (has_text, None)
    except Exception as e:
        # Intentar reparar con qpdf
        repaired_path = file_path.parent / f"repaired_{file_path.name}"
        subprocess.run(['qpdf', '--linearize', str(file_path), str(repaired_path)])
        return (False, None)
```

#### 2.2.2. Procesamiento de Imágenes

**Formatos Soportados:** JPEG, PNG, TIFF, BMP

**Normalización:**
- Conversión a PNG (formato sin pérdida)
- Redimensionamiento si > 4000px (optimización)
- Corrección de orientación (EXIF)
- Normalización de espacio de color (RGB)

**Librerías:**
- `Pillow (PIL)`: Procesamiento de imágenes
- `exifread`: Lectura de metadatos EXIF

#### 2.2.3. Procesamiento de Documentos Word

**Formatos:** `.docx` (Office Open XML)

**Proceso:**
- Extracción directa de texto estructurado
- Preservación de metadatos (autor, fecha creación)
- Conversión de tablas a estructuras JSON

**Librerías:**
- `python-docx`: Lectura de documentos Word

---

### 2.3. Fase 3: Extracción de Texto (OCR & Text Extraction)

#### 3.3.1. Extracción de PDFs con Capa de Texto

**Estrategia:**
- Usar `pdfplumber` para extracción de texto y tablas estructuradas
- Preservar coordenadas de texto (para referencias posteriores)
- Extraer metadatos (autor, fecha, título)

**Ejemplo:**
```python
import pdfplumber

def extract_text_from_pdf(file_path: Path) -> Dict[str, Any]:
    text_content = []
    tables_content = []
    metadata = {}
    
    with pdfplumber.open(file_path) as pdf:
        # Metadatos
        metadata = pdf.metadata
        
        # Texto por página (con coordenadas)
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                text_content.append({
                    'page': page_num,
                    'text': text,
                    'bbox': page.bbox
                })
            
            # Tablas
            tables = page.extract_tables()
            for table in tables:
                tables_content.append({
                    'page': page_num,
                    'data': table
                })
    
    return {
        'text': '\n\n'.join([p['text'] for p in text_content]),
        'text_by_page': text_content,
        'tables': tables_content,
        'metadata': metadata
    }
```

#### 3.3.2. OCR para Imágenes y PDFs Escaneados

**Motor OCR:** Tesseract OCR con modelo de idioma español

**Configuración:**
- Idioma: `spa` (español)
- PSM (Page Segmentation Mode): Auto-detección
- OCR Engine Mode: LSTM (mejor precisión)

**Pre-procesamiento de Imagen:**
1. Conversión a escala de grises
2. Aplicación de filtro de desenfoque (Gaussian Blur)
3. Binarización (Threshold) adaptativa
4. Reducción de ruido (morphological operations)

**Librerías:**
- `pytesseract`: Wrapper de Tesseract OCR
- `opencv-python (cv2)`: Pre-procesamiento de imágenes
- `numpy`: Operaciones de arrays

**Código:**
```python
import pytesseract
import cv2
import numpy as np

def ocr_image(image_path: Path) -> str:
    """Aplica OCR a una imagen con pre-procesamiento"""
    # Leer imagen
    img = cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Pre-procesamiento
    # 1. Desenfoque para reducir ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 2. Binarización adaptativa
    binary = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    
    # 3. OCR
    text = pytesseract.image_to_string(
        binary, lang='spa', config='--psm 6'
    )
    
    return text
```

**Manejo de PDFs Escaneados:**
- Convertir cada página a imagen (300 DPI)
- Aplicar OCR por página
- Reconstruir texto completo

---

### 2.4. Fase 4: Clasificación Documental Inteligente

**Objetivo:** Identificar el tipo de documento mediante análisis multi-capa (nombre, contenido, estructura).

#### 4.4.1. Taxonomía de Documentos

La taxonomía define **no solo el tipo**, sino también **qué información debe extraerse** y **qué campos tendrá en la base de datos**.

| Tipo Documento | Nivel | Campos Específicos en BD | Relevancia Checklist |
|----------------|-------|-------------------------|---------------------|
| `CARTA_RESPUESTA` | Level 1 (Crítico) | `response_date`, `decision`, `resolution_number`, `cnr_reference` | ✅ Crítico: Define si el reclamo fue aceptado/rechazado |
| `ORDEN_TRABAJO` | Level 1 (Crítico) | `ot_number`, `technician_name`, `visit_date`, `findings`, `equipment_status` | ✅ Crítico: Evidencia técnica de terreno |
| `TABLA_CALCULO` | Level 1 (Crítico) | `total_amount`, `cim_kwh`, `period_start`, `period_end`, `calculation_method` | ✅ Crítico: Base del cálculo de facturación |
| `EVIDENCIA_FOTOGRAFICA` | Level 2 (Soportante) | `photo_count`, `tags`, `geolocation`, `timestamp` | ⚠️ Soportante: Corrobora hallazgos técnicos |
| `GRAFICO_CONSUMO` | Level 2 (Soportante) | `consumption_data`, `period_months`, `trend` | ⚠️ Soportante: Historial de consumo |
| `INFORME_CNR` | Level 2 (Soportante) | `cnr_number`, `installation_date`, `equipment_model` | ⚠️ Soportante: Especificaciones técnicas |
| `OTROS` | Level 2 (Soportante) | `generic_metadata` | ❌ No estructurado |

#### 4.4.2. Algoritmo de Clasificación Multi-Capa

**Estrategia:** Combinar señales de múltiples fuentes con pesos configurables.

**Señales de Clasificación:**

1. **Análisis de Nombre de Archivo** (Peso: 0.3)
   - Patrones regex por tipo
   - Palabras clave en nombre
   - Nomenclatura estandarizada (ej: `RPT_CNR_SEC_10_ref_...`)

2. **Análisis de Contenido** (Peso: 0.5)
   - Presencia de frases clave
   - Estructura de documento (encabezados, tablas)
   - Densidad de términos técnicos

3. **Análisis Estructural** (Peso: 0.2)
   - Presencia de tablas (indica `TABLA_CALCULO`)
   - Presencia de imágenes (indica `EVIDENCIA_FOTOGRAFICA`)
   - Número de páginas

**Implementación:**

```python
class DocumentClassifier:
    """Clasificador multi-capa con scoring de confianza"""
    
    # Patrones por tipo de documento
    PATTERNS = {
        'CARTA_RESPUESTA': {
            'filename': [
                r'respuesta.*reclamo',
                r'rpt_cnr',
                r'resolucion.*cnr'
            ],
            'content': [
                r'respuesta\s+al\s+reclamo',
                r'resoluci[oó]n\s+n[°º]?\s*\d+',
                r'cnr.*resuelve'
            ],
            'structure': ['has_header', 'has_signature']
        },
        'TABLA_CALCULO': {
            'filename': [r'calculo', r'calculacion', r'cnr.*calculo'],
            'content': [
                r'consumo\s+indicado\s+mensual',
                r'cim.*kwh',
                r'tabla\s+de\s+c[aá]lculo'
            ],
            'structure': ['has_table', 'has_numbers']
        },
        'ORDEN_TRABAJO': {
            'filename': [r'orden.*trabajo', r'ot_', r'trabajo.*tecnico'],
            'content': [
                r'orden\s+de\s+trabajo\s+n[°º]?',
                r'visita\s+t[ée]cnica',
                r'equipo\s+de\s+medida'
            ],
            'structure': ['has_technical_fields']
        }
    }
    
    def classify(self, file_path: Path, content: str, 
                 structure: Dict) -> Tuple[str, float]:
        """
        Clasifica documento y retorna (tipo, confianza)
        
        Returns:
            (document_type, confidence_score 0.0-1.0)
        """
        scores = {}
        
        for doc_type, patterns in self.PATTERNS.items():
            score = 0.0
            
            # Señal 1: Nombre de archivo (30%)
            filename_score = self._match_filename(file_path, patterns['filename'])
            score += filename_score * 0.3
            
            # Señal 2: Contenido (50%)
            content_score = self._match_content(content, patterns['content'])
            score += content_score * 0.5
            
            # Señal 3: Estructura (20%)
            structure_score = self._match_structure(structure, patterns['structure'])
            score += structure_score * 0.2
            
            scores[doc_type] = score
        
        # Tipo con mayor score
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]
        
        # Si confianza < 0.6, marcar como OTROS
        if confidence < 0.6:
            return ('OTROS', confidence)
        
        return (best_type, confidence)
```

**Librerías:**
- `regex`: Expresiones regulares avanzadas
- `scikit-learn` (opcional): Clasificación ML si se implementa modelo entrenado

---

### 2.5. Fase 5: Extracción de Entidades Específicas por Tipo

**Principio Clave:** Cada tipo de documento tiene un **esquema de extracción único** que define qué campos se buscan y cómo se almacenan en la base de datos.

#### 5.5.1. Extracción Genérica (Entidades Maestras)

**Entidades que se buscan en TODOS los documentos:**
- **RUT**: Patrón `\d{1,2}\.\d{3}\.\d{3}-[\dkK]`
- **NIS/Número Cliente**: Patrón `(?:nis|cliente\s*n[°º]?)\s*(\d{4,10})`
- **Dirección**: Patrón `(?:av\.?|avenida|calle)\s+[^,\n]+`
- **Comuna**: Lista de comunas conocidas
- **Monto**: Patrón `\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)`

**Librerías:**
- `regex`: Patrones complejos
- `spacy` (opcional): NER (Named Entity Recognition) para direcciones

#### 5.5.2. Extracción Específica: CARTA_RESPUESTA

**Campos a Extraer:**
```python
CARTA_RESPUESTA_SCHEMA = {
    'response_date': {
        'pattern': r'fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        'type': 'date',
        'required': True
    },
    'decision': {
        'pattern': r'(?:resuelve|resoluci[oó]n)[:\s]+(?:procedente|improcedente|rechazado|aceptado)',
        'type': 'enum',
        'values': ['PROCEDENTE', 'IMPROCEDENTE', 'RECHAZADO', 'ACEPTADO'],
        'required': True
    },
    'resolution_number': {
        'pattern': r'resoluci[oó]n\s+n[°º]?\s*(\d+)',
        'type': 'string',
        'required': False
    },
    'cnr_reference': {
        'pattern': r'ref[\.:]?\s*(\d{6,10})',
        'type': 'string',
        'required': False
    },
    'legal_basis': {
        'pattern': r'art[íi]culo\s+(\d+[a-z]?)\s+de\s+la\s+ley',
        'type': 'string',
        'required': False
    }
}
```

**Ejemplo de Extracción:**
```python
def extract_carta_respuesta(content: str) -> Dict[str, Any]:
    """Extrae campos específicos de una Carta de Respuesta"""
    extracted = {}
    
    # Fecha de respuesta
    date_match = re.search(CARTA_RESPUESTA_SCHEMA['response_date']['pattern'], 
                          content, re.IGNORECASE)
    if date_match:
        extracted['response_date'] = normalize_date(date_match.group(1))
    
    # Decisión
    decision_match = re.search(CARTA_RESPUESTA_SCHEMA['decision']['pattern'],
                              content, re.IGNORECASE)
    if decision_match:
        decision_text = decision_match.group(1).upper()
        extracted['decision'] = map_decision(decision_text)
    
    # Número de resolución
    resolution_match = re.search(
        CARTA_RESPUESTA_SCHEMA['resolution_number']['pattern'],
        content, re.IGNORECASE
    )
    if resolution_match:
        extracted['resolution_number'] = resolution_match.group(1)
    
    return extracted
```

#### 5.5.3. Extracción Específica: TABLA_CALCULO

**Campos a Extraer:**
```python
TABLA_CALCULO_SCHEMA = {
    'total_amount': {
        'pattern': r'total[:\s]+\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)',
        'type': 'float',
        'required': True
    },
    'cim_kwh': {
        'pattern': r'cim[:\s]+(\d+(?:[.,]\d+)?)\s*kwh',
        'type': 'float',
        'required': True
    },
    'period_start': {
        'pattern': r'periodo[:\s]+desde[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        'type': 'date',
        'required': False
    },
    'period_end': {
        'pattern': r'hasta[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        'type': 'date',
        'required': False
    },
    'calculation_method': {
        'pattern': r'm[ée]todo[:\s]+(promedio|mediana|estimado)',
        'type': 'enum',
        'values': ['PROMEDIO', 'MEDIANA', 'ESTIMADO'],
        'required': False
    },
    'table_data': {
        'extraction': 'table_parser',  # Extracción de tabla completa
        'type': 'json',
        'required': False
    }
}
```

**Extracción de Tablas:**
```python
def extract_tabla_calculo(content: Dict) -> Dict[str, Any]:
    """Extrae datos de una Tabla de Cálculo"""
    extracted = {}
    
    # Buscar tabla en estructura extraída
    if 'tables' in content:
        for table in content['tables']:
            # Buscar fila con "Total" o "CIM"
            for row in table['data']:
                if any('total' in str(cell).lower() for cell in row):
                    # Extraer monto de la fila
                    amounts = extract_amounts_from_row(row)
                    if amounts:
                        extracted['total_amount'] = max(amounts)
                
                if any('cim' in str(cell).lower() for cell in row):
                    # Extraer CIM
                    kwh_values = extract_kwh_from_row(row)
                    if kwh_values:
                        extracted['cim_kwh'] = kwh_values[0]
        
        # Guardar tabla completa como JSON
        extracted['table_data'] = json.dumps(table['data'])
    
    return extracted
```

#### 5.5.4. Extracción Específica: ORDEN_TRABAJO

**Campos a Extraer:**
```python
ORDEN_TRABAJO_SCHEMA = {
    'ot_number': {
        'pattern': r'orden\s+(?:de\s+)?trabajo\s+n[°º]?\s*(\d+)',
        'type': 'string',
        'required': True
    },
    'technician_name': {
        'pattern': r't[ée]cnico[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        'type': 'string',
        'required': False
    },
    'visit_date': {
        'pattern': r'fecha\s+visita[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        'type': 'date',
        'required': True
    },
    'findings': {
        'extraction': 'section_parser',  # Extraer sección "Hallazgos"
        'type': 'text',
        'required': False
    },
    'equipment_status': {
        'pattern': r'estado\s+equipo[:\s]+(operativo|defectuoso|sin\s+sello)',
        'type': 'enum',
        'values': ['OPERATIVO', 'DEFECTUOSO', 'SIN_SELLO'],
        'required': False
    },
    'recommendations': {
        'extraction': 'section_parser',
        'type': 'text',
        'required': False
    }
}
```

#### 5.5.5. Extracción Específica: EVIDENCIA_FOTOGRAFICA

**Campos a Extraer:**
```python
EVIDENCIA_FOTOGRAFICA_SCHEMA = {
    'photo_count': {
        'extraction': 'file_count',  # Contar archivos de imagen
        'type': 'integer',
        'required': True
    },
    'tags': {
        'extraction': 'image_analysis',  # Análisis de imagen con CV
        'type': 'array',
        'values': ['medidor', 'sello', 'fachada', 'instalacion'],
        'required': False
    },
    'geolocation': {
        'extraction': 'exif_metadata',
        'type': 'coordinates',
        'required': False
    },
    'timestamp': {
        'extraction': 'exif_metadata',
        'type': 'datetime',
        'required': False
    }
}
```

**Análisis de Imágenes con Computer Vision:**
```python
import cv2
from PIL import Image
import exifread

def analyze_photographic_evidence(image_path: Path) -> Dict[str, Any]:
    """Analiza evidencia fotográfica"""
    result = {
        'tags': [],
        'geolocation': None,
        'timestamp': None
    }
    
    # Leer EXIF
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)
        
        # Geolocalización
        if 'GPS GPSLatitude' in tags:
            lat = parse_exif_coordinate(tags['GPS GPSLatitude'])
            lon = parse_exif_coordinate(tags['GPS GPSLongitude'])
            result['geolocation'] = {'lat': lat, 'lon': lon}
        
        # Timestamp
        if 'EXIF DateTimeOriginal' in tags:
            result['timestamp'] = str(tags['EXIF DateTimeOriginal'])
    
    # Análisis de contenido con CV
    img = cv2.imread(str(image_path))
    
    # Detectar objetos (usando modelo pre-entrenado o heurísticas)
    # Ejemplo: Detectar si hay un medidor
    if detect_meter(img):
        result['tags'].append('medidor')
    
    if detect_seal(img):
        result['tags'].append('sello')
    
    return result
```

---

## 3. Estrategia de Persistencia: Esquema Estrella con Campos Específicos

### 3.1. Modelo de Datos Relacional

#### 3.1.1. Tabla PERSONAS

```sql
CREATE TABLE personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rut TEXT UNIQUE NOT NULL,  -- Clave natural
    nombre TEXT,
    email TEXT,
    telefono TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    INDEX idx_rut (rut)
);
```

**Lógica de Upsert:**
```python
def upsert_persona(rut: str, nombre: str = None, 
                   email: str = None, telefono: str = None) -> int:
    """
    Inserta o actualiza una persona
    
    Returns:
        persona_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar existente
    cursor.execute("SELECT id FROM personas WHERE rut = ?", (rut,))
    existing = cursor.fetchone()
    
    if existing:
        persona_id = existing[0]
        # Actualizar solo si nuevos datos son más recientes
        updates = []
        params = []
        
        if nombre:
            updates.append("nombre = ?")
            params.append(nombre)
        if email:
            updates.append("email = COALESCE(?, email)")  # Solo actualizar si no existe
            params.append(email)
        if telefono:
            updates.append("telefono = COALESCE(?, telefono)")
            params.append(telefono)
        
        if updates:
            params.append(persona_id)
            cursor.execute(
                f"UPDATE personas SET {', '.join(updates)}, "
                "fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
                params
            )
    else:
        # Insertar nuevo
        cursor.execute("""
            INSERT INTO personas (rut, nombre, email, telefono)
            VALUES (?, ?, ?, ?)
        """, (rut, nombre, email, telefono))
        persona_id = cursor.lastrowid
    
    conn.commit()
    return persona_id
```

#### 3.1.2. Tabla SUMINISTROS

```sql
CREATE TABLE suministros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nis TEXT NOT NULL,
    comuna TEXT NOT NULL,
    direccion TEXT,
    numero_cliente TEXT,
    coordenadas_lat REAL,
    coordenadas_lon REAL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Clave única compuesta
    UNIQUE(nis, comuna),
    
    -- Índices
    INDEX idx_nis (nis),
    INDEX idx_comuna (comuna)
);
```

**Lógica de Upsert:**
```python
def upsert_suministro(nis: str, comuna: str, direccion: str = None,
                      numero_cliente: str = None) -> int:
    """
    Inserta o actualiza un suministro
    
    Returns:
        suministro_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar existente
    cursor.execute(
        "SELECT id FROM suministros WHERE nis = ? AND comuna = ?",
        (nis, comuna)
    )
    existing = cursor.fetchone()
    
    if existing:
        suministro_id = existing[0]
        # Actualizar dirección si es más completa
        if direccion:
            cursor.execute("""
                UPDATE suministros 
                SET direccion = COALESCE(?, direccion),
                    numero_cliente = COALESCE(?, numero_cliente)
                WHERE id = ?
            """, (direccion, numero_cliente, suministro_id))
    else:
        cursor.execute("""
            INSERT INTO suministros (nis, comuna, direccion, numero_cliente)
            VALUES (?, ?, ?, ?)
        """, (nis, comuna, direccion, numero_cliente))
        suministro_id = cursor.lastrowid
    
    conn.commit()
    return suministro_id
```

#### 3.1.3. Tabla CASOS

```sql
CREATE TABLE casos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id TEXT UNIQUE NOT NULL,  -- Clave natural SEC
    persona_id INTEGER NOT NULL,
    suministro_id INTEGER NOT NULL,
    empresa TEXT,
    materia TEXT,
    monto_disputa REAL,
    fecha_ingreso DATE,
    estado TEXT DEFAULT 'PENDIENTE',
    edn_json TEXT,  -- EDN completo como JSON
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (persona_id) REFERENCES personas(id),
    FOREIGN KEY (suministro_id) REFERENCES suministros(id),
    
    INDEX idx_case_id (case_id),
    INDEX idx_persona (persona_id),
    INDEX idx_suministro (suministro_id),
    INDEX idx_estado (estado)
);
```

#### 3.1.4. Tabla DOCUMENTOS (Esquema Diferenciado por Tipo)

**Diseño Clave:** La tabla `documentos` tiene un campo `extracted_data` de tipo JSONB que almacena **campos específicos según el tipo de documento**.

```sql
CREATE TABLE documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id INTEGER NOT NULL,
    file_id TEXT UNIQUE NOT NULL,  -- UUID interno
    original_name TEXT NOT NULL,
    standardized_name TEXT,
    type TEXT NOT NULL,  -- CARTA_RESPUESTA, TABLA_CALCULO, etc.
    level TEXT,  -- level_1_critical, level_2_supporting
    file_path TEXT,  -- Ruta relativa al storage
    file_size INTEGER,
    mime_type TEXT,
    
    -- Campo JSONB con datos específicos por tipo
    extracted_data JSON,  -- SQLite JSON o PostgreSQL JSONB
    
    -- Metadatos genéricos
    metadata JSON,
    
    -- Timestamps
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (caso_id) REFERENCES casos(id),
    
    INDEX idx_caso (caso_id),
    INDEX idx_type (type),
    INDEX idx_file_id (file_id)
);
```

**Ejemplos de `extracted_data` por Tipo:**

**CARTA_RESPUESTA:**
```json
{
  "response_date": "2023-12-21",
  "decision": "IMPROCEDENTE",
  "resolution_number": "12345",
  "cnr_reference": "231220-000557",
  "legal_basis": "Art. 45 Ley General de Servicios Eléctricos"
}
```

**TABLA_CALCULO:**
```json
{
  "total_amount": 150000.0,
  "cim_kwh": 450.5,
  "period_start": "2023-10-01",
  "period_end": "2023-12-31",
  "calculation_method": "PROMEDIO",
  "table_data": [
    ["Mes", "Consumo", "Monto"],
    ["Octubre", "420", "140000"],
    ["Noviembre", "450", "150000"]
  ]
}
```

**ORDEN_TRABAJO:**
```json
{
  "ot_number": "OT-2023-1234",
  "technician_name": "Juan Pérez",
  "visit_date": "2023-12-15",
  "findings": "Medidor operativo, sello intacto",
  "equipment_status": "OPERATIVO",
  "recommendations": "Sin observaciones"
}
```

**EVIDENCIA_FOTOGRAFICA:**
```json
{
  "photo_count": 3,
  "tags": ["medidor", "sello", "fachada"],
  "geolocation": {
    "lat": -33.4489,
    "lon": -70.6693
  },
  "timestamp": "2023-12-15T10:30:00"
}
```

**Ventajas de este Diseño:**
1. **Flexibilidad**: Cada tipo de documento puede tener campos únicos sin modificar el esquema
2. **Consultas Analíticas**: PostgreSQL JSONB permite consultas eficientes sobre campos específicos
3. **Evolución**: Nuevos tipos de documentos pueden agregarse sin migraciones

**Ejemplo de Consulta Analítica (PostgreSQL):**
```sql
-- Encontrar todas las cartas de respuesta con decisión "IMPROCEDENTE"
SELECT d.*, c.case_id
FROM documentos d
JOIN casos c ON d.caso_id = c.id
WHERE d.type = 'CARTA_RESPUESTA'
  AND d.extracted_data->>'decision' = 'IMPROCEDENTE';

-- Calcular promedio de montos en tablas de cálculo
SELECT AVG((extracted_data->>'total_amount')::numeric) as promedio_monto
FROM documentos
WHERE type = 'TABLA_CALCULO';
```

---

### 3.2. Lógica de Upsert Completa

**Flujo de Procesamiento de un Caso:**

```python
def process_case_to_database(case_id: str, edn: Dict[str, Any]) -> int:
    """
    Procesa un EDN y lo persiste en la base de datos relacional
    
    Returns:
        caso_id (PK de la tabla casos)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Resolver/crear PERSONA
        unified_context = edn['unified_context']
        persona_id = upsert_persona(
            rut=unified_context['rut_client'],
            nombre=unified_context['client_name'],
            email=unified_context.get('email'),
            telefono=unified_context.get('phone')
        )
        
        # 2. Resolver/crear SUMINISTRO
        suministro_id = upsert_suministro(
            nis=unified_context['service_nis'],
            comuna=unified_context['commune'],
            direccion=unified_context.get('address_standard'),
            numero_cliente=unified_context.get('service_nis')  # Puede ser diferente
        )
        
        # 3. Crear/actualizar CASO (idempotente)
        cursor.execute("""
            INSERT INTO casos (
                case_id, persona_id, suministro_id, empresa,
                materia, monto_disputa, fecha_ingreso, edn_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(case_id) DO UPDATE SET
                fecha_actualizacion = CURRENT_TIMESTAMP,
                edn_json = excluded.edn_json
        """, (
            case_id, persona_id, suministro_id,
            edn.get('empresa'), edn.get('materia'),
            edn.get('monto_disputa'), edn.get('fecha_ingreso'),
            json.dumps(edn)
        ))
        
        caso_db_id = cursor.lastrowid
        
        # 4. Insertar DOCUMENTOS (con extracted_data específico)
        document_inventory = edn['document_inventory']
        
        for level in ['level_1_critical', 'level_2_supporting']:
            for doc in document_inventory.get(level, []):
                # Extraer datos específicos según tipo
                extracted_data = doc.get('extracted_data', {})
                
                cursor.execute("""
                    INSERT INTO documentos (
                        caso_id, file_id, original_name, standardized_name,
                        type, level, file_path, extracted_data, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(file_id) DO NOTHING
                """, (
                    caso_db_id, doc['file_id'], doc['original_name'],
                    doc.get('standardized_name'), doc['type'], level,
                    doc.get('file_path'), json.dumps(extracted_data),
                    json.dumps(doc.get('metadata', {}))
                ))
        
        conn.commit()
        return caso_db_id
        
    except Exception as e:
        conn.rollback()
        raise
```

---

## 4. Generación del Expediente Digital Normalizado (EDN)

### 4.1. Estructura del EDN

El EDN es el **contrato de datos** que alimenta todos los módulos posteriores. Debe ser **completo, normalizado y validado**.

```json
{
  "compilation_metadata": {
    "case_id": "231220-000557",
    "processing_timestamp": "2023-12-20T14:30:00Z",
    "status": "COMPLETED",
    "processing_version": "1.0",
    "errors": []
  },
  "unified_context": {
    "rut_client": "12.345.678-9",
    "client_name": "Juan Pérez González",
    "service_nis": "5854164",
    "address_standard": "Av. Providencia 1234, Depto 45",
    "commune": "Providencia",
    "email": "juan.perez@email.com",
    "phone": "+56912345678"
  },
  "document_inventory": {
    "level_1_critical": [
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
    ],
    "level_2_supporting": [],
    "level_0_missing": [
      {
        "required_type": "ORDEN_TRABAJO",
        "alert_level": "HIGH",
        "description": "No se detectó documento técnico de terreno."
      }
    ]
  },
  "materia": "Facturación",
  "monto_disputa": 150000.0,
  "empresa": "ENEL",
  "fecha_ingreso": "2023-12-20",
  "alertas": []
}
```

### 4.2. Algoritmo de Construcción del EDN

```python
def build_edn(case_id: str, processed_documents: List[Dict],
              case_metadata: Dict) -> Dict[str, Any]:
    """
    Construye el EDN a partir de documentos procesados
    """
    # 1. Agregar metadatos de compilación
    compilation_metadata = {
        'case_id': case_id,
        'processing_timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': 'COMPLETED',
        'processing_version': '1.0',
        'errors': []
    }
    
    # 2. Construir unified_context (consolidar entidades de todos los docs)
    unified_context = consolidate_entities(processed_documents)
    
    # 3. Organizar documentos por nivel
    document_inventory = {
        'level_1_critical': [],
        'level_2_supporting': [],
        'level_0_missing': []
    }
    
    for doc in processed_documents:
        level = doc['level']
        document_inventory[level].append({
            'type': doc['type'],
            'file_id': doc['file_id'],
            'original_name': doc['original_name'],
            'standardized_name': doc.get('standardized_name'),
            'file_path': doc['file_path'],
            'extracted_data': doc.get('extracted_data', {}),
            'metadata': doc.get('metadata', {})
        })
    
    # 4. Detectar documentos faltantes
    required_types = ['CARTA_RESPUESTA', 'TABLA_CALCULO', 'ORDEN_TRABAJO']
    found_types = {doc['type'] for doc in processed_documents}
    
    for req_type in required_types:
        if req_type not in found_types:
            document_inventory['level_0_missing'].append({
                'required_type': req_type,
                'alert_level': 'HIGH',
                'description': f'No se detectó {req_type}'
            })
    
    # 5. Construir EDN final
    edn = {
        'compilation_metadata': compilation_metadata,
        'unified_context': unified_context,
        'document_inventory': document_inventory,
        'materia': case_metadata.get('materia'),
        'monto_disputa': extract_max_amount(processed_documents),
        'empresa': case_metadata.get('empresa'),
        'fecha_ingreso': case_metadata.get('fecha_ingreso'),
        'alertas': detect_alerts(unified_context, processed_documents)
    }
    
    return edn

def consolidate_entities(documents: List[Dict]) -> Dict[str, Any]:
    """Consolida entidades de todos los documentos"""
    all_ruts = set()
    all_nis = set()
    all_addresses = []
    all_communes = set()
    
    for doc in documents:
        entities = doc.get('entities', {})
        if entities.get('rut'):
            all_ruts.add(entities['rut'])
        if entities.get('nis'):
            all_nis.add(entities['nis'])
        if entities.get('address'):
            all_addresses.append(entities['address'])
        if entities.get('commune'):
            all_communes.add(entities['commune'])
    
    # Resolver conflictos (tomar el más frecuente o el de mayor confianza)
    rut = resolve_entity(all_ruts) if all_ruts else None
    nis = resolve_entity(all_nis) if all_nis else None
    address = resolve_address(all_addresses) if all_addresses else None
    commune = resolve_entity(all_communes) if all_communes else None
    
    return {
        'rut_client': rut or 'N/A',
        'client_name': extract_name_from_documents(documents),
        'service_nis': nis or 'N/A',
        'address_standard': address,
        'commune': commune or 'Desconocida',
        'email': extract_email_from_documents(documents),
        'phone': extract_phone_from_documents(documents)
    }
```

---

## 5. Manejo de Errores y Casos Edge

### 5.1. Estrategia de Tolerancia a Fallos

**Principio:** Un documento fallido no debe detener el procesamiento del caso completo.

**Implementación:**
```python
def process_case_robust(case_id: str, files: List[Path]) -> Dict[str, Any]:
    """Procesa un caso con manejo robusto de errores"""
    errors = []
    processed_docs = []
    
    for file_path in files:
        try:
            doc = process_file(file_path)
            processed_docs.append(doc)
        except PDFCorruptError as e:
            errors.append({
                'file': file_path.name,
                'error': 'PDF corrupto',
                'action': 'marcado_para_revision_manual'
            })
            # Continuar con siguiente archivo
            continue
        except OCRFailedError as e:
            errors.append({
                'file': file_path.name,
                'error': 'OCR falló',
                'action': 'marcado_como_imagen_sin_texto'
            })
            # Procesar como imagen sin texto
            doc = process_as_image_only(file_path)
            processed_docs.append(doc)
        except Exception as e:
            errors.append({
                'file': file_path.name,
                'error': str(e),
                'action': 'registrado_en_log'
            })
            # Continuar
    
    # Construir EDN incluso con errores
    edn = build_edn(case_id, processed_docs, {})
    edn['compilation_metadata']['errors'] = errors
    edn['compilation_metadata']['status'] = 'COMPLETED_WITH_WARNINGS' if errors else 'COMPLETED'
    
    return edn
```

### 5.2. Validación de Integridad

**Validaciones Post-Procesamiento:**
1. **RUT válido**: Verificar dígito verificador
2. **NIS válido**: Rango numérico razonable
3. **Fechas consistentes**: `fecha_ingreso` <= `response_date` (si existe)
4. **Montos razonables**: Entre 1.000 y 10.000.000 CLP
5. **Documentos críticos**: Al menos uno de `CARTA_RESPUESTA` o `TABLA_CALCULO`

---

## 6. Librerías y Tecnologías Recomendadas

### 6.1. Stack Tecnológico

| Componente | Librería | Versión Mínima | Propósito |
|------------|----------|----------------|-----------|
| **PDF Processing** | `pdfplumber` | 0.9.0 | Extracción de texto y tablas |
| **PDF Validation** | `pypdf` | 3.0.0 | Validación y reparación |
| **OCR** | `pytesseract` | 0.3.10 | Reconocimiento óptico de caracteres |
| **Image Processing** | `Pillow` | 10.0.0 | Procesamiento de imágenes |
| **Computer Vision** | `opencv-python` | 4.8.0 | Análisis de imágenes |
| **Word Documents** | `python-docx` | 1.1.0 | Lectura de documentos Word |
| **Regex** | `regex` | 2023.0.0 | Expresiones regulares avanzadas |
| **Database** | `sqlalchemy` | 2.0.0 | ORM y gestión de BD |
| **Date Parsing** | `dateutil` | 2.8.0 | Parsing flexible de fechas |
| **NLP (Opcional)** | `spacy` | 3.7.0 | Named Entity Recognition |

### 6.2. Herramientas Externas (CLI)

- **qpdf**: Reparación de PDFs corruptos
- **ghostscript**: Conversión a PDF/A
- **tesseract-ocr**: Motor OCR (requiere instalación del sistema)

---

## 7. Flujo Completo: Ejemplo de Procesamiento

### 7.1. Caso de Uso: Procesar Lote de Archivos

**Input:**
```
case_id: "231220-000557"
files:
  - "Respuesta_Reclamo_2642280.pdf"
  - "1982860-Calculo_2023_9677.pdf"
  - "foto_medidor_1.jpg"
  - "foto_medidor_2.jpg"
```

**Procesamiento:**

1. **Sanitización:**
   - `Respuesta_Reclamo_2642280.pdf` → PDF válido, tiene capa de texto
   - `1982860-Calculo_2023_9677.pdf` → PDF válido, tiene capa de texto
   - `foto_medidor_1.jpg` → Imagen válida
   - `foto_medidor_2.jpg` → Imagen válida

2. **Extracción de Texto:**
   - PDFs → Extracción directa con `pdfplumber`
   - Imágenes → OCR con `pytesseract`

3. **Clasificación:**
   - `Respuesta_Reclamo_2642280.pdf` → `CARTA_RESPUESTA` (confianza: 0.95)
   - `1982860-Calculo_2023_9677.pdf` → `TABLA_CALCULO` (confianza: 0.92)
   - `foto_medidor_1.jpg` → `EVIDENCIA_FOTOGRAFICA` (confianza: 1.0)
   - `foto_medidor_2.jpg` → `EVIDENCIA_FOTOGRAFICA` (confianza: 1.0)

4. **Extracción de Entidades:**

   **CARTA_RESPUESTA:**
   ```json
   {
     "response_date": "2023-12-21",
     "decision": "IMPROCEDENTE",
     "resolution_number": "12345"
   }
   ```

   **TABLA_CALCULO:**
   ```json
   {
     "total_amount": 150000.0,
     "cim_kwh": 450.5,
     "period_start": "2023-10-01",
     "period_end": "2023-12-31"
   }
   ```

   **EVIDENCIA_FOTOGRAFICA:**
   ```json
   {
     "photo_count": 2,
     "tags": ["medidor", "sello"]
   }
   ```

5. **Consolidación de Entidades:**
   - RUT: `12.345.678-9` (encontrado en CARTA_RESPUESTA)
   - NIS: `5854164` (encontrado en nombre de archivo y TABLA_CALCULO)
   - Dirección: `Av. Providencia 1234` (encontrado en CARTA_RESPUESTA)
   - Comuna: `Providencia` (encontrado en CARTA_RESPUESTA)

6. **Persistencia en BD:**
   - Upsert PERSONA (RUT: `12.345.678-9`)
   - Upsert SUMINISTRO (NIS: `5854164`, Comuna: `Providencia`)
   - Insert CASO (vinculando persona y suministro)
   - Insert 4 DOCUMENTOS (cada uno con su `extracted_data` específico)

7. **Generación de EDN:**
   - EDN completo con todos los documentos clasificados
   - `level_0_missing`: `["ORDEN_TRABAJO"]` (no encontrado)

---

## 8. Consideraciones de Performance y Escalabilidad

### 8.1. Optimizaciones

- **Procesamiento Paralelo**: Procesar múltiples archivos en paralelo (usar `multiprocessing` o `asyncio`)
- **Caché de OCR**: Si un PDF ya fue procesado, no re-ejecutar OCR
- **Índices de BD**: Índices en `rut`, `nis`, `case_id`, `type`
- **Batch Inserts**: Insertar documentos en lotes

### 8.2. Monitoreo

- **Métricas**: Tiempo de procesamiento por documento, tasa de éxito de OCR, precisión de clasificación
- **Logging**: Registrar todos los pasos del pipeline para debugging

---

## 9. Conclusión

El OMC es el corazón del sistema de ingesta de la SEC. Su diseño permite:

1. **Transformar documentos no estructurados** en datos analizables
2. **Construir una base de datos histórica** que preserva la relación entre actores y eventos
3. **Generar un contrato de datos estandarizado** (EDN) que alimenta todos los módulos posteriores
4. **Mantener flexibilidad** mediante esquemas JSON específicos por tipo de documento
5. **Garantizar robustez** mediante manejo de errores y validaciones

La clave del éxito está en **reconocer que cada tipo de documento tiene información única** y diseñar el sistema para extraer y almacenar esa información de manera estructurada y consultable.

