# Guía de Diseño Visual para Figma - Sistema de Análisis de Reclamos SEC

Este documento proporciona la estructura completa del sistema para diseñar el diagrama visual en Figma.

## 1. ARQUITECTURA GENERAL - 3 CAPAS PRINCIPALES

### Capa 1: ENTRADA (Input Layer)
- **Color sugerido**: Azul claro (#E3F2FD)
- **Componentes**:
  - Reclamo JSON (archivo de entrada)
  - Credenciales (opcional, para scraping)
  - Base de Datos (boletas existentes)

### Capa 2: PROCESAMIENTO (Processing Layer)
- **Color sugerido**: Amarillo/Naranja (#FFF3E0)
- **Módulos principales**:
  - Obtención de Boletas
  - Consolidación Jurídico-Técnica
  - Ficha Técnica y Checklist
  - Utilidades (Config, Logger, Base de Datos)

### Capa 3: SALIDA (Output Layer)
- **Color sugerido**: Verde claro (#E8F5E9)
- **Documentos generados**:
  - Expediente (JSON/TXT)
  - Ficha Técnica (PDF/HTML)
  - Checklist (PDF/HTML/JSON)
  - Informe Ejecutivo (estructura JSON)
  - Instrucciones (estructura JSON)

---

## 2. ESTRUCTURA DE MÓDULOS DETALLADA

### MÓDULO 1: OBTENCIÓN DE BOLETAS
**Ubicación**: `modulos/obtencion_boletas/`
**Color**: #2196F3 (Azul)

#### Componentes:
1. **ScraperBase** (`scraper_base.py`)
   - Clase abstracta base
   - Funcionalidades comunes: sesiones, retry, logging
   - **Conexiones**: Heredado por scrapers específicos

2. **ScraperFactory** (`scrapers/scraper_factory.py`)
   - Crea scrapers según distribuidora
   - **Conexiones**: 
     - Recibe: nombre distribuidora
     - Crea: Scraper específico (Enel, CGE, etc.)

3. **EnelScraper** (`scrapers/enel_scraper.py`)
   - Implementación específica para Enel
   - **Conexiones**:
     - Hereda de: ScraperBase
     - Usa: ExtractorDatos, ValidadorBoletas
     - Retorna: Lista de boletas

4. **ExtractorDatos** (`procesamiento/extractor_datos.py`)
   - Parsea PDF/HTML a JSON estructurado
   - **Conexiones**:
     - Recibe: PDF/HTML de boletas
     - Retorna: Datos estructurados

5. **ValidadorBoletas** (`procesamiento/validador_boletas.py`)
   - Valida completitud y corrección de datos
   - **Conexiones**:
     - Recibe: Boletas extraídas
     - Retorna: Boletas validadas
     - Guarda en: BaseDatos

**Flujo interno**:
```
ScraperFactory → Scraper Específico → Login → Obtener Boletas → 
ExtractorDatos → ValidadorBoletas → BaseDatos
```

---

### MÓDULO 2: CONSOLIDACIÓN JURÍDICO-TÉCNICA
**Ubicación**: `modulos/consolidacion_juridico_tecnica/`
**Color**: #FF9800 (Naranja)

#### Componentes:
1. **ClasificadorTipologias** (`clasificador_tipologias.py`)
   - Clasifica reclamo según tipología SEC
   - **Conexiones**:
     - Recibe: Reclamo
     - Usa: Manual SEC (JSON)
     - Retorna: Tipología identificada + confianza

2. **AnalizadorReclamos** (`analizador_reclamos.py`)
   - Analiza reclamo según procedimiento específico
   - **Conexiones**:
     - Recibe: Reclamo, Boletas, Tipología
     - Usa: Manual SEC, Resolución 1952
     - Retorna: Análisis completo
   - **Tipologías implementadas**:
     - ✅ Facturación Excesiva (completo)
     - ⚠️ Otras (placeholders)

3. **EvaluadorCumplimiento** (`evaluador_cumplimiento.py`)
   - Evalúa cumplimiento normativo
   - **Conexiones**:
     - Recibe: Expediente, Tipología
     - Evalúa: Plazos, Medios probatorios, Consistencia, Respuesta
     - Retorna: Evaluación de cumplimiento

4. **GeneradorExpediente** (`generador_expediente.py`)
   - Genera expediente estructurado
   - **Conexiones**:
     - Recibe: Reclamo, Clasificación, Análisis, Boletas
     - Retorna: Expediente completo (JSON/TXT)
     - Guarda en: BaseDatos y archivos

**Flujo interno**:
```
ClasificadorTipologias → AnalizadorReclamos → GeneradorExpediente → 
EvaluadorCumplimiento → Expediente Completo
```

---

### MÓDULO 3: FICHA TÉCNICA Y CHECKLIST
**Ubicación**: `modulos/ficha_tecnica_checklist/`
**Color**: #4CAF50 (Verde)

#### Componentes:
1. **GeneradorInforme** (`generador_informe.py`)
   - Genera informe ejecutivo
   - **Conexiones**:
     - Recibe: Expediente, Análisis, Cumplimiento
     - Retorna: Informe estructurado (JSON)
     - Formatea: Texto legible

2. **GeneradorInstrucciones** (`generador_instrucciones.py`)
   - Genera instrucciones automáticas
   - **Conexiones**:
     - Recibe: Expediente, Análisis, Cumplimiento
     - Retorna: Instrucciones estructuradas (JSON)
     - Formatea: Texto legible

3. **GeneradorFicha** (`generador_ficha.py`)
   - Genera ficha técnica completa
   - **Conexiones**:
     - Recibe: Expediente, Análisis, Cumplimiento
     - Usa: GeneradorInforme, GeneradorInstrucciones
     - Usa: Templates HTML
     - Genera: Gráficos (matplotlib)
     - Retorna: PDF/HTML

4. **ChecklistCumplimiento** (`checklist_cumplimiento.py`)
   - Genera checklist verificable
   - **Conexiones**:
     - Recibe: Expediente, Cumplimiento
     - Usa: Templates HTML
     - Retorna: PDF/HTML/JSON

**Flujo interno**:
```
GeneradorInforme + GeneradorInstrucciones → GeneradorFicha → PDF/HTML
EvaluadorCumplimiento → ChecklistCumplimiento → PDF/HTML/JSON
```

---

### MÓDULO 4: UTILIDADES
**Ubicación**: `modulos/utils/`
**Color**: #9E9E9E (Gris)

#### Componentes:
1. **Config** (`config.py`)
   - Gestión de configuración
   - **Conexiones**: Usado por todos los módulos

2. **Logger** (`logger.py`)
   - Sistema de logging
   - **Conexiones**: Usado por todos los módulos

3. **BaseDatos** (`base_datos.py`)
   - Gestión de base de datos SQLite
   - **Conexiones**:
     - Almacena: Reclamos, Boletas, Expedientes
     - Consulta: Boletas por cliente

---

### MÓDULO 5: ORQUESTADOR PRINCIPAL
**Ubicación**: `modulos/main.py`
**Color**: #9C27B0 (Púrpura)

#### Componente:
**SistemaAnalisisReclamos** (clase principal)
- Orquesta todo el flujo
- **Conexiones**: Conecta todos los módulos

---

## 3. FLUJO COMPLETO DE DATOS (10 PASOS)

### Visualización del Flujo:

```
[ENTRADA]
  └─ Reclamo JSON
  └─ Credenciales (opcional)

[PASO 1] Obtener Boletas
  ├─ ScraperFactory → Scraper Específico
  ├─ Login → Obtener Boletas
  ├─ ExtractorDatos → Parsear
  ├─ ValidadorBoletas → Validar
  └─ BaseDatos → Guardar

[PASO 2] Clasificar Tipología
  ├─ ClasificadorTipologias
  └─ Manual SEC (JSON)

[PASO 3] Analizar Reclamo
  ├─ AnalizadorReclamos
  ├─ Boletas
  └─ Manual SEC / Resolución 1952

[PASO 4] Generar Expediente
  └─ GeneradorExpediente

[PASO 5] Evaluar Cumplimiento
  └─ EvaluadorCumplimiento

[PASO 6] Generar Informe
  └─ GeneradorInforme

[PASO 7] Generar Instrucciones
  └─ GeneradorInstrucciones

[PASO 8] Generar Ficha Técnica
  ├─ GeneradorFicha
  ├─ GeneradorInforme
  ├─ GeneradorInstrucciones
  └─ Templates HTML

[PASO 9] Generar Checklist
  └─ ChecklistCumplimiento

[PASO 10] Guardar Resultados
  └─ BaseDatos

[SALIDA]
  ├─ Expediente (JSON/TXT)
  ├─ Ficha Técnica (PDF/HTML)
  ├─ Checklist (PDF/HTML/JSON)
  ├─ Informe (JSON)
  └─ Instrucciones (JSON)
```

---

## 4. CONEXIONES ENTRE MÓDULOS

### Conexiones Principales:

1. **main.py → Todos los módulos**
   - Inicializa y orquesta todo

2. **Obtención Boletas → BaseDatos**
   - Guarda boletas obtenidas

3. **Clasificador → Analizador**
   - Tipología identificada → Análisis específico

4. **Analizador → GeneradorExpediente**
   - Análisis → Expediente estructurado

5. **EvaluadorCumplimiento → GeneradorExpediente**
   - Cumplimiento → Expediente completo

6. **GeneradorFicha → GeneradorInforme + GeneradorInstrucciones**
   - Usa ambos para generar ficha completa

7. **Todos → Logger**
   - Todos los módulos registran eventos

8. **Todos → Config**
   - Todos los módulos usan configuración

---

## 5. ESTRUCTURA DE DATOS

### Entrada:
- **Reclamo**: JSON con número, cliente, distribuidora, descripción
- **Credenciales**: JSON con usuario/password (opcional)

### Procesamiento:
- **Boletas**: Lista de diccionarios con datos estructurados
- **Clasificación**: Tipología + confianza
- **Análisis**: Resultado del análisis técnico
- **Cumplimiento**: Evaluación normativa
- **Expediente**: Estructura completa

### Salida:
- **Expediente**: JSON/TXT
- **Ficha Técnica**: PDF/HTML
- **Checklist**: PDF/HTML/JSON
- **Informe**: Estructura JSON
- **Instrucciones**: Estructura JSON

---

## 6. ALMACENAMIENTO

### Base de Datos (SQLite):
- **Tabla: reclamos**
  - ID, número_reclamo, cliente, distribuidora, tipología, fecha_ingreso, estado, datos_reclamo

- **Tabla: boletas**
  - ID, número_cliente, distribuidora, período, número_boleta, consumo_kwh, monto_total, datos_boleta

- **Tabla: expedientes**
  - ID, id_reclamo, tipología, análisis, medios_probatorios, cumplimiento

### Archivos:
- **Expedientes**: `data/expedientes/EXP-{NUMERO}-{FECHA}.{json|txt}`
- **Fichas Técnicas**: `data/expedientes/FICHA-{NUMERO}-{FECHA}.{pdf|html}`
- **Checklists**: `data/expedientes/CHECKLIST-{NUMERO}-{FECHA}.{pdf|html|json}`
- **Logs**: `logs/sec_reclamos.log`

---

## 7. DEPENDENCIAS EXTERNAS

### Bibliotecas Python:
- **Selenium**: Web scraping
- **BeautifulSoup4**: Parsing HTML
- **pdfplumber**: Parsing PDFs
- **reportlab**: Generación PDF
- **matplotlib**: Gráficos
- **sqlalchemy**: Base de datos
- **pyyaml**: Configuración

### Recursos:
- **Manual SEC**: `docs/manual_reclamos_2025.json`
- **Resolución 1952**: `docs/resolucion_exenta_1952.json`
- **Templates HTML**: `modulos/ficha_tecnica_checklist/templates/`

---

## 8. SUGERENCIAS DE DISEÑO PARA FIGMA

### Colores por Módulo:
- **Obtención Boletas**: #2196F3 (Azul)
- **Consolidación Jurídico-Técnica**: #FF9800 (Naranja)
- **Ficha Técnica**: #4CAF50 (Verde)
- **Utilidades**: #9E9E9E (Gris)
- **Orquestador**: #9C27B0 (Púrpura)

### Formas Sugeridas:
- **Módulos principales**: Rectángulos redondeados grandes
- **Componentes**: Rectángulos medianos
- **Base de datos**: Cilindro
- **Archivos**: Documento con esquina doblada
- **Flujo de datos**: Flechas con etiquetas

### Capas Visuales:
1. **Fondo**: Estructura general (3 capas)
2. **Módulos**: Agrupaciones por color
3. **Componentes**: Dentro de cada módulo
4. **Conexiones**: Flechas entre componentes
5. **Datos**: Etiquetas de entrada/salida

### Anotaciones:
- Agregar notas explicativas en cada módulo
- Indicar estado de implementación (✅ Completo, ⚠️ Parcial, ❌ Pendiente)
- Mostrar flujo numérico (Paso 1, Paso 2, etc.)
- Incluir leyenda de colores y símbolos

---

## 9. ELEMENTOS ESPECIALES A DESTACAR

### Puntos de Entrada:
- Reclamo JSON (archivo)
- Credenciales (opcional)
- Base de Datos (boletas existentes)

### Puntos de Salida:
- Expediente
- Ficha Técnica
- Checklist
- Informe
- Instrucciones

### Puntos de Decisión:
- ¿Obtener boletas por scraping?
- ¿Qué distribuidora? (Factory pattern)
- ¿Qué tipología? (Clasificador)
- ¿Cumple o no cumple? (Evaluador)

### Recursos Externos:
- Manual SEC (JSON)
- Resolución 1952 (JSON)
- Templates HTML
- Portales de distribuidoras (web scraping)

---

## 10. VISTAS SUGERIDAS

### Vista 1: Arquitectura General
- 3 capas principales (Entrada, Procesamiento, Salida)
- Módulos principales como bloques grandes
- Conexiones principales entre módulos

### Vista 2: Flujo Detallado
- 10 pasos numerados
- Flujo secuencial con decisiones
- Datos que fluyen en cada paso

### Vista 3: Módulo por Módulo
- Desglose de cada módulo
- Componentes internos
- Conexiones internas

### Vista 4: Estructura de Datos
- Formato de entrada
- Transformaciones
- Formato de salida

### Vista 5: Almacenamiento
- Base de datos (tablas)
- Archivos generados
- Logs

---

## 11. NOTAS PARA EL DISEÑO

1. **Modularidad**: Cada módulo debe ser visualmente independiente pero conectado
2. **Flujo claro**: Las flechas deben mostrar claramente el flujo de datos
3. **Jerarquía**: Módulos principales más grandes, componentes más pequeños
4. **Colores consistentes**: Usar la misma paleta de colores en todo el diagrama
5. **Legibilidad**: Texto claro y legible, tamaños apropiados
6. **Completitud**: Indicar qué está implementado y qué está pendiente
7. **Interactividad**: En Figma, puedes hacer frames interactivos para navegar entre vistas

---

## 12. CHECKLIST PARA EL DISEÑO

- [ ] Vista de arquitectura general (3 capas)
- [ ] Todos los módulos principales representados
- [ ] Componentes dentro de cada módulo
- [ ] Flujo completo de 10 pasos
- [ ] Conexiones entre módulos
- [ ] Puntos de entrada y salida
- [ ] Base de datos y almacenamiento
- [ ] Recursos externos (Manual SEC, Templates)
- [ ] Leyenda de colores y símbolos
- [ ] Anotaciones de estado (completo/parcial/pendiente)
- [ ] Formato de datos (entrada/procesamiento/salida)

---

Este documento te servirá como guía completa para diseñar el diagrama visual en Figma. Puedes usar cada sección como referencia para crear diferentes vistas o capas en tu diseño.

