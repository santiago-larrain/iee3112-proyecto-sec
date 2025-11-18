# Plan de Pruebas y Validación del Sistema

## Fase 1: Pruebas Básicas de Funcionalidad

### 1.1. Prueba de Clasificación de Tipologías

**Objetivo**: Verificar que el clasificador identifica correctamente las tipologías.

```bash
# Crear archivos de prueba para cada tipología
python run.py --reclamo datos/test_facturacion_excesiva.json --sin-scraping
python run.py --reclamo datos/test_facturacion_provisoria.json --sin-scraping
python run.py --reclamo datos/test_cobros_indebidos.json --sin-scraping
```

**Verificar**:
- [ ] Clasificación correcta de tipología principal
- [ ] Confianza > 0.5 para casos claros
- [ ] Tipologías secundarias identificadas cuando aplica

### 1.2. Prueba de Análisis sin Boletas

**Objetivo**: Verificar que el sistema funciona sin boletas (modo básico).

```bash
python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping
```

**Verificar**:
- [ ] No hay errores de NoneType
- [ ] Se genera expediente correctamente
- [ ] El análisis indica que no hay boletas para comparar
- [ ] El expediente se guarda en formato JSON

### 1.3. Prueba de Análisis con Boletas Mock

**Objetivo**: Verificar análisis con datos simulados.

**Pasos**:
1. Crear boletas de prueba en base de datos
2. Ejecutar análisis
3. Verificar resultados

**Verificar**:
- [ ] Comparación con período espejo funciona
- [ ] Detección de facturación provisoria
- [ ] Cálculo de consumo excesivo (2x período espejo)
- [ ] Recomendaciones generadas correctamente

### 1.4. Prueba de Generación de Expedientes

**Objetivo**: Verificar formatos de salida.

```bash
python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping --formato json
python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping --formato txt
```

**Verificar**:
- [ ] Expediente JSON válido y completo
- [ ] Expediente TXT legible y bien formateado
- [ ] Todos los campos requeridos presentes
- [ ] Medios probatorios listados correctamente

## Fase 2: Pruebas de Integración

### 2.1. Prueba de Flujo Completo

**Objetivo**: Verificar que todo el flujo funciona end-to-end.

**Pasos**:
1. Reclamo → Clasificación → Análisis → Expediente → Cumplimiento
2. Verificar que cada paso genera datos correctos
3. Verificar que no hay pérdida de información entre pasos

### 2.2. Prueba de Base de Datos

**Objetivo**: Verificar persistencia de datos.

```python
# Script de prueba
from modulos.utils.base_datos import BaseDatos
from modulos.utils.config import Config

config = Config()
db = BaseDatos(config)

# Probar guardar y recuperar
reclamo_id = db.guardar_reclamo({...})
reclamo = db.obtener_reclamo("REC-2024-001")
boletas = db.obtener_boletas_cliente("12345678")
```

**Verificar**:
- [ ] Reclamos se guardan correctamente
- [ ] Boletas se guardan y recuperan
- [ ] Expedientes se asocian correctamente
- [ ] Consultas funcionan sin errores

## Fase 3: Pruebas de Scraping (Cuando esté configurado)

### 3.1. Prueba de Login

**Objetivo**: Verificar que el scraper puede autenticarse.

**Pasos**:
1. Configurar credenciales de prueba
2. Intentar login
3. Verificar sesión activa

**Verificar**:
- [ ] Login exitoso
- [ ] Manejo de errores de credenciales
- [ ] Detección de CAPTCHA (si aplica)

### 3.2. Prueba de Extracción de Boletas

**Objetivo**: Verificar extracción de datos.

**Pasos**:
1. Obtener boletas de un período específico
2. Verificar datos extraídos
3. Validar formato y completitud

**Verificar**:
- [ ] Boletas se extraen correctamente
- [ ] Datos están completos (lecturas, consumos, montos)
- [ ] Validación detecta errores
- [ ] Datos se normalizan correctamente

## Fase 4: Pruebas de Casos Especiales

### 4.1. Casos Edge

- [ ] Reclamo sin descripción
- [ ] Reclamo con múltiples tipologías
- [ ] Boletas con datos faltantes
- [ ] Períodos sin boletas espejo
- [ ] Consumos cero o negativos

### 4.2. Manejo de Errores

- [ ] Error de conexión en scraping
- [ ] Archivo de reclamo mal formateado
- [ ] Base de datos no disponible
- [ ] Timeout en operaciones

## Fase 5: Validación con Datos Reales

### 5.1. Pruebas con Reclamos Reales (Anonimizados)

**Objetivo**: Validar con casos reales de la SEC.

**Pasos**:
1. Obtener reclamos reales (anonimizados)
2. Procesar con el sistema
3. Comparar resultados con análisis manual
4. Ajustar según discrepancias

## Checklist de Validación

### Funcionalidad Core
- [ ] Clasificación de tipologías funciona
- [ ] Análisis de facturación excesiva funciona
- [ ] Análisis de facturación provisoria funciona
- [ ] Generación de expedientes funciona
- [ ] Evaluación de cumplimiento funciona

### Integración
- [ ] Flujo completo sin errores
- [ ] Base de datos funciona
- [ ] Logging funciona correctamente
- [ ] Manejo de errores robusto

### Calidad
- [ ] Código sin errores de linting
- [ ] Documentación completa
- [ ] Ejemplos funcionan
- [ ] Performance aceptable

