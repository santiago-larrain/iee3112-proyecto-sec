# Manual de Uso - Sistema de Análisis de Reclamos SEC

## 1. Introducción y Objetivos

El Sistema de Análisis de Reclamos SEC es una herramienta automatizada diseñada para:

- Extraer y procesar boletas de facturación de distribuidoras eléctricas mediante web scraping
- Clasificar reclamos según las tipologías definidas en el Manual de Reclamos SEC 2025
- Analizar reclamos aplicando los procedimientos normativos específicos de cada tipología
- Generar expedientes estructurados con análisis jurídico-técnico
- Evaluar el cumplimiento normativo de las respuestas de las distribuidoras

### Alcance

El sistema está diseñado para procesar los siguientes tipos de reclamos:

1. **Facturación Excesiva** (Anexo N°1)
2. **Error de Lectura** (Anexo N°1.1)
3. **Facturación Provisoria** (Anexo N°2)
4. **Cobros Indebidos** (Anexo N°3)
5. **Atención Comercial** (Anexo N°4)
6. **Calidad de Suministro** (Anexo N°5)
7. **No Cumplimiento de Instrucción** (Anexo N°6)
8. **Consumos No Registrados (CNR)** (Resolución Exenta 1952)

## 2. Arquitectura del Sistema

### Estructura de Módulos

```
modulos/
├── obtencion_boletas/          # Web scraping de boletas
│   ├── scraper_base.py         # Clase base para scrapers
│   ├── scrapers/               # Scrapers específicos por distribuidora
│   └── procesamiento/          # Extracción y validación de datos
├── consolidacion_juridico_tecnica/  # Análisis jurídico-técnico
│   ├── clasificador_tipologias.py
│   ├── analizador_reclamos.py
│   ├── evaluador_cumplimiento.py
│   └── generador_expediente.py
├── ficha_tecnica_checklist/    # Generación de fichas técnicas y checklist
│   ├── generador_ficha.py      # Genera ficha técnica PDF/HTML
│   ├── generador_informe.py    # Genera informe ejecutivo
│   ├── generador_instrucciones.py  # Genera instrucciones automáticas
│   ├── checklist_cumplimiento.py   # Genera checklist verificable
│   └── templates/              # Templates HTML
├── utils/                      # Utilidades compartidas
│   ├── config.py
│   ├── logger.py
│   └── base_datos.py
└── main.py                     # Orquestador principal
```

### Flujo de Trabajo

1. **Recepción de Reclamo**: El sistema recibe un reclamo en formato JSON
2. **Obtención de Boletas**: Se obtienen las boletas mediante web scraping o desde base de datos
3. **Clasificación**: Se clasifica el reclamo según su tipología
4. **Análisis**: Se analiza el reclamo aplicando el procedimiento específico
5. **Evaluación de Cumplimiento**: Se evalúa el cumplimiento normativo
6. **Generación de Expediente**: Se genera el expediente estructurado
7. **Generación de Informe Ejecutivo**: Se genera informe con explicación del análisis
8. **Generación de Instrucciones**: Se generan instrucciones automáticas para el funcionario
9. **Generación de Ficha Técnica**: Se genera ficha técnica completa en PDF/HTML
10. **Generación de Checklist**: Se genera checklist de cumplimiento verificable
11. **Almacenamiento**: Se guarda en base de datos y archivos

## 3. Instalación y Configuración

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Chrome/Chromium (para web scraping con Selenium)
- Acceso a internet (para web scraping)

### Instalación

1. **Clonar o descargar el proyecto**

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

3. **Instalar driver de Chrome para Selenium**:
```bash
# En Linux/Mac
sudo apt-get install chromium-chromedriver  # Ubuntu/Debian
brew install chromedriver  # macOS

# O descargar manualmente desde:
# https://chromedriver.chromium.org/
```

4. **Crear archivo de configuración** (opcional):
```bash
mkdir config
```

