# Inicio Rápido - Próximos Pasos

## 🚀 Comenzar Ahora (5 minutos)

### 1. Probar el Sistema Básico

```bash
# Activar ambiente conda
conda activate sec

# Crear datos de prueba
python scripts/crear_datos_prueba.py

# Ejecutar suite de pruebas
python scripts/probar_sistema.py

# Probar con un reclamo
python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping
```

### 2. Revisar Resultados

- Verificar que no hay errores
- Revisar expedientes generados en `data/expedientes/`
- Verificar logs en `logs/sec_reclamos.log`

## 📋 Checklist de Configuración con SEC

### Información Crítica a Obtener

#### 🔐 Accesos y Credenciales
- [ ] **Credenciales de prueba para portales de distribuidoras**
  - Enel: usuario/password o método de autenticación
  - CGE: credenciales de acceso
  - Otras distribuidoras prioritarias
  
- [ ] **Acceso a PESEC** (si aplica)
  - ¿Existe API? ¿URLs? ¿Credenciales?
  - Documentación de endpoints
  - Rate limiting y cuotas

#### 📊 URLs y Estructura
- [ ] **URLs actuales de portales**
  - URL de login de cada distribuidora
  - URL de sección de boletas
  - Cambios recientes en estructura
  
- [ ] **Estructura de datos**
  - Formato exacto de boletas por distribuidora
  - Campos obligatorios vs opcionales
  - Formatos de fecha, monto, etc.

#### 📖 Validación Normativa
- [ ] **Reglas de negocio**
  - Confirmar: ¿30 días hábiles o corridos?
  - Validar cálculo de período espejo
  - Confirmar umbral de 2x período espejo
  - Validar límite de 3x promedio para provisoria
  
- [ ] **Medios probatorios**
  - Lista completa por tipología
  - Formatos aceptados
  - Requisitos de calidad

#### 🧪 Datos de Prueba
- [ ] **Reclamos reales anonimizados**
  - Mínimo 10 por tipología
  - Con resultados esperados para validación
  
- [ ] **Boletas reales anonimizadas**
  - Últimos 24 meses
  - Diferentes distribuidoras

## 🔧 Tareas Técnicas Inmediatas

### Prioridad ALTA (Esta Semana)

1. **Actualizar Scraper de Enel**
   - [ ] Obtener credenciales de prueba
   - [ ] Analizar estructura HTML actual del portal
   - [ ] Actualizar selectores CSS/XPath en `enel_scraper.py`
   - [ ] Probar login y extracción
   - [ ] Validar datos extraídos

2. **Validar Reglas de Negocio**
   - [ ] Reunión con SEC para clarificar dudas
   - [ ] Documentar decisiones
   - [ ] Ajustar código según validación

3. **Crear Casos de Prueba**
   - [ ] Ejecutar `scripts/crear_datos_prueba.py`
   - [ ] Crear casos específicos por tipología
   - [ ] Validar resultados esperados

### Prioridad MEDIA (Próximas 2 Semanas)

4. **Implementar Más Scrapers**
   - [ ] Identificar distribuidoras prioritarias
   - [ ] Crear scrapers para CGE, Saesa, etc.
   - [ ] Probar y validar cada uno

5. **Mejorar Análisis**
   - [ ] Ajustar según feedback SEC
   - [ ] Implementar casos especiales
   - [ ] Mejorar detección de patrones

6. **Integración con PESEC**
   - [ ] Investigar API disponible
   - [ ] Implementar cliente si existe
   - [ ] Probar sincronización

## 🧪 Cómo Probar el Sistema

### Prueba 1: Funcionalidad Básica

```bash
# Crear datos de prueba
python scripts/crear_datos_prueba.py

# Probar clasificación
python run.py --reclamo datos/reclamo_ejemplo.json --sin-scraping
```

**Verificar**:
- ✓ No hay errores
- ✓ Expediente se genera
- ✓ Tipología clasificada correctamente

### Prueba 2: Suite Completa

```bash
# Ejecutar todas las pruebas
python scripts/probar_sistema.py
```

**Verificar**:
- ✓ Todas las pruebas pasan
- ✓ Sin errores críticos
- ✓ Funcionalidad core operativa

### Prueba 3: Con Scraping Real

```bash
# Cuando tengas credenciales configuradas
python run.py --reclamo datos/reclamo_ejemplo.json \
  --credenciales datos/credenciales.json
```

**Verificar**:
- ✓ Login exitoso
- ✓ Boletas extraídas correctamente
- ✓ Datos validados y normalizados

## 📝 Documentos de Referencia

1. **`docs/CHECKLIST_PERSONALIZACION.md`** - Lista completa de cosas a configurar
2. **`docs/PROXIMOS_PASOS.md`** - Plan detallado de implementación
3. **`docs/GUIA_IMPLEMENTACION.md`** - Guía semana a semana
4. **`docs/PLAN_PRUEBAS.md`** - Plan de pruebas estructurado

## 🎯 Objetivo Inmediato

**Esta Semana**: Tener el sistema funcionando con:
- ✓ Clasificación validada
- ✓ Análisis funcionando correctamente
- ✓ Expedientes generándose sin errores
- ✓ Al menos un scraper funcional (Enel)

**Próximas 2 Semanas**: 
- ✓ Validación con SEC completada
- ✓ Scrapers para distribuidoras prioritarias
- ✓ Datos de prueba reales procesados
- ✓ Sistema listo para pruebas con usuarios

## 💡 Tips

1. **Empieza simple**: Primero valida que todo funciona sin scraping
2. **Itera rápido**: Prueba, ajusta, prueba de nuevo
3. **Documenta decisiones**: Cada ajuste debe quedar documentado
4. **Mantén comunicación con SEC**: Valida constantemente
5. **Prueba con casos reales**: Los datos reales revelan problemas que los mock no

## 🆘 Si Algo Falla

1. Revisar logs: `logs/sec_reclamos.log`
2. Ejecutar pruebas: `python scripts/probar_sistema.py`
3. Verificar configuración: `config/config.yaml`
4. Consultar documentación: `docs/manual_uso.md`
5. Revisar troubleshooting: `docs/manual_uso.md` sección 7

