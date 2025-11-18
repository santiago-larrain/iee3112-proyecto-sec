# Siguientes Pasos - Sistema de Análisis de Reclamos SEC

Este documento lista los pasos pendientes, información faltante, templates pendientes y prioridades para completar el sistema.

## Estado Actual

✅ **Completado**:
- Estructura base del sistema
- Obtención de boletas (estructura)
- Clasificación de tipologías
- Análisis de reclamos (facturación excesiva implementado)
- Generación de expedientes
- Evaluación de cumplimiento (con mejoras)
- **Ficha técnica completa con PDF/HTML**
- **Generación de instrucciones automáticas**
- **Generación de informe ejecutivo**
- **Checklist de cumplimiento**

## Información Faltante que Requiere Consulta con SEC

### 1. URLs y Credenciales de Portales

**Prioridad: ALTA**

- [ ] URLs actualizadas de portales de distribuidoras:
  - [ ] Enel Distribución
  - [ ] CGE (Chilectra)
  - [ ] Saesa
  - [ ] Otras distribuidoras a implementar

- [ ] Estructura de autenticación de cada portal:
  - [ ] Método de login (usuario/password, RUT, etc.)
  - [ ] Selectores CSS/XPath actualizados
  - [ ] Detección y resolución de CAPTCHA
  - [ ] Políticas anti-bot y rate limiting

**Archivo**: `config/config.yaml` (sección `scraping`)

### 2. Integración con PESEC

**Prioridad: MEDIA-ALTA**

- [ ] ¿Existe API disponible para PESEC?
- [ ] Documentación de API
- [ ] Credenciales de acceso
- [ ] Endpoints disponibles:
  - [ ] Obtener reclamos
  - [ ] Enviar expedientes
  - [ ] Consultar estado
- [ ] Rate limiting y cuotas
- [ ] Formato de datos esperado

**Archivos a crear**:
- `modulos/integracion/pesec_client.py`
- `modulos/integracion/sincronizador.py`

### 3. Validación de Reglas de Negocio

**Prioridad: ALTA**

#### Facturación Excesiva
- [ ] Confirmar umbral de 2x período espejo
- [ ] Validar cálculo de período espejo (mes anterior, mismo mes, mes posterior)
- [ ] Confirmar límite máximo según potencia
- [ ] Validar árbol de decisión completo

#### Facturación Provisoria
- [ ] Confirmar límite de 3x promedio mensual
- [ ] Validar detección de "lecturas inventadas"
- [ ] Confirmar requisitos de fotografías
- [ ] Validar cálculo de cuotas

#### CNR (Consumos No Registrados)
- [ ] Validar cálculo de CIM con diferentes escenarios
- [ ] Confirmar reglas de períodos máximos (12 meses vs 3 meses)
- [ ] Validar medios de prueba específicos
- [ ] Confirmar casos especiales (ocupación < 3 meses)

#### Cobros Indebidos
- [ ] Validar procedimiento de análisis
- [ ] Confirmar medios probatorios requeridos
- [ ] Validar cálculo de reembolsos

**Archivo**: `docs/manual_reclamos_2025.json` (ya existe, requiere validación)

### 4. Medios Probatorios Requeridos

**Prioridad: MEDIA**

- [ ] Lista completa y actualizada por tipología
- [ ] Formatos aceptados (PDF, imágenes, etc.)
- [ ] Requisitos de calidad/resolución
- [ ] Validación de medios probatorios

**Archivo**: `modulos/consolidacion_juridico_tecnica/evaluador_cumplimiento.py` (actualizar método `_obtener_medios_requeridos`)

### 5. Plazos y Cumplimiento

**Prioridad: MEDIA**

- [ ] Validar criterios de cumplimiento
- [ ] Confirmar cómo se calculan días transcurridos (hábiles vs calendario)
- [ ] Validar excepciones a plazos
- [ ] Confirmar plazos específicos por tipología

**Archivo**: `modulos/consolidacion_juridico_tecnica/evaluador_cumplimiento.py` (constante `PLAZO_RESOLUCION_DIAS`)

## Implementaciones Pendientes

### 1. Scrapers Adicionales

**Prioridad: MEDIA**

- [ ] Scraper para CGE (Chilectra)
- [ ] Scraper para Saesa
- [ ] Scraper para otras distribuidoras según prioridad

**Archivos**: `modulos/obtencion_boletas/scrapers/`

### 2. Análisis de Otras Tipologías

**Prioridad: ALTA**

