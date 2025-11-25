# Capítulo 12: AI ChatBot (Proyección)

[← Anterior: Futuras Analíticas](11_Futuras_analiticas.md) | [Siguiente: Cierre →](13_Cierre.md)

## 12.1. Visión General

Este capítulo describe conceptualmente cómo un asistente de inteligencia artificial conversacional (ChatBot) podría integrarse al sistema para permitir consultas naturales sobre los datos estructurados, acelerar la resolución de casos y proporcionar asistencia contextual al funcionario.

## 12.2. Arquitectura Conceptual

### 12.2.1. Componentes del Sistema

```
┌─────────────────────────────────────────┐
│         Interfaz de Chat (Frontend)      │
│         Panel lateral con mensajes       │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      API de Chat (Backend)               │
│      Endpoint: POST /api/chat            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│    Motor RAG (Retrieval-Augmented        │
│         Generation)                      │
│  ┌──────────────────────────────────┐   │
│  │ 1. Procesa pregunta natural      │   │
│  │ 2. Busca en base de datos        │   │
│  │ 3. Recupera contexto relevante    │   │
│  │ 4. Genera respuesta con LLM       │   │
│  └──────────────────────────────────┘   │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  BBDD    │ │  EDNs    │ │  Docs    │
│ Relacional│ │  JSON    │ │  Texto   │
└──────────┘ └──────────┘ └──────────┘
```

### 12.2.2. Tecnología RAG

**Retrieval-Augmented Generation (RAG)** combina:
- **Retrieval**: Búsqueda en base de datos estructurada
- **Augmentation**: Enriquecimiento con contexto relevante
- **Generation**: Generación de respuesta natural usando LLM

**Ventajas:**
- Respuestas basadas en datos reales del sistema
- No requiere entrenamiento del modelo
- Actualizable con nuevos datos
- Transparente (puede citar fuentes)

## 12.3. Capacidades del ChatBot

### 12.3.1. Consultas sobre Casos

**Ejemplos de Preguntas:**
- "¿Cuántos casos de CNR tiene la comuna de Maipú?"
- "¿Qué casos están pendientes de la empresa ENEL?"
- "Muéstrame los casos similares a este"
- "¿Cuál es el tiempo promedio de resolución este mes?"

**Procesamiento:**
1. Parsear pregunta natural
2. Identificar entidades (comuna, empresa, tipo de caso)
3. Construir query a base de datos
4. Ejecutar query y obtener resultados
5. Formatear respuesta natural

### 12.3.2. Análisis de Caso Actual

**Ejemplos de Preguntas:**
- "¿Qué irregularidades tiene este caso?"
- "¿Por qué el item B.2 está marcado como NO_CUMPLE?"
- "¿Qué documentos faltan para este caso?"
- "¿Cómo se resolvieron casos similares?"

**Procesamiento:**
1. Identificar caso actual (contexto de sesión)
2. Cargar EDN del caso
3. Analizar checklist y documentos
4. Buscar casos similares en historial
5. Generar respuesta contextual

### 12.3.3. Asistencia en Resolución

**Ejemplos de Preguntas:**
- "¿Qué argumentos legales puedo usar para este caso?"
- "¿Cuál es la normativa aplicable para CNR?"
- "¿Qué debe incluir la resolución de instrucción?"

**Procesamiento:**
1. Identificar tipo de caso y estado del checklist
2. Cargar snippets de argumentos relevantes
3. Consultar base de conocimiento normativa
4. Generar respuesta con referencias legales

### 12.3.4. Consultas Analíticas

**Ejemplos de Preguntas:**
- "¿Qué empresas tienen más reclamos este año?"
- "¿Hay tendencias en los casos de CNR?"
- "¿Qué comunas tienen más problemas?"

**Procesamiento:**
1. Parsear consulta analítica
2. Ejecutar análisis sobre base de datos
3. Generar visualización o resumen
4. Presentar resultados en formato natural

## 12.4. Integración con Base de Datos

### 12.4.1. Acceso a Datos Estructurados

