# Motor de Ingesta (OMC) - Guía de Uso

## Descripción

El Objeto Maestro de Compilación (OMC) procesa casos reales de la SEC, extrayendo información de documentos PDF y DOCX, clasificándolos y almacenándolos en la base de datos. El OMC transforma documentos no estructurados en Expedientes Digitales Normalizados (EDN).

## Instalación de Dependencias

```bash
cd backend
pip install -r requirements.txt
```

## Procesar Casos de Ejemplo

Para procesar los casos reales ubicados en `data/Files/` y generar la base de datos JSON:

```bash
cd backend
python src/engine/omc/create_json_database.py
```

Este script usa el motor **OMC** completo para:
1. Escanear todas las carpetas de casos en `data/Files/` (ej: `data/Files/230125-000509/`)
2. Procesar cada archivo con OCR (PDFs) y extracción de texto (DOCX)
3. Extraer entidades (RUT, NIS, direcciones, montos) usando el EntityExtractor
4. Clasificar documentos automáticamente usando el DocumentClassifier
5. Generar Expedientes Digitales Normalizados (EDN) completos
6. Almacenar todo en la base de datos JSON (`data/DataBase/`)

**Nota**: Este script reemplaza el procesamiento manual y aprovecha todas las capacidades del OMC (OCR, extracción de entidades, clasificación inteligente).

## Estructura de la Base de Datos

El sistema crea los siguientes archivos JSON:

- **personas.json**: Clientes identificados por RUT
- **suministros.json**: Puntos de suministro identificados por NIS + Comuna
- **casos.json**: Reclamos vinculados a personas y suministros (solo metadatos)
- **documentos.json**: Archivos procesados con su clasificación y metadatos
- **edn.json**: Expedientes Digitales Normalizados completos

## Componentes del OMC

- **document_processor.py**: Orquestador principal del pipeline
- **pdf_extractor.py**: Extracción de texto y datos de PDFs
- **docx_extractor.py**: Extracción de texto y datos de DOCX
- **document_classifier.py**: Clasificación de documentos por tipo
- **document_categorizer.py**: Categorización funcional de documentos
- **entity_extractor.py**: Extracción de entidades (RUT, NIS, direcciones, montos)

## Uso en la API

Una vez procesados los casos, la API automáticamente los leerá de la base de datos JSON. Si no hay casos en BD, se usa el mock como fallback.

## Notas

- El script es idempotente: puede ejecutarse múltiples veces sin duplicar datos
- Si un archivo no se puede procesar, se marca como faltante y se continúa
- Los documentos se clasifican automáticamente según heurísticas de nombre y contenido
- El OMC genera el EDN que alimenta al MIN (Motor de Inferencia Normativa) y al MGR (Motor de Generación de Resoluciones)