Crear `config/config.yaml`:
```yaml
base_datos:
  tipo: sqlite
  nombre: sec_reclamos.db

logging:
  nivel: INFO
  archivo: logs/sec_reclamos.log

scraping:
  timeout: 30
  max_reintentos: 3
  delay_entre_peticiones: 2
```

### Configuración de Variables de Entorno (Opcional)

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=sec_reclamos
export LOG_LEVEL=INFO
```

## 4. Guía de Uso por Módulo

### 4.1. Obtención de Boletas

#### Uso Básico

```python
from modulos.obtencion_boletas.scrapers.scraper_factory import ScraperFactory

factory = ScraperFactory()
scraper = factory.crear_scraper("enel")

# Login
scraper.login(usuario="12345678", password="contraseña")

# Obtener boletas
boletas = scraper.obtener_boletas(
    numero_cliente="12345678",
    periodo_inicio="2023-01",
    periodo_fin="2024-12"
)

# Cerrar conexión
scraper.cerrar()
```

#### Validación de Boletas

```python
from modulos.obtencion_boletas.procesamiento.validador_boletas import ValidadorBoletas

validador = ValidadorBoletas()
resultado = validador.validar(boleta)

if resultado['valida']:
    print("Boleta válida")
else:
    print(f"Errores: {resultado['errores']}")
```

### 4.2. Clasificación de Tipologías

```python
from modulos.consolidacion_juridico_tecnica.clasificador_tipologias import ClasificadorTipologias

clasificador = ClasificadorTipologias()

reclamo = {
    'descripcion': 'Mi factura está muy alta, el consumo es excesivo',
    'numero_cliente': '12345678',
    'distribuidora': 'Enel',
    'fecha_ingreso': '2024-01-15'
}

clasificacion = clasificador.clasificar(reclamo)
print(f"Tipología: {clasificacion['tipologia_principal']}")
print(f"Confianza: {clasificacion['confianza']:.2%}")
```

### 4.3. Análisis de Reclamos

```python
from modulos.consolidacion_juridico_tecnica.analizador_reclamos import AnalizadorReclamos

analizador = AnalizadorReclamos()

analisis = analizador.analizar(
    reclamo=reclamo,
    boletas=boletas,
    tipologia='facturacion_excesiva'
)

print(f"Procedimiento: {analisis['procedimiento_aplicado']}")
print(f"Supera 2x período espejo: {analisis['analisis_consumo']['supera_2x_periodo_espejo']}")
```

### 4.4. Evaluación de Cumplimiento

```python
from modulos.consolidacion_juridico_tecnica.evaluador_cumplimiento import EvaluadorCumplimiento

evaluador = EvaluadorCumplimiento()

cumplimiento = evaluador.evaluar(
    expediente=expediente,
    tipologia='facturacion_excesiva'
)

print(f"Cumplimiento general: {cumplimiento['cumplimiento_general']}")
print(f"Plazos cumplidos: {cumplimiento['cumplimiento_plazos']['cumple']}")
```

### 4.5. Generación de Expedientes

```python
from modulos.consolidacion_juridico_tecnica.generador_expediente import GeneradorExpediente

generador = GeneradorExpediente()

expediente = generador.generar(
    reclamo=reclamo,
    clasificacion=clasificacion,
    analisis=analisis,
    boletas=boletas,
    cumplimiento=cumplimiento
)

# Guardar en archivo
ruta = generador.guardar(expediente, formato='json')
print(f"Expediente guardado: {ruta}")
```

### 4.6. Generación de Ficha Técnica e Informes

El sistema ahora genera automáticamente:

1. **Ficha Técnica**: Documento completo en PDF/HTML con análisis detallado
2. **Informe Ejecutivo**: Resumen con explicación del análisis y justificación técnica
3. **Instrucciones**: Instrucciones automáticas para el funcionario
4. **Checklist de Cumplimiento**: Lista verificable punto por punto

#### Generación Automática

Estos documentos se generan automáticamente al procesar un reclamo:

```python
from modulos.main import SistemaAnalisisReclamos