**Fuentes de Datos:**
- `personas.json`, `suministros.json`, `casos.json`: Metadatos relacionales
- `edn.json`: Expedientes completos con contexto
- `documentos.json`: Índice de documentos con extracted_data
- Texto completo de documentos: Para búsqueda semántica

### 12.4.2. Vectorización de Documentos

**Proceso:**
1. Extraer texto de documentos procesados
2. Dividir en chunks (fragmentos)
3. Generar embeddings vectoriales
4. Almacenar en base de datos vectorial

**Búsqueda Semántica:**
- Pregunta del usuario se convierte en embedding
- Búsqueda de chunks similares en espacio vectorial
- Recuperación de contexto relevante

### 12.4.3. Query a Base de Datos Relacional

**Ejemplos de Queries Generadas:**
```python
# Pregunta: "¿Cuántos casos CNR tiene ENEL?"
query = """
SELECT COUNT(*) 
FROM casos c
JOIN edn e ON c.case_id = e.case_id
WHERE c.empresa = 'ENEL' 
  AND e.compilation_metadata->>'tipo_caso' = 'CNR'
"""
```

## 12.5. Procesamiento de Lenguaje Natural

### 12.5.1. Entendimiento de Intención

**Intenciones Identificadas:**
- `CONSULTA_CASO`: Preguntas sobre un caso específico
- `CONSULTA_ANALITICA`: Preguntas sobre estadísticas
- `ASISTENCIA_RESOLUCION`: Ayuda con generación de resolución
- `BUSQUEDA_SIMILARES`: Encontrar casos similares

### 12.5.2. Extracción de Entidades

**Entidades Reconocidas:**
- Empresas: "ENEL", "Grupo Saesa"
- Comunas: "Maipú", "Santiago"
- Tipos de caso: "CNR", "Corte de Suministro"
- Fechas: "este mes", "último año"
- IDs de caso: "231220-000557"

### 12.5.3. Generación de Respuesta

**Proceso:**
1. Recuperar contexto relevante (datos + documentos)
2. Construir prompt para LLM con contexto
3. Generar respuesta natural
4. Incluir citas a fuentes (casos, documentos)
5. Formatear respuesta para presentación

## 12.6. Interfaz de Usuario

### 12.6.1. Panel de Chat

**Componente Actual:** `AIChatPanel.vue`

**Características Actuales:**
- Panel lateral derecho plegable
- Chat con mensajes del usuario y respuestas de IA
- Respuestas simuladas basadas en palabras clave
- Diseño responsive

**Mejoras Futuras:**
- Integración con motor RAG real
- Respuestas basadas en datos del sistema
- Citas a fuentes (casos, documentos)
- Visualizaciones inline (gráficos, tablas)

### 12.6.2. Experiencia de Usuario

**Flujo de Conversación:**
1. Usuario escribe pregunta en lenguaje natural
2. Sistema muestra indicador de "pensando"
3. Sistema procesa pregunta y genera respuesta
4. Respuesta se muestra con formato legible
5. Opción de hacer seguimiento o nueva pregunta

**Características:**
- Historial de conversación por sesión
- Contexto mantenido durante la conversación
- Sugerencias de preguntas frecuentes
- Enlaces a casos/documentos mencionados

## 12.7. Casos de Uso Específicos

### 12.7.1. Asistencia en Revisión de Caso

**Escenario:**
Funcionario está revisando un caso CNR y tiene dudas.

**Interacción:**
```
Usuario: "¿Por qué este caso está marcado como NO_CUMPLE en el item B.2?"

IA: "El item B.2 (Existencia de Evidencia Fotográfica) está marcado como 
NO_CUMPLE porque no se encontraron documentos de tipo EVIDENCIA_FOTOGRAFICA 
en el inventario documental. Según la regla RULE_CHECK_PHOTOS_EXISTENCE, 
se requiere al menos una imagen para acreditar el estado del medidor. 
Puedes revisar los documentos en la Sección B del caso."
```

### 12.7.2. Búsqueda de Casos Similares

**Escenario:**
Funcionario quiere ver cómo se resolvieron casos similares.

