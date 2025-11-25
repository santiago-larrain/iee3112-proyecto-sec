# Manual de Arquitectura y Operación - Sistema de Análisis de Reclamos SEC

## Tabla de Contenidos

### Capítulo 1: Arquitectura General
Visión de alto nivel del sistema. Diagrama de bloques mostrando el flujo completo desde la ingesta hasta la resolución. Explicación del patrón de diseño "Pipeline & Filters" y la arquitectura hexagonal utilizada.

[Leer Capítulo 1 →](1_Arquitectura_General.md)

---

### Capítulo 2: Entradas
Define el contrato de entrada del sistema. Tipos de archivos aceptados, validaciones de seguridad, estructura del Payload JSON inicial y restricciones de ingesta.

[Leer Capítulo 2 →](2_Entradas.md)

---

### Capítulo 3: OMC (Objeto Maestro de Compilación)
Describe el núcleo del sistema de ingesta. Explica las fases de sanitización, OCR, clasificación documental y la generación del "Contrato de Datos" (EDN). Transformación de documentos no estructurados en datos analizables.

[Leer Capítulo 3 →](3_OMC.md)

---

### Capítulo 4: DataBase
Explica el Modelo Relacional Estrella (Personas, Suministros, Casos, Documentos). Justifica la separación de metadata del EDN. Describe la estrategia de "Upsert Inteligente" para evitar duplicados y preservar historial.

[Leer Capítulo 4 →](4_DataBase.md)

---

### Capítulo 5: EDN (Expediente Digital Normalizado)
Define la estructura JSON del EDN como fuente única de verdad. Explica la importancia de este objeto como contrato de datos para los procesos posteriores. Detalla los niveles de inventario (Crítico, Soportante, Ausente).

[Leer Capítulo 5 →](5_EDN.md)

---

### Capítulo 6: MIN (Motor de Inferencia Normativa)
Explica cómo se separan las Reglas (Python) de la Configuración (JSON). Detalla el concepto de "Binding" y cómo el sistema decide si un requisito se CUMPLE o NO. Generación automática del checklist de validación.

[Leer Capítulo 6 →](6_MIN.md)

---

### Capítulo 7: Checklist
Describe la Interfaz de Usuario resultante del MIN. Explica la lógica de los grupos (Admisibilidad, Instrucción, Fondo) y la funcionalidad de "Deep Linking" a la evidencia. Proceso de validación humana.

[Leer Capítulo 7 →](7_Checklist.md)

---

### Capítulo 8: MGR (Motor de Generación Resolutiva)
Describe el sistema de plantillas dinámicas. Explica cómo el estado del Checklist determina si se usa la plantilla de "Instrucción" o "Improcedente" y cómo se inyectan los párrafos legales específicos.

[Leer Capítulo 8 →](8_MGR.md)

---

### Capítulo 9: Resolución
El producto final del sistema. Describe el flujo de revisión humana, edición del borrador, firma digital y cierre del caso. Persistencia de la resolución y actualización de estado.

[Leer Capítulo 9 →](9_Resolucion.md)

---

### Capítulo 10: Utilidades
Describe scripts auxiliares, modos de prueba (Test vs Validate) y herramientas de debugging. Herramientas para desarrollo, testing y mantenimiento del sistema.

[Leer Capítulo 10 →](10_Utilidades.md)

---

### Capítulo 11: Futuras Analíticas
Describe el valor de los datos estructurados para Business Intelligence. Capacidades futuras: mapas de calor de fraude, detección de reincidencia, métricas de eficiencia y análisis predictivo.

[Leer Capítulo 11 →](11_Futuras_analiticas.md)

---

### Capítulo 12: AI ChatBot (Proyección)
Describe conceptualmente cómo un asistente IA (RAG) podría conectarse a la BBDD estructurada para responder preguntas naturales como "¿Cuántos casos de CNR tiene la comuna X?". Integración de inteligencia artificial conversacional.

[Leer Capítulo 12 →](12_AI_ChatBot.md)

---

### Capítulo 13: Cierre
Conclusiones sobre la escalabilidad del sistema, mantenimiento y roadmap técnico. Consideraciones de evolución futura y mejores prácticas.

[Leer Capítulo 13 →](13_Cierre.md)

---

## Resumen Ejecutivo

El **Sistema de Análisis de Reclamos SEC** es una plataforma full-stack diseñada para procesar, analizar y resolver reclamos de manera eficiente y consistente. El sistema transforma documentos no estructurados en datos normalizados mediante un pipeline automatizado (OMC), valida el cumplimiento normativo mediante reglas configurables (MIN), y genera resoluciones legales mediante plantillas dinámicas (MGR).

**Arquitectura Clave:**
- **OMC**: Transforma documentos → EDN (Expediente Digital Normalizado)
- **MIN**: Evalúa EDN → Checklist de validación
- **MGR**: Genera Checklist → Resolución legal

**Principios de Diseño:**
- Separación de responsabilidades (reglas vs configuración)
- Human-in-the-loop (validación humana de decisiones automáticas)
- Escalabilidad (soporte para múltiples tipos de reclamos)
- Trazabilidad (historial completo de actores y eventos)

---

[Inicio del Manual](0_Indice.md) | [Siguiente: Arquitectura General →](1_Arquitectura_General.md)

