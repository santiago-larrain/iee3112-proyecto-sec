# Guía para Funcionarios SEC - Sistema de Análisis de Reclamos

Esta guía está dirigida a funcionarios de la SEC que utilizarán el sistema para analizar reclamos.

## Introducción

El Sistema de Análisis de Reclamos SEC automatiza el proceso de análisis de reclamos, generando automáticamente:

- **Ficha Técnica**: Documento completo con análisis detallado
- **Checklist de Cumplimiento**: Lista verificable de requisitos
- **Instrucciones**: Guía de acciones a seguir
- **Informe Ejecutivo**: Resumen para toma de decisiones

## Uso Básico

### 1. Procesar un Reclamo

```bash
python run.py --reclamo datos/reclamo_ejemplo.json
```

El sistema procesará el reclamo y generará automáticamente todos los documentos necesarios.

### 2. Ubicación de Documentos Generados

Los documentos se guardan en la carpeta `data/expedientes/` con los siguientes nombres:

- `FICHA-{NUMERO_RECLAMO}-{FECHA}.pdf` - Ficha técnica
- `CHECKLIST-{NUMERO_RECLAMO}-{FECHA}.pdf` - Checklist de cumplimiento
- `EXP-{NUMERO_RECLAMO}-{FECHA}.json` - Expediente completo

## Cómo Leer la Ficha Técnica

### Estructura de la Ficha Técnica

La ficha técnica contiene las siguientes secciones:

#### 1. Resumen Ejecutivo

- **Número de Reclamo**: Identificador único del reclamo
- **Cliente**: Número de cliente
- **Distribuidora**: Empresa distribuidora
- **Tipología**: Tipo de reclamo identificado
- **Conclusión Principal**: Resumen del análisis
- **Estado de Cumplimiento**: Si cumple o no con los requisitos

#### 2. Análisis Técnico Detallado

- **Procedimiento Aplicado**: Qué procedimiento del manual SEC se aplicó
- **Análisis de Consumo**: Comparación con períodos anteriores
- **Causa Raíz**: Determinación de la causa del problema
- **Pasos Sugeridos**: Acciones recomendadas

#### 3. Evaluación de Cumplimiento

- **Cumplimiento General**: Estado general (Sí/No)
- **Plazos**: Si se cumplieron los plazos establecidos
- **Medios Probatorios**: Si están completos los medios requeridos
- **Consistencia**: Si la información es consistente
- **Incumplimientos**: Lista de incumplimientos detectados

#### 4. Instrucciones para Funcionario

- **Acciones Inmediatas**: Qué hacer primero (prioridad alta/media/normal)
- **Medios Probatorios a Solicitar**: Qué documentos faltan
- **Pasos Siguientes**: Secuencia de acciones recomendadas
- **Recomendaciones**: Sugerencias específicas

#### 5. Recomendaciones y Conclusiones

- **Recomendaciones**: Acciones sugeridas con prioridad
- **Conclusión Principal**: Resumen final
- **Siguiente Paso**: Qué hacer a continuación

## Cómo Leer el Checklist de Cumplimiento

### Estructura del Checklist

El checklist verifica punto por punto el cumplimiento normativo:

#### Items de Verificación

1. **Plazos**: Cumplimiento de plazo de resolución (30 días)
2. **Medios Probatorios**: Si están completos según tipología
3. **Consistencia de Información**: Si los datos son consistentes
4. **Respuesta de Primera Instancia**: Si la respuesta es completa
5. **Cumplimiento General**: Estado general

#### Interpretación

- **✓ CUMPLE**: El item cumple con el requisito
- **✗ NO CUMPLE**: El item no cumple, ver observaciones

#### Resumen

Al final del checklist encontrarás:
- **Items que cumplen**: X/Y items
- **Porcentaje de cumplimiento**: X%
- **Cumplimiento General**: SÍ/NO

## Cómo Usar las Instrucciones

Las instrucciones se generan automáticamente y te indican:

### Acciones Inmediatas

Cada acción tiene una prioridad:
- **[ALTA]**: Requiere atención urgente
- **[MEDIA]**: Requiere atención en breve
- **[NORMAL]**: Puede atenderse en el flujo normal

### Medios Probatorios a Solicitar

Lista de documentos que faltan, con:
- **Prioridad**: Alta o media
- **Justificación**: Por qué se requiere
- **Plazo Sugerido**: Cuándo solicitarlo

### Pasos Siguientes

Secuencia ordenada de acciones a realizar según la tipología del reclamo.

## Interpretación de Resultados

### Cumplimiento General: SÍ

- El expediente cumple con todos los requisitos normativos
- Puedes proceder con la resolución del reclamo
- Revisa las recomendaciones para acciones adicionales

### Cumplimiento General: NO

- Se detectaron incumplimientos que deben resolverse
- Revisa la lista de incumplimientos
- Solicita información faltante antes de continuar
- Sigue las instrucciones generadas

### Análisis de Consumo Excesivo

Si el análisis detecta consumo excesivo (supera 2x período espejo):
- Se requiere verificación del medidor
- Solicitar lectura al cliente
- Indagar por cambios en hábitos de consumo
- Ofrecer verificación sin costo

## Casos Especiales

### Análisis Automático

Si el sistema indica "Este es un análisis automático":
- No hay respuesta de empresa disponible aún
- El sistema analizó solo con la información del reclamo
- La evaluación de respuesta de empresa no aplica
- Debes esperar la respuesta de la distribuidora

### Baja Confianza en Clasificación

Si la confianza de clasificación es menor a 50%:
- Revisar manualmente la clasificación
- El sistema no está seguro de la tipología
- Puede requerir ajuste manual

### Medios Probatorios Faltantes

Si faltan medios probatorios:
- Contactar a la distribuidora para solicitarlos
- Usar los plazos sugeridos en las instrucciones
- No proceder con resolución hasta tener medios completos

## Recomendaciones de Uso

1. **Siempre revisar la Ficha Técnica completa** antes de tomar decisiones
2. **Usar el Checklist** para verificar cumplimiento punto por punto
3. **Seguir las Instrucciones** generadas, especialmente acciones inmediatas
4. **Validar manualmente** si la confianza de clasificación es baja
5. **Solicitar medios faltantes** antes de emitir resolución
6. **Documentar** cualquier decisión o ajuste manual realizado

## Preguntas Frecuentes

### ¿Puedo modificar manualmente los documentos generados?

Sí, pero se recomienda documentar los cambios. Los documentos se regeneran cada vez que procesas el reclamo.

### ¿Qué hago si el sistema clasifica incorrectamente?

Puedes ajustar manualmente la tipología y reprocesar, o contactar al equipo técnico.

### ¿Cómo interpreto los gráficos de consumo?

Los gráficos muestran el historial de consumo. Si hay un pico anormal, el sistema lo detectará automáticamente.

### ¿El sistema reemplaza mi criterio profesional?

No. El sistema es una herramienta de apoyo. Tu criterio profesional es fundamental para la toma de decisiones finales.

## Soporte

Para dudas o problemas:
1. Revisar esta guía
2. Consultar el manual técnico (`docs/manual_uso.md`)
3. Contactar al equipo técnico del proyecto

## Glosario

- **Período Espejo**: Mismo mes del año anterior, usado para comparar consumo
- **CIM**: Consumo Índice Mensual (para casos CNR)
- **CNR**: Consumos No Registrados
- **Medios Probatorios**: Documentos requeridos según tipología
- **Tipología**: Tipo de reclamo según clasificación SEC

