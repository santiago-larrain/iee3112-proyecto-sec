# Motor de Ingesta - Guía de Uso

## Descripción

El Motor de Ingesta procesa casos reales de la SEC, extrayendo información de documentos PDF y DOCX, clasificándolos y almacenándolos en la base de datos.

## Instalación de Dependencias

```bash
cd backend
pip install -r requirements.txt
```

## Procesar Casos de Ejemplo

Para procesar los 5 casos reales ubicados en `data/example_cases/`:

```bash
cd backend
python scripts/process_example_cases.py
```

El script:
1. Escanea todas las carpetas en `data/example_cases/`
2. Procesa cada archivo (PDF, DOCX, imágenes)
3. Extrae entidades (RUT, NIS, direcciones, montos)
4. Clasifica documentos por tipo
5. Genera Expedientes Digitales Normalizados (EDN)
6. Almacena todo en la base de datos SQLite (`data/sec_reclamos.db`)

## Estructura de la Base de Datos

El sistema crea las siguientes tablas:

- **personas**: Clientes identificados por RUT
- **suministros**: Puntos de suministro identificados por NIS + Comuna
- **casos**: Reclamos vinculados a personas y suministros
- **documentos**: Archivos procesados con su clasificación y metadatos

## Uso en la API

Una vez procesados los casos, la API automáticamente los leerá de la base de datos en lugar del JSON mock. Si no hay casos en BD, se usa el mock como fallback.

## Notas

- El script es idempotente: puede ejecutarse múltiples veces sin duplicar datos
- Si un archivo no se puede procesar, se marca como faltante y se continúa
- Los documentos se clasifican automáticamente según heurísticas de nombre y contenido