**Interacción:**
```
Usuario: "Muéstrame casos CNR similares a este en la comuna de Maipú"

IA: "Encontré 5 casos CNR similares en Maipú:
1. Caso 231015-000123 - Resuelto como INSTRUCCION (falta de OT)
2. Caso 231120-000456 - Resuelto como IMPROCEDENTE (todo cumplía)
...
¿Quieres ver los detalles de alguno?"
```

### 12.7.3. Consulta Analítica

**Escenario:**
Supervisor quiere entender tendencias del sistema.

**Interacción:**
```
Usuario: "¿Qué empresas tienen más reclamos este mes?"

IA: "Este mes, las empresas con más reclamos son:
1. ENEL: 45 casos (32 pendientes, 13 resueltos)
2. Grupo Saesa: 28 casos (18 pendientes, 10 resueltos)
3. CGE: 22 casos (15 pendientes, 7 resueltos)

El tiempo promedio de resolución es de 12 días para ENEL, 
15 días para Grupo Saesa, y 10 días para CGE."
```

## 12.8. Consideraciones Técnicas

### 12.8.1. Modelo de Lenguaje

**Opciones:**
- **OpenAI GPT-4**: Alta calidad, requiere API key
- **Llama 2/3**: Open source, puede ejecutarse localmente
- **Claude**: Alternativa de alta calidad
- **Modelos especializados**: Entrenados en dominio legal

### 12.8.2. Base de Datos Vectorial

**Opciones:**
- **Pinecone**: Servicio gestionado
- **Weaviate**: Open source, auto-hospedado
- **Chroma**: Ligero, fácil de integrar
- **FAISS**: De Facebook, alto rendimiento

### 12.8.3. Seguridad y Privacidad

**Consideraciones:**
- Datos sensibles (RUTs, información personal)
- Cumplimiento con normativa de protección de datos
- Encriptación de comunicaciones
- Logs de auditoría de consultas

## 12.9. Roadmap de Implementación

### 12.9.1. Fase 1: Prototipo Básico

- Integración con LLM básico (GPT-3.5 o equivalente)
- Consultas simples a base de datos
- Respuestas de plantilla mejoradas
- Interfaz de chat funcional

### 12.9.2. Fase 2: RAG Básico

- Vectorización de documentos
- Búsqueda semántica
- Recuperación de contexto relevante
- Respuestas basadas en datos reales

### 12.9.3. Fase 3: Análisis Avanzado

- Consultas analíticas complejas
- Generación de visualizaciones
- Búsqueda de casos similares
- Asistencia en resolución

### 12.9.4. Fase 4: Optimización

- Fine-tuning del modelo
- Caché de respuestas frecuentes
- Optimización de queries
- Mejora de experiencia de usuario

## 12.10. Beneficios Esperados

### 12.10.1. Para el Funcionario

- **Aceleración**: Respuestas rápidas a preguntas comunes
- **Contexto**: Información relevante sin buscar manualmente
- **Aprendizaje**: Aprender de casos históricos
- **Eficiencia**: Reducir tiempo en tareas repetitivas

### 12.10.2. Para la Organización

- **Consistencia**: Mismas respuestas para mismas preguntas
- **Escalabilidad**: Atender más consultas sin más personal
- **Conocimiento**: Capturar y reutilizar conocimiento institucional
- **Innovación**: Posicionar a la SEC como líder en uso de IA

## 12.11. Conclusión

El ChatBot con tecnología RAG representa una evolución natural del sistema, permitiendo consultas naturales sobre los datos estructurados y proporcionando asistencia contextual al funcionario. La integración con la base de datos relacional y los EDNs proporciona una base sólida para respuestas precisas y relevantes. Aunque actualmente el sistema tiene un prototipo básico con respuestas simuladas, la arquitectura está preparada para integrar un motor RAG completo que transforme la forma en que los funcionarios interactúan con el sistema.

---

[← Anterior: Futuras Analíticas](11_Futuras_analiticas.md) | [Siguiente: Cierre →](13_Cierre.md)