sistema = SistemaAnalisisReclamos()
resultado = sistema.procesar_reclamo(reclamo)

# Los documentos están disponibles en resultado
print(f"Ficha técnica: {resultado['ficha_tecnica']}")
print(f"Checklist: {resultado['checklist']}")
print(f"Informe: {resultado['informe']}")
print(f"Instrucciones: {resultado['instrucciones']}")
```

#### Generación Manual

También puedes generar estos documentos manualmente:

```python
from modulos.ficha_tecnica_checklist.generador_ficha import GeneradorFicha
from modulos.ficha_tecnica_checklist.generador_informe import GeneradorInforme
from modulos.ficha_tecnica_checklist.generador_instrucciones import GeneradorInstrucciones
from modulos.ficha_tecnica_checklist.checklist_cumplimiento import ChecklistCumplimiento

# Generar ficha técnica
generador_ficha = GeneradorFicha()
ruta_ficha = generador_ficha.generar(expediente, analisis, cumplimiento, formato='pdf')

# Generar informe
generador_informe = GeneradorInforme()
informe = generador_informe.generar(expediente, analisis, cumplimiento)

# Generar instrucciones
generador_instrucciones = GeneradorInstrucciones()
instrucciones = generador_instrucciones.generar(expediente, analisis, cumplimiento)

# Generar checklist
checklist_gen = ChecklistCumplimiento()
ruta_checklist = checklist_gen.generar(expediente, cumplimiento, formato='pdf')
```

#### Formatos Disponibles

- **Ficha Técnica**: PDF, HTML
- **Checklist**: PDF, HTML, JSON
- **Informe**: Estructura JSON (puede formatearse a texto)
- **Instrucciones**: Estructura JSON (puede formatearse a texto)

## 5. Uso del Sistema Completo

### 5.1. Desde Línea de Comandos

**IMPORTANTE**: El script debe ejecutarse desde la raíz del proyecto usando `run.py`.

#### Procesar un Reclamo

```bash
python run.py --reclamo datos/reclamo_ejemplo.json
```

#### Con Credenciales para Scraping

```bash
python run.py \
  --reclamo datos/reclamo_ejemplo.json \
  --credenciales datos/credenciales.json
```

#### Sin Scraping (usar base de datos)

```bash
python run.py \
  --reclamo datos/reclamo_ejemplo.json \
  --sin-scraping
```

#### Especificar Formato de Salida

```bash
python run.py \
  --reclamo datos/reclamo_ejemplo.json \
  --formato txt \
  --salida resultados/expediente.txt
```

#### Especificar Formato de Ficha Técnica

```bash
python run.py \
  --reclamo datos/reclamo_ejemplo.json \
  --formato-ficha html
```

#### Sin Generar Ficha Técnica

```bash
python run.py \
  --reclamo datos/reclamo_ejemplo.json \
  --sin-ficha
```

#### Alternativa: Usar módulo directamente

Si prefieres usar el módulo directamente, puedes hacerlo así:

```bash
# Desde la raíz del proyecto
python -m modulos.main --reclamo datos/reclamo_ejemplo.json
```

### 5.2. Formato de Entrada (Reclamo JSON)

```json
{
  "numero_reclamo": "REC-2024-001",
  "numero_cliente": "12345678",
  "distribuidora": "enel",
  "fecha_ingreso": "2024-01-15",
  "titulo": "Facturación Excesiva",
  "descripcion": "Mi factura del mes de enero es muy alta comparada con meses anteriores. El consumo registrado es excesivo."
}
```

### 5.3. Formato de Credenciales (JSON)

```json
{
  "usuario": "12345678",
  "password": "contraseña_segura"
}
```

### 5.4. Uso Programático

```python
from modulos.main import SistemaAnalisisReclamos