- [ ] Implementar análisis completo para:
  - [ ] Facturación Provisoria (Anexo N°2)
  - [ ] CNR (Resolución 1952)
  - [ ] Cobros Indebidos (Anexo N°3)
  - [ ] Error de Lectura (Anexo N°1.1)
  - [ ] Calidad de Suministro (Anexo N°5)
  - [ ] No Cumplimiento de Instrucción (Anexo N°6)

**Archivo**: `modulos/consolidacion_juridico_tecnica/analizador_reclamos.py`

### 3. Mejoras de Análisis

**Prioridad: MEDIA**

- [ ] Detección de patrones anómalos
- [ ] Análisis estadístico de tendencias
- [ ] Validación cruzada con datos históricos
- [ ] Comparación con sistemas internos

**Archivos**: Nuevos módulos en `modulos/consolidacion_juridico_tecnica/`

### 4. Automatización y Scheduler

**Prioridad: BAJA**

- [ ] Implementar scheduler para procesamiento automático
- [ ] Scraping periódico de boletas
- [ ] Procesamiento batch de reclamos
- [ ] Notificaciones de nuevos reclamos

**Archivos**:
- `modulos/scheduler/tareas.py`
- `scripts/procesar_reclamos_batch.py`

### 5. Testing Exhaustivo

**Prioridad: ALTA**

- [ ] Tests unitarios para cada módulo
- [ ] Tests de integración
- [ ] Tests end-to-end
- [ ] Tests con datos reales (anónimos)
- [ ] Validación con funcionarios SEC

**Archivos**: `tests/`

## Templates Pendientes

### 1. Templates de Documentos

**Prioridad: MEDIA**

- [x] Template HTML para ficha técnica (completado)
- [x] Template HTML para checklist (completado)
- [ ] Template para carta respuesta (si aplica)
- [ ] Template para resolución de reclamo

**Archivos**: `modulos/ficha_tecnica_checklist/templates/`

### 2. Configuración

**Prioridad: MEDIA**

- [ ] Template de configuración completo con ejemplos
- [ ] Documentación de todas las opciones de configuración
- [ ] Ejemplos de configuración por ambiente (desarrollo, producción)

**Archivo**: `config/config.yaml.example` (mejorar)

## Documentación Pendiente

### 1. Guía para Funcionarios SEC

**Prioridad: ALTA**

- [ ] Crear guía específica para funcionarios
- [ ] Explicar cómo leer la ficha técnica
- [ ] Explicar cómo interpretar el checklist
- [ ] Ejemplos prácticos de uso

**Archivo**: `docs/GUIA_FUNCIONARIOS.md`

### 2. Manual de Uso Actualizado

**Prioridad: MEDIA**

- [x] Actualizar con nueva funcionalidad de ficha técnica (pendiente completar)
- [ ] Agregar ejemplos de uso de ficha técnica
- [ ] Documentar formatos de salida
- [ ] Troubleshooting específico

**Archivo**: `docs/manual_uso.md`

### 3. Documentación Técnica

**Prioridad: BAJA**

- [ ] Diagramas de arquitectura actualizados
- [ ] Documentación de API (si se expone)
- [ ] Guía de desarrollo para nuevos módulos

## Prioridades de Implementación

### Fase 1: Validación y Configuración (1-2 semanas)
1. Consultar con SEC sobre reglas de negocio
2. Obtener URLs y credenciales de portales
3. Validar medios probatorios requeridos
4. Configurar sistema con información real

### Fase 2: Completar Análisis (2-3 semanas)
1. Implementar análisis de tipologías faltantes
2. Mejorar análisis de facturación excesiva
3. Implementar análisis de CNR completo
4. Testing exhaustivo de análisis

### Fase 3: Integración (2-3 semanas)
1. Integración con PESEC (si aplica)
2. Completar scrapers de distribuidoras
3. Automatización del flujo
4. Testing de integración

### Fase 4: Optimización y Producción (1-2 semanas)
1. Optimización de performance
2. Mejoras de UI/UX de documentos
3. Documentación final
4. Preparación para producción

## Notas Importantes

- **No implementar sin validación**: Las reglas de negocio deben ser validadas con SEC antes de implementar
- **Modularidad**: Mantener código modular para facilitar cambios
- **Documentación**: Documentar todos los cambios y decisiones
- **Testing**: Probar exhaustivamente antes de usar en producción
- **Seguridad**: No commitear credenciales ni información sensible

## Contactos y Recursos

- **Manual SEC**: `docs/manual_reclamos_2025.json`
- **Resolución CNR**: `docs/resolucion_exenta_1952.json`
- **Checklist de Personalización**: `docs/CHECKLIST_PERSONALIZACION.md`
- **Plan de Pruebas**: `docs/PLAN_PRUEBAS.md`

