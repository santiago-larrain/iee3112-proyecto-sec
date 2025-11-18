# Datos de Ejemplo

Este directorio contiene archivos de ejemplo para probar el sistema.

## Archivos

- `reclamo_ejemplo.json`: Ejemplo de reclamo en formato JSON
- `credenciales_ejemplo.json`: Plantilla para credenciales de scraping

## Uso

```bash
# Procesar reclamo de ejemplo
python modulos/main.py --reclamo datos/reclamo_ejemplo.json

# Con credenciales (copiar credenciales_ejemplo.json a credenciales.json y completar)
python modulos/main.py --reclamo datos/reclamo_ejemplo.json --credenciales datos/credenciales.json
```

## Nota de Seguridad

**NO** subir archivos con credenciales reales al repositorio. El archivo `credenciales.json` está en `.gitignore`.