sistema = SistemaAnalisisReclamos()

reclamo = {
    "numero_reclamo": "REC-2024-001",
    "numero_cliente": "12345678",
    "distribuidora": "enel",
    "fecha_ingreso": "2024-01-15",
    "titulo": "Facturación Excesiva",
    "descripcion": "Consumo excesivo en enero"
}

credenciales = {
    "usuario": "12345678",
    "password": "contraseña"
}

resultado = sistema.procesar_reclamo(
    reclamo,
    obtener_boletas=True,
    credenciales_scraping=credenciales
)

# Guardar expediente
ruta = sistema.guardar_expediente(resultado, formato='json')
print(f"Expediente: {ruta}")
```

## 6. Ejemplos Prácticos

### Ejemplo 1: Análisis de Facturación Excesiva

```python
from modulos.main import SistemaAnalisisReclamos

sistema = SistemaAnalisisReclamos()

reclamo = {
    "numero_reclamo": "REC-2024-001",
    "numero_cliente": "12345678",
    "distribuidora": "enel",
    "fecha_ingreso": "2024-01-15",
    "titulo": "Facturación Excesiva Enero 2024",
    "descripcion": "El consumo de enero 2024 es de 850 kWh, cuando normalmente consumo 300-400 kWh mensuales. Esto es más del doble de mi consumo habitual."
}

resultado = sistema.procesar_reclamo(reclamo, obtener_boletas=False)

# Ver resultados
print(f"Tipología: {resultado['clasificacion']['tipologia_principal']}")
print(f"Supera 2x período espejo: {resultado['analisis']['analisis_consumo']['supera_2x_periodo_espejo']}")
print(f"Recomendaciones: {resultado['analisis']['recomendaciones']}")
```

### Ejemplo 2: Validación de Boletas

```python
from modulos.obtencion_boletas.procesamiento.validador_boletas import ValidadorBoletas

validador = ValidadorBoletas()

boletas = [
    {
        "numero_cliente": "12345678",
        "distribuidora": "Enel",
        "periodo_facturacion": "2024-01",
        "lectura_actual": 1500.0,
        "lectura_anterior": 1200.0,
        "consumo_kwh": 300.0,
        "monto_total": 45000.0
    }
]

resultados = validador.validar_lote(boletas)
boletas_validas = validador.obtener_boletas_validas(boletas)
```

## 7. Troubleshooting

### Problemas Comunes

#### 1. Error al conectar con Chrome/Selenium

**Síntoma**: `WebDriverException` o error de conexión

**Solución**:
- Verificar que Chrome/Chromium esté instalado
- Verificar que chromedriver esté en PATH
- Actualizar chromedriver a versión compatible con Chrome

#### 2. Error en Login de Scraper

**Síntoma**: Login falla o timeout

**Solución**:
- Verificar credenciales
- Verificar que la estructura del sitio no haya cambiado
- Aumentar timeout en configuración
- Verificar si hay CAPTCHA (requiere intervención manual)

#### 3. No se encuentran boletas

**Síntoma**: Lista de boletas vacía

**Solución**:
- Verificar número de cliente
- Verificar período de búsqueda
- Revisar logs para errores específicos
- Verificar que el scraper esté actualizado para la distribuidora

#### 4. Error en clasificación de tipología

**Síntoma**: Tipología incorrecta o baja confianza

**Solución**:
- Revisar descripción del reclamo (debe ser clara)
- Verificar keywords en clasificador
- Ajustar reglas de clasificación si es necesario

#### 5. Error en análisis de consumo

**Síntoma**: No se puede comparar con período espejo

**Solución**:
- Verificar que haya boletas de al menos 12 meses anteriores
- Verificar formato de períodos en boletas
- Revisar que las boletas tengan consumo_kwh válido

### Logs y Debugging

El sistema genera logs en `logs/sec_reclamos.log` (configurable).

Para aumentar nivel de detalle:
```python
from modulos.utils.config import Config
from modulos.utils.logger import Logger

config = Config()
config.set('logging.nivel', 'DEBUG')
logger = Logger(config)
```

## 8. Referencias Normativas

### Documentos de Referencia

1. **Manual de Procedimiento de Resolución de Reclamos 2025**
   - Ubicación: `docs/manual_reclamos_2025.json`
   - Contiene procedimientos para cada tipología

2. **Resolución Exenta N° 1952 (2009)**
   - Ubicación: `docs/resolucion_exenta_1952.json`
   - Procedimiento para Consumos No Registrados (CNR)

3. **Norma Técnica de Calidad de Servicio para Sistemas de Distribución (NTCSD) 2024**
   - Referenciada en el manual
   - Establece estándares de calidad y continuidad

### Reglas de Negocio Clave

#### Facturación Excesiva
- Comparar consumo con 2x período espejo (año anterior)
- Descartar CNR, facturación provisoria, cobros indebidos
- Árbol de decisión: causas internas → error lectura → problema medidor

#### Facturación Provisoria
- Límite: 3x promedio mensual para 3+ meses consecutivos
- Requiere lecturas contiguas y fotografías como medios probatorios

#### CNR (Resolución 1952)
- CIM: promedio de 12 meses anteriores
- Período máximo: 12 meses (conexiones irregulares) o 3 meses (otros)
- Requiere medios de prueba específicos

#### Plazos
- 30 días para resolución en primera instancia
- Verificación de cumplimiento de plazos en evaluación

## 9. Extensión del Sistema

### Agregar Nueva Distribuidora

1. Crear nuevo scraper en `modulos/obtencion_boletas/scrapers/`:

```python
from ..scraper_base import ScraperBase

class NuevaDistribuidoraScraper(ScraperBase):
    def obtener_url_login(self) -> str:
        return "https://nueva-distribuidora.cl/login"
    
    def login(self, usuario: str, password: str) -> bool:
        # Implementar login
        pass
    
    def obtener_boletas(self, numero_cliente: str, ...):
        # Implementar extracción
        pass
```

2. Registrar en `scraper_factory.py`:

```python
from .nueva_distribuidora_scraper import NuevaDistribuidoraScraper

_scrapers_disponibles = {
    'enel': EnelScraper,
    'nueva_distribuidora': NuevaDistribuidoraScraper,
}
```

### Agregar Nueva Tipología

1. Agregar en `clasificador_tipologias.py`:

```python
TIPOLOGIAS = {
    # ... existentes
    'nueva_tipologia': {
        'codigo': 'Anexo N°X',
        'nombre': 'Nueva Tipología',
        'keywords': ['keyword1', 'keyword2']
    }
}
```

2. Implementar analizador en `analizador_reclamos.py`:

```python
def _analizar_nueva_tipologia(self, reclamo, boletas):
    # Implementar análisis
    pass
```

## 10. Mantenimiento y Actualizaciones

### Actualización de Scrapers

Los scrapers pueden requerir actualización si:
- La estructura HTML del sitio cambia
- Se implementan nuevas medidas anti-bot
- Cambian los métodos de autenticación

### Actualización de Reglas de Negocio

Si cambia la normativa:
1. Actualizar `docs/manual_reclamos_2025.json`
2. Actualizar reglas en `analizador_reclamos.py`
3. Actualizar medios probatorios en `evaluador_cumplimiento.py`

### Backup de Datos

La base de datos SQLite se encuentra en `data/sec_reclamos.db`. Realizar backups periódicos.

## 11. Contacto y Soporte

Para dudas o problemas:
- Revisar logs en `logs/sec_reclamos.log`
- Consultar documentación en `docs/`
- Revisar código fuente y comentarios

---

**Versión del Manual**: 1.0  
**Fecha de Actualización**: 2025-01  
**Sistema**: Análisis de Reclamos SEC

